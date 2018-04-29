#!Python
import random
import re
import copy
import pprint

'''Model Class ----------------------------------------------------------------------------------------------
Has:
	Hyper parameters
	Q = [] list of states
	q0 = starting state
	Sigma = [] list of input symbols (mutable)
	Delta = [] list of output symbols (imutable?)
	Omicron = [] list of marked output symbols
Handles:
	CreateTransitions
	UpdateExpectations
	ApplyReward
	ApplyPunishment
	ApplyConditioning
	UpdateConditioning
	'''
class Model(object):

	def __init__(self,Sigma,Delta,tau=1,alpha=0.05,beta=0.05,gamma=0.2,eta=1.0,zeta=0.1,nu=0.5,kappa=0.9):
		#Hyperparameters
		self.tau = tau
		self.alpha = alpha
		self.beta = beta
		self.gamma = gamma
		self.eta = eta 
		self.zeta = zeta
		self.nu  = nu
		self.kappa = kappa
		self.EPSILON = Epsilon()
		#Variables
		self.Q = [] #List of all states
		self.Sigma = Sigma 
		self.Delta = Delta
		self.Omicron = [] #List of outputed symbol
		self.OmicronDist = [] #List of associated Distributions by storing their transitions for later access
		self.OmicronA = [] #List of associated input symboks related to OmicronDist
		self.c = None
		self.I = [] #List of input symbol and strength pairs
		self.Il = self.I #Last set of inputs
		self.Isymbols = [] #Only the symbols for I
		self.Ilsymbols = [] #Only the symbols for Il
		self.history = [] #History of ad,sd,o,od
		self.conditioned = [] #Stores what transitions had their distributins conditioned
		self.ql = None #Last state
		self.ad = Epsilon() #Strongest Input
		self.al = Epsilon() #Last strongest input
		self.ol = Epsilon() #Last output
		self.o = Epsilon() #Current Output
		self.qa = self.c
		self.sd = 0.0 #Strongest pair's strength

	'''
	Starts up the model.
	Sets the global alphabets to the inputed ones for reference
	'''
	def Start(self,q0):
		#Create or read in experiment
		global SIGMA,DELTA
		SIGMA = self.Sigma
		DELTA = self.Delta
		if q0 not in self.Q:
			self.Q = self.Q + [q0]
		self.c = q0
		self.ql = q0
		self.qa = q0
		self.Cycle()

	'''
	Step 2-On
	'''
	def Cycle(self):
		while(True):
			systemInput = GetInput()#Step 3
			self.Il = self.I 
			self.I = systemInput
			#Store the symbols for quick reference
			self.Isymbols = []
			for pair in self.I:
				self.Isymbols = self.Isymbols + [pair[0]]
			self.Ilsymbols = []
			for pair in self.Il:
				self.Isymbols = self.Ilsymbols + [pair[0]]
			if self.I == Epsilon(): #Step 2
				if self.c.transitions[GetSymbolIndex(Epsilon())] != None:
					if self.c.transitions[GetSymbolIndex(Epsilon())].isTemporary:
						self.c.transitions[GetSymbolIndex(Epsilon())].isTemporary = False
					self.ql = self.c
					self.c = self.c.GetNextState(Epsilon())
				self.qa = self.c
				self.al = Epsilon()
				self.ol = Epsilon()
				self.Omicron = []
				self.OmicronDist = []
				self.OmicronA = []
				HandleOutput('[Message] Time greater than tau passed')
				self.history = self.history + [["' '",0.0,"' '",0.0]] #Epsilon added to History
				return self.Cycle()
			(self.ad,self.sd) = self.HandleInput(self.I) #Step 4
			self.CreateTransitions() #Step 5
			self.ol = self.o #Step 6
			self.o = self.c.transitions[GetSymbolIndex(self.ad)].ChooseOuput() #Step 7
			#Determine Rewards based on some output stuff here?
			Sout = (self.sd*self.c.transitions[GetSymbolIndex(self.ad)].GetConfidence())/(1+self.c.transitions[GetSymbolIndex(self.ad)].GetConfidence())
			HandleOutput('Output: '+self.o+' with strength '+str(Sout))
			self.history = self.history + [[self.ad,self.sd,self.o,Sout]]
			self.Omicron = self.Omicron + [self.o] #Step 8
			self.OmicronDist = self.OmicronDist + [self.c.transitions[GetSymbolIndex(self.ad)]]
			self.OmicronA = self.OmicronA + [self.ad]
			self.UpdateExpectations() #Step 9
			self.ql = self.c #Self 6
			self.al = self.ad
			self.c = self.c.GetNextState(self.ad) #Step 10
			if self.c.isReward: #Step 11
				self.ApplyReward()
			elif self.c.isPunishment:
				self.ApplyPunishment()
			else:
				self.ApplyConditioning()
		#self.Cycle() #Step 12

	'''Returns the strongest input pair'''
	def HandleInput(self,nextInput):
		output = ['',0]
		maxS = output[1]
		for pair in nextInput:
			s = pair[1]
			if s > maxS:
				output = pair
		return output

	def CreateTransitions(self):
		if self.c.transitions[GetSymbolIndex(Epsilon())] != None and self.c.transitions[GetSymbolIndex(Epsilon())].isTemporary:
			self.c.transitions[GetSymbolIndex(Epsilon())] = None
		for pair in self.I:
			ai = pair[0]
			si = pair[1]
			if self.c.transitions[GetSymbolIndex(ai)] == None:
				qn = State(str(len(self.Q)))
				self.Q = self.Q + [qn]
				temp = Transition(self.c,qn)
				te = Transition(qn,self.qa)
				te.isTemporary = True
				te.GenerateNew(self.eta,self.Delta)
				found = False
				for state in self.Q:
					told = state.transitions[GetSymbolIndex(ai)]
					if told != None:
						temp.CopyTransition(told)
						if told.TakeTransition().isReward:
							qn.isReward = True
						elif told.TakeTransition().isPunishment:
							qn.isPunishment = True
						found = True
						break
				if not found:
					temp.GenerateNew(self.eta,self.Delta)
				self.c.AddTransitionOn(ai,temp)
				qn.AddTransitionOn(Epsilon(),te)

	def UpdateExpectations(self):
		t1 = self.ql.transitions[GetSymbolIndex(self.al)] #ql on al
		t2 = self.c.transitions[GetSymbolIndex(self.ad)] #c on ad
		if t1 != None and t2 != None:
			if t2 in t1.Expectations.keys():
				deltaE = self.alpha * (1-t1.Expectations[t2])
				t1.Confidence *= (1-self.beta*abs(deltaE))
				t1.Expectations[t2] += deltaE
				deltaE = self.alpha * (1-t2.Expectations[t1])
				t2.Confidence *= (1-self.beta*abs(deltaE))
				t2.Expectations[t1] += deltaE
			else:
				t1.Expectations[t2] = self.alpha
				t2.Expectations[t1] = self.alpha

		if t1 != None:
			for symbol in self.Sigma:
				haveSymbol = False
				for pair in self.I:
					if symbol in pair:
						haveSymbol = True
				if not haveSymbol:
					t3 = self.c.transitions[GetSymbolIndex(symbol)] # ql on a
					if t3 != None and t1 in t3.Expectations.keys():
						deltaE = -self.alpha*t1.Expectations[t3]
						t1.Confidence *= (1-self.beta*abs(deltaE))
						t1.Expectations[t3] += deltaE
						deltaE = -self.alpha*t3.Expectations[t1]
						t3.Confidence *= (1-self.beta*abs(deltaE))
						t3.Expectations[t1] += deltaE

		if t2 != None:
			for state in self.Q:
				for symbol in self.Sigma:
					if state != self.ql or symbol != self.al:
						t4 = state.transitions[GetSymbolIndex(symbol)] # q on a
						if t4 != None and t4 in t2.Expectations.keys():
							deltaE = -self.alpha*t2.Expectations[t4]
							t2.Confidence *= (1-self.beta*abs(deltaE))
							t2.Expectations[t4] += deltaE
							deltaE = -self.alpha*t4.Expectations[t2]
							t4.Confidence *= (1-self.beta*abs(deltaE))
							t4.Expectations[t2] += deltaE

		for a in self.Sigma:
			for b in self.Sigma:
				if a != b:
					t5 = self.c.transitions[GetSymbolIndex(a)] #c on a
					t6 = self.c.transitions[GetSymbolIndex(b)] #c on b
					if t5 != None and t6 != None:
						if a in self.Isymbols and b in self.Isymbols:
							if t6 in t5.Expectations.keys(): #I THINK THIS IS NOW ONE WAY
								deltaE = self.alpha * (1-t5.Expectations[t6])
								t5.Confidence *= (1-self.beta*abs(deltaE))
								t5.Expectations[t6] += deltaE
							else:
								t5.Expectations[t6] = self.alpha
								t5.Confidence *= (1-self.beta*abs(deltaE)) #IDK IF THIS BELONGS HERE
						elif a in self.Isymbols or b in self.Isymbols:
							if t6 in t5.Expectations.keys():
								deltaE = -self.alpha * t5.Expectations[t6]
								t5.Confidence *= (1-self.beta*abs(deltaE))
								t5.Expectations[t6] += deltaE


	#!!!!!!!!!!!!!!!!CHECK THIS LOGIC!!!!!!!!!!!!!!!!!!!!!!!!!!!
	def ApplyReward(self):
		t = 1
		for i in range(len(self.OmicronDist)-1,-1,-1):
			distribution = self.OmicronDist[i].PDelta
			symbol = self.Omicron[i]
			a = self.OmicronA[i]
			change = self.zeta*t*self.sd*1/self.OmicronDist[i].GetConfidence()
			print(pprint.pformat(distribution),symbol,a,str(change))
			distribution[symbol] = (distribution[symbol] + change)/(1+change)
			for b in self.Delta:
				if b != symbol:
					distribution[b] = (distribution[b])/(1+change)
			self.OmicronDist[i].Confidence += self.zeta*t*self.sd
			#Unmark beta here? seems weird
			for state in self.Q:
				tr = state.transitions[GetSymbolIndex(a)] #state on a
				if tr != None:
					tr.PDelta[symbol] = (tr.PDelta[symbol] + self.gamma*change)/(1+self.gamma*change)
					for b in self.Delta:
						if b != symbol:
							tr.PDelta[b] = (tr.PDelta[b])/(1+self.gamma*change)
					tr.Confidence += self.gamma *self.zeta * t * self.sd
			t = self.kappa * t
		self.Omicron = []
		self.OmicronDist = []
		self.OmicronA = []

	#!!!!!!!!!!!!!!!!CHECK THIS LOGIC!!!!!!!!!!!!!!!!!!!!!!!!!!!		
	def ApplyPunishment(self):
		t = 1
		for i in range(len(self.OmicronDist)-1,-1,-1):
			distribution = self.OmicronDist[i].PDelta
			symbol = self.Omicron[i]
			a = self.OmicronA[i]
			distribution[symbol] = (distribution[symbol])/(1+self.zeta*t*self.sd*1/self.OmicronDist[i].GetConfidence())
			for b in self.Delta:
				if b != symbol:
					distribution[b] = (distribution[b]+(1/(len(self.Delta)-1))*self.zeta*t*self.sd*1/self.OmicronDist[i].GetConfidence())/(1+self.zeta*t*self.sd*1/self.OmicronDist[i].GetConfidence())
			self.OmicronDist[i].Confidence += self.zeta*t*self.sd
			#Unmark beta here? seems weird
			for state in self.Q:
				tr = state.transitions[GetSymbolIndex(a)] #state on a
				if tr != None:
					tr.PDelta[symbol] = (tr.PDelta[symbol])/(1+self.gamma*self.zeta*t*self.sd*1/tr.Confidence)
					for b in self.Delta:
						if b != symbol:
							tr.PDelta[b] = (tr.PDelta[b]+(1/(len(self.Delta)-1))*self.zeta*t*self.sd*1/tr.Confidence/(1+self.gamma*self.zeta*t*self.sd*1/tr.Confidence))
					tr.Confidence += self.gamma *self.zeta * t * self.sd
			t = self.kappa * t
		self.Omicron = []
		self.OmicronDist = []
		self.OmicronA = []

	def ApplyConditioning(self):
		global EpislonCanLearn
		self.conditioned = []
		tl = self.ql.transitions[GetSymbolIndex(self.al)] #ql on al
		if self.ol != Epsilon() and self.ol != self.o and tl != None:
			for a in self.Sigma:
				if EpislonCanLearn or a != Epsilon():
					t2 = self.ql.transitions[GetSymbolIndex(a)] #ql on a
					if t2 != None and t2 in tl.Expectations.keys() and a in self.Isymbols:
						#print('[DEBUG ApplyConditioning]: g:%f sd:%f c:%f for %s' %(self.gamma,self.sd,t2.Confidence,t2.PrintTransition()))
						change = self.gamma*self.sd/t2.Confidence
						t2.PDelta[self.ol] = (t2.PDelta[self.ol] + change) / (1+change)
						for b in self.Delta:
							if b != self.ol:
								t2.PDelta[b] = t2.PDelta[b] / (1+change)
						if t2 not in self.conditioned:
							self.conditioned += [t2]
							#print(t2.PrintTransition()+' Conditioned')
							t2.Confidence += self.gamma * self.sd
							self.UpdateConditioning(self.ql,a,(self.sd/t2.Confidence))
					for q in self.Q:
						t3 = q.transitions[GetSymbolIndex(a)] #q on a
						if t3 != None and t3.endState == self.ql and t3 in tl.Expectations.keys():
							#print('[DEBUG ApplyConditioning]: g:%f sd:%f c:%f for %s' %(self.gamma,self.sd,t3.Confidence,t3.PrintTransition()))
							change = self.gamma*self.sd/t3.Confidence
							t3.PDelta[self.ol] = (t3.PDelta[self.ol] + change) / (1+change)
							for b in self.Delta:
								if b != self.ol:
									t3.PDelta[b] = t3.PDelta[b] / (1+change)
							if t3 not in self.conditioned:
								self.conditioned += [t3]
								#print(t3.PrintTransition()+' Conditioned')
								t3.Confidence += self.gamma * self.sd
								self.UpdateConditioning(q,a,(self.sd/t3.Confidence))

	def UpdateConditioning(self,qP,aP,s):
		global EpislonCanLearn
		if s > 0:
			t1 = qP.transitions[GetSymbolIndex(aP)] #q' on a'
			if t1 != None:
				for a in self.Sigma:
					if EpislonCanLearn or a != Epsilon():
						t2 = qP.transitions[GetSymbolIndex(a)] #q' on a
						if t2 != None and t2 in t1.Expectations.keys() and t2 not in self.conditioned: #a in self.Isymbols (Not doing this here?) 
							#print('[DEBUG ApplyConditioning]: g:%f sd:%f c:%f for %s' %(self.gamma,s,t2.Confidence,t2.PrintTransition()))
							change = self.gamma*s/t2.Confidence
							t2.PDelta[self.ol] = (t2.PDelta[self.ol] + change) / (1+change)
							for b in self.Delta:
								if b != self.ol:
									t2.PDelta[b] = t2.PDelta[b] / (1+change)
							self.conditioned += [t2]
							#print(t2.PrintTransition()+' Conditioned')
							t2.Confidence += self.gamma*s
							self.UpdateConditioning(qP,a,s/t2.Confidence)
						for q in self.Q:
							t3 = q.transitions[GetSymbolIndex(a)] #q on a
							if t3 != None and t3 in t1.Expectations.keys() and t3 not in self.conditioned and t3.endState == qP: #I changed this from ql because that didn't make sense
								#print('[DEBUG ApplyConditioning]: g:%f sd:%f c:%f for %s' %(self.gamma,s,t3.Confidence,t3.PrintTransition()))
								change = self.gamma*s/t3.Confidence
								t3.PDelta[self.ol] = (t3.PDelta[self.ol] + change) / (1+change)
								for b in self.Delta:
									if b != self.ol:
										t3.PDelta[b] = t3.PDelta[b] / (1+change)
								#print(t3.PrintTransition()+' Conditioned')
								self.conditioned += [t3]
								t3.Confidence += self.gamma*s
								self.UpdateConditioning(q,a,s/t3.Confidence)

	#!!!!!!!!!!!!!!!!CHECK THIS LOGIC!!!!!!!!!!!!!!!!!!!!!!!!!!!
	def OldApplyConditioning(self):
		self.conditioned = []
		if self.ol != Epsilon() and self.o != self.ol:
			for symbol in self.Sigma:
				t1 = self.ql.transitions[GetSymbolIndex(self.al)] #ql on al
				t2 = self.ql.transitions[GetSymbolIndex(symbol)] #ql on symbol
				if t1 != None and t2 != None:
					if t2 in t1.Expectations.keys():
						if symbol in self.Ilsymbols:
							change = self.gamma*self.sd*(1/t2.Confidence)
							t2.PDelta[self.ol] = (t2.PDelta[self.ol] + change)/(1+change)
							for d in self.Delta:
								if d != symbol:
									t2.PDelta[d] = (t2.PDelta[d])/(1+change)
							#Condition?
							if t2 not in self.conditioned:
								self.conditioned = self.conditioned + [t2]
								t2.Confidence += self.gamma*self.sd
								UpdateConditioning(self.ql,symbol,self.sd*(1/t2.Confidence))
			for state in self.Q:
				for symbol in self.Sigma:
					if state.transitions[GetSymbolIndex(symbol)] == self.ql:
						t1 = self.ql.transitions[GetSymbolIndex(self.al)] #ql on al
						t3 = state.transitions[GetSymbolIndex(symbol)] #state on symbol that leads to ql
						if t1 != None and t3 != None:
							if t3 in t1.Expectations.keys():
								change = self.gamma*self.sd*(1/t3.Confidence)
								t3.PDelta[self.ol] = (t3.PDelta[self.ol] + change) / (1+change)
								for d in self.Delta:
									if d != symbol:
										t3.PDelta[d] = t3.PDelta[d] / (1+change)
								#Condition?
								if t3 not in self.conditioned:
									self.conditioned = self.conditioned + [t3]
									t3.Confidence += self.gamma*self.sd
									UpdateConditioning(state,symbol,self.sd*(1/t3.Confidence))

			#DO THE PART ABOUT THE NOT ALREADY CONDITIONED THINGS?
				#I decided to do this in the other loops and then I need to determine some marker to say we already handled them

	#!!!!!!!!!!!!!!!!CHECK THIS LOGIC!!!!!!!!!!!!!!!!!!!!!!!!!!!
	def OldUpdateConditioning(self,state,symbol,s):
		if s > 0:
			t1 = state.transitions[GetSymbolIndex(symbol)] # state on symbol
			if t1 != None:
				for a in self.Sigma:
					t2 = state.transitions[GetSymbolIndex(a)] # state on a
					if t2 != None and t2 in t1.Expectations.keys():
						if t2 not in self.conditioned:
							self.conditioned = self.conditioned + [t2]
							change = self.gamma*s*(1/t2.Confidence)
							t2.PDelta[self.ol] = (t2.PDelta[self.ol]+change)/(1+change)
							for d in self.Delta:
								if d != self.ol:
									t2.PDelta[d] = (t2.PDelta[d])/(1+change)
							if a in self.Isymbols:
								t2.Confidence += self.gamma * s
								self.conditioned = self.conditioned + [t2]
								UpdateConditioning(state,a,s*(1/t2.Confidence))
					for q in self.Q:
						t3 = q.transitions[GetSymbolIndex(a)] # q on a
						if t3 != None and t3.GetNextState() == state and t3 in t1.Expectations.keys():
							change = self.gamma*s*(1/t1.Confidence)
							t1.PDelta[self.ol] = (t1.PDelta[self.ol]+change)/(1+change)
							for d in self.Delta:
								if d != self.ol:
									t1.PDelta[d] = t1.PDelta[d] / (1+change)
							if state == self.ql and t3 not in self.conditioned:
								t3.Confidence += self.gamma*s
								self.conditioned = self.conditioned + [t3]
								UpdateConditioning(q,a,s*(1/t3.Confidence))


	def PrintModel(self):
		output = '--------- Status --------\n'
		output += 'Sigma: ' +str(self.Sigma) +'\n'
		output += 'Delta: ' +str(self.Delta) +'\n'
		output += '\n------- I/O -------------\n'
		output += 'Last Input: '+str(self.Il) + '\n'
		output += 'Current Input: '+str(self.I) +'\n'
		output += 'Last Output: '+str(self.ol) +'\n'
		output += 'Current Output: '+str(self.o) +'\n'
		output += '\n------- All States ------\n'
		for q in self.Q:
			if q == self.c:
				output += '[ C] '+ q.PrintState()
			elif q == self.ql:
				output += '[ql] '+ q.PrintState()
			else:
				output += '[+ ] '+ q.PrintState()
			if q.isReward:
				output += ' [Reward]\n'
			elif q.isPunishment:
				output += ' [punishment]\n'
			else:
				output += '\n'
			for a in self.Sigma:
				t = q.transitions[GetSymbolIndex(a)]
				if a == Epsilon():
					a = "' '"
				if t != None:
					output += '   <'+a+'>: '+t.PrintTransition()
					if t.isTemporary:
						output += ' [Temp]\n'
					else:
						output += '\n'
					output += '      Confidence: '+str(t.GetConfidence())+'\n'
					for to in t.Expectations.keys():
						output += '      ('+t.PrintTransition()+') => ('+to.PrintTransition()+') = '+str(t.Expectations[to]) +'\n'
					output += '      PDelta:\n         '+pprint.pformat(t.PDelta,indent=9) + '\n'
				else:
					output += '   <'+a+'>: None\n'
			output += '\n'
		output += '\n------- History ----------\n'
		for entry in self.history:
			output += str(entry)+'\n'
		output += '\n'
		return output

	def ProduceHTML(self):
		global HTMLstart,HTMLend
		output = HTMLstart
		for q in self.Q:
			output += '      {name: \"[ '+str(q.id)+' ]\", color:'
			if q == self.c:
				output += '\"blue\"},\n'
			elif q == self.ql:
				output += '\"orange\"},\n'
			else:
				if q.isReward:
					output += '\"green\"},\n'
				elif q.isPunishment:
					output += '\"red\"},\n'
				else:
					output += '\"gray\"},\n'
		output += '''
		],
		edges: [
		'''
		for q in self.Q:
			for a in self.Sigma:
				t = q.transitions[GetSymbolIndex(a)]
				if t != None:
					output += '   {source: '+str(t.startState.id)+', target: '+str(t.endState.id)+', color:'
					if q == self.c and a == self.ad:
						output += '\'blue\''
					elif q == self.ql and a == self.al:
						output += '\'orange\''
					else:
						if q.isReward:
							output += '\'green\''
						elif q.isPunishment:
							output += '\'red\''
						else:
							if t.isTemporary:
								output += '\'white\''
							else:
								output += '\'gray\''
					output += ', name: \''+a+'\'},\n'
		output += HTMLend
		return output




'''State Class ----------------------------------------------------------------------------------------------
Has:
	delta = {[]} get next state from 
	R = bool is it a reward state
	P = bool is it a punishment state
	'''
class State(object):

	def __init__(self,ID,isPunishment=False,isReward=False):
		global SIGMA
		self.id = ID
		self.isReward = isReward
		self.isPunishment = isPunishment
		self.transitions = [None] * len(SIGMA) #List of transitions where index matches symbols in SIGMA

	'''delta
	Takes in a symbol and follows that transition
	Returns the next state or None if the transition is not defined'''
	def GetNextState(self,symbol):
		return self.transitions[GetSymbolIndex(symbol)].TakeTransition()

	'''adds the transition to the array of transitions at the index of the given symbol if it does not exists already'''
	def AddTransitionOn(self,symbol,transition):
		index = GetSymbolIndex(symbol)
		if index >= len(self.transitions):
			self.transitions = self.transitions + [None]*index-len(self.transitions)

		if self.transitions[index] == None:
			self.transitions[index] = transition
		else:
			#DEBUG
			print('[Error] Transition for the symbol %s already exists for this state %s' %(symbol,self.PrintState()))
			print(self.transitions[index].PrintState())

	def PrintState(self):
		return ('State '+str(self.id))
	
'''Transition Class ----------------------------------------------------------------------------------------------
Has:
	lambda = sigma(P^Delta) the ability to choose output from its own distribution of outputs
	PDelta = {} probablistic disribution of outputs
	C = float the confidence in this transition
	E = {} expectation that this transition is related to other transitions
	'''
class Transition(object):

	def __init__(self,fromState,goToState,isTemporary=False):
		self.startState = fromState
		self.endState = goToState
		self.isTemporary = isTemporary
		self.PDelta = {} #Key: Symbol | Value [0,1] probability of it being produced
		self.Confidence = 0.1
		self.Expectations = {} #Key: Transition | Value: [0,1] expectation value

	'''lamdba'''
	def ChooseOuput(self):
		global DELTA
		rand = random.uniform(0,1)
		level = 0
		for symbol in self.PDelta.keys():
			level += self.PDelta[symbol]
			if rand <= level:
				#!TODO! enable proper output and working with model's omicron
				return symbol
				break

	'''returns the next endState and chooses the output'''
	def TakeTransition(self):
		#self.ChooseOuput() #THIS IS MOVED TO BEING CALLED FROM THE MODEL
		return self.endState

	'''returns the confidence'''
	def GetConfidence(self):
		return self.Confidence

	'''Sets the confidence'''
	def SetConfidence(self, value):
		self.Confidence = value

	'''returns the expectation value with transition, if E(t1,t2) does not exist it returns None'''
	def GetExpectationWith(self,transition):
		if transition not in self.E.keys():
			return None
		else:
			return self.E[transition]

	'''Copies the distribution and the confidence'''
	def CopyTransition(self,other):
		self.PDelta = copy.copy(other.PDelta)
		self.Confidence = copy.copy(other.Confidence)

	'''Creates new Expectations and Confidence'''
	def GenerateNew(self,eta,Delta):
		self.Confidence = 0.1
		self.PDelta[Epsilon()] = eta
		difference = 1-eta
		if difference > 0:
			for symbol in Delta:
				if symbol != Epsilon():
					self.PDelta[symbol] = difference/(len(Delta) - 1)
		else:
			for symbol in Delta:
				if symbol != Epsilon():
					self.PDelta[symbol] = 0.0
		self.Confidence = 0.1

	def PrintTransition(self):
		return (self.startState.PrintState() +" -> "+self.endState.PrintState())

'''Globals  ----------------------------------------------------------------------------------------------'''
SIGMA = []
DELTA = []
Q = []
EPSILON = ''
outputFile = 'output.txt'
inputFileName = 'input.txt'
inputFile = None
usingFile = False;
m = None
EpislonCanLearn = False

'''Script Functions  ----------------------------------------------------------------------------------------------'''	

def main():
	global SIGMA,DELTA,m,Q
	LoadFromFile('Dog.txt')
	m = Model(SIGMA,DELTA)
	m.Q = Q
	m.Start(Q[0])

'''Gets input from user in form of symbol:strength pairs seperated by commas
i.e. A:0.2,B:0.4
DOES NOT CHECK IF INPUT IS VALID
'''
def GetInput():
	global usingFile
	if not usingFile:
		Iin = []
		userInput = input('\nPlease enter symbol streangth pairs seperated by , :\n')
		if (userInput == EPSILON  or userInput == "EPSION"):
			return EPSILON
		quit = ['quit','q']
		if (userInput.lower() in quit):
			exit()
		if userInput.lower() == 'status':
			status = m.PrintModel()
			#print(status)
			SaveStatusToFile(status)
			return GetInput()
		if userInput.lower() == 'read file':
			usingFile = True
			return GetFileInput()
		pairs = userInput.split(',')
		count = 0
		for pair in pairs:
			toks = pair.split(':')
			if len(toks) == 1:
				Iin = Iin +[[toks[0],1.0]]
			else:
				Iin = Iin+[[toks[0],float(toks[1])]]
			count += 1
		return Iin
	else:
		return GetFileInput()

'''Reads from the file if the flag is set true'''
def GetFileInput():
	global inputFile,inputFileName,usingFile
	if inputFile == None:
		inputFile = open(inputFileName,'r')
	Iin = []
	for line in inputFile:
		userInput = line.strip()
		quit = ['quit','q']
		if userInput == EPSILON or userInput == "EPSILON":
			print ('EPSILON')
			return EPSILON
		elif (userInput.lower() in quit):
			exit()
		elif userInput.lower() == 'status':
			status = m.PrintModel()
			#print(status)
			SaveStatusToFile(status)
			return GetInput()
		else:
			pairs = userInput.split(',')
			count = 0
			for pair in pairs:
				toks = pair.split(':')
				if len(toks) == 1:
					Iin = Iin +[[toks[0],1.0]]
				else:
					Iin = Iin+[[toks[0],float(toks[1])]]
				count += 1
				return Iin
	usingFile = False
	inputFile = None
	return GetInput()

'''Returns the epsilon value'''
def Epsilon():
	return EPSILON

'''Outputs to the console, will be updated as needed'''
def HandleOutput(outputString):
	print(outputString)

'''Takes a symbol in and returns the index of it within SIGMA'''
def GetSymbolIndex(symbol):
	for i in range(len(SIGMA)):
		if symbol == SIGMA[i]:
			return i
	return -1

def SaveStatusToFile(status):
	global outputFile,m
	file = open(outputFile,'w')
	file.write(status)
	print('[Message] Status saved to \"output.txt\"')
	#HTML OUT
	file = open('index.html','w')
	file.write(m.ProduceHTML())

def LoadFromFile(fileName):
	global SIGMA,DELTA,Q
	file = open(fileName,'r')
	sigma = []
	delta = []
	q = []
	count = 0
	for line in file:
		line = line.strip()
		if count == 0:
			sigma = [Epsilon()] + line.split(',')
			SIGMA = sigma
		elif count == 1:
			delta = [Epsilon()] + line.split(',')
			DELTA = delta
		elif count == 2:
			listOfQ = line.split(',')
			for i in listOfQ:
				i = int(i)
				q = q + [State(i)]
			Q = q
		else:
			if line[0] == 'T':
				line = line[2:]
				toks = line.split('=')
				left = toks[0].strip().split('>') # StartState + symbol
				right = toks[1].strip().split(':') # EndState : Confidence
				t = Transition(Q[int(left[0].strip())],Q[int(right[0].strip())])
				symbol = left[1].strip()
				if symbol == '?':
					symbol = Epsilon()
				t.GenerateNew(1.0,delta)
				t.SetConfidence(float(right[1].strip()))
				Q[int(left[0].strip())].AddTransitionOn(symbol,t)
				#print(t.PrintTransition())
			elif line[0] == 'P':
				line = line[2:]
				#print(line)
				toks = line.split('=')
				left = toks[0].strip().split('>')
				state = Q[int(left[0].strip())]
				symbolIndex = GetSymbolIndex(left[1].strip())
				distribution = {}
				i = 0
				total = 0
				for num in toks[1].strip().split(','):
					distribution[DELTA[i]] = float(num)
					total += float(num)
					i += 1
				if total != 1.0:
					print('Error in distributions, total is not out of 1:')
					pprint.pprint(distribution)
					for symbol in distribution.keys():
						distribution[symbol] = (distribution[symbol] + (1-total)/len(distribution))/ 1
					pprint.pprint(distribution)
				state.transitions[symbolIndex].PDelta = distribution
			elif line[0] == '+':
				toks = line.strip().split(' ')
				Q[int(toks[1])].isReward = True
			elif line[0] == '-':
				toks = line.strip().split(' ')
				Q[int(toks[1])].isPunishment = True


		count+=1
		'''
	for state in Q:
		print(state.PrintState())
	print(sigma)
	print(delta)
	'''
HTMLstart = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CS481 Output</title>
<script src="http://d3js.org/d3.v3.min.js" charset="utf-8"></script>
<style type="text/css">
</style>
</head>
<body>

<script type="text/javascript">

    var w = 1000;
    var h = 600;
    var linkDistance=200;

    var colors = d3.scale.category10();

    var dataset = {

    nodes: [
'''
HTMLend = '''
    ]
    };

 
    var svg = d3.select("body").append("svg").attr({"width":w,"height":h});

    var force = d3.layout.force()
        .nodes(dataset.nodes)
        .links(dataset.edges)
        .size([w,h])
        .linkDistance([linkDistance])
        .charge([-500])
        .theta(0.1)
        .gravity(0.05)
        .start();

 

    var edges = svg.selectAll("line")
      .data(dataset.edges)
      .enter()
      .append("line")
      .attr("id",function(d,i) {return 'edge'+i})
      .attr('marker-end','url(#arrowhead)')
      .style("stroke","#ccc")
      .style("pointer-events", "none");
    
    var nodes = svg.selectAll("circle")
      .data(dataset.nodes)
      .enter()
      .append("circle")
      .attr({"r":15})
      .style("fill",function(d) { return d.color;})//function(d,i){return colors(i);})
      .call(force.drag)


    var nodelabels = svg.selectAll(".nodelabel") 
       .data(dataset.nodes)
       .enter()
       .append("text")
       .attr({"x":function(d){return d.x;},
              "y":function(d){return d.y;},
              "class":"nodelabel",
              "stroke":"black"})
       .text(function(d){return d.name;});

    var edgepaths = svg.selectAll(".edgepath")
        .data(dataset.edges)
        .enter()
        .append('path')
        .attr({'d': function(d) {return 'M '+d.source.x+' '+d.source.y+' L '+ d.target.x +' '+d.target.y},
               'class':'edgepath',
               'fill-opacity':1,
               'stroke-opacity':1,
               'fill':function(d) {return d.color},
               'stroke':function(d) {return d.color},
               'id':function(d,i) {return 'edgepath'+i}})
        .style("pointer-events", "none");

    var edgelabels = svg.selectAll(".edgelabel")
        .data(dataset.edges)
        .enter()
        .append('text')
        .style("pointer-events", "none")
        .attr({'class':'edgelabel',
               'id':function(d,i){return 'edgelabel'+i},
               'dx':80,
               'dy':0,
               'font-size':15,
               'fill':'#aaa'});

    edgelabels.append('textPath')
        .data(dataset.edges)
        .attr('xlink:href',function(d,i) {return '#edgepath'+i})
        .style("pointer-events", "none")
        .text(function(d,i){return d.name});//'label '+i}); //THIS IS THE NAME OF THE LABEL


    svg.append('defs').append('marker')
        .data(dataset.edges)
        .attr({'id':'arrowhead',
               'viewBox':'-0 -5 10 10',
               'refX':25,
               'refY':0,
               //'markerUnits':'strokeWidth',
               'orient':'auto',
               'markerWidth':10,
               'markerHeight':10,
               'xoverflow':'visible'})
        .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#ccc')
            .attr('stroke','#ccc');
     

    force.on("tick", function(){

        edges.attr({"x1": function(d){return d.source.x;},
                    "y1": function(d){return d.source.y;},
                    "x2": function(d){return d.target.x;},
                    "y2": function(d){return d.target.y;}
        });

        nodes.attr({"cx":function(d){return d.x;},
                    "cy":function(d){return d.y;}
        });

        nodelabels.attr("x", function(d) { return d.x; }) 
                  .attr("y", function(d) { return d.y; });

        edgepaths.attr('d', function(d) { var path='M '+d.source.x+' '+d.source.y+' L '+ d.target.x +' '+d.target.y;
                                           //console.log(d)
                                           return path});       

        edgelabels.attr('transform',function(d,i){
            if (d.target.x<d.source.x){
                bbox = this.getBBox();
                rx = bbox.x+bbox.width/2;
                ry = bbox.y+bbox.height/2;
                return 'rotate(180 '+rx+' '+ry+')';
                }
            else {
                return 'rotate(0)';
                }
        });
    });

</script>

</body>
</html>
'''

if __name__ == '__main__':
	main()