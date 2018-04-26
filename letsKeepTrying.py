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
		self.c = None
		self.I = [] #List of input symbol and strength pairs
		self.Il = self.I #Last set of inputs
		self.ql = None #Last state
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
		self.Q = self.Q + [q0]
		self.c = q0
		self.ql = q0
		self.qa = q0
		self.Cycle()

	'''
	Step 2-On
	'''
	def Cycle(self):
		self.Il = self.I #Step 3
		self.I = GetInput()
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
			HandleOutput('Time greater than tau passed')
			return self.Cycle()
		(self.ad,self.sd) = self.HandleInput(self.I) #Step 4
		self.CreateTransitions() #Step 5
		self.ol = self.o #Step 6
		self.o = self.c.transitions[GetSymbolIndex(self.ad)].ChooseOuput() #Step 7
		#Determine Rewards based on some output stuff here?
		Sout = (self.sd*self.c.transitions[GetSymbolIndex(self.ad)].GetConfidence())/(1+self.c.transitions[GetSymbolIndex(self.ad)].GetConfidence())
		HandleOutput('Output: '+self.o+' with strength '+str(Sout))
		self.Omicron = self.Omicron + [self.o] #Step 8
		self.OmicronDist = self.OmicronDist + [self.c.GetNextState(self.ad)]
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
		self.Cycle() #Step 12

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
				found = False
				for state in self.Q:
					told = state.transitions[GetSymbolIndex(ai)]
					if told != None:
						temp.CopyTransition(told)
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
					hasA = False
					hasB = False
					for pair in self.I:
						if a in pair:
							hasA = True
						if b in pair:
							hasB = True
					t5 = self.c.transitions[GetSymbolIndex(a)] #c on a
					t6 = self.c.transitions[GetSymbolIndex(b)] #c on b
					if t5 != None and t6 != None:
						if t5 in t6.Expectations.keys():
							if hasA and hasB:
								deltaE = self.alpha * (1-t5.Expectations[t6])
								t5.Confidence *= (1-self.beta*abs(deltaE))
								t5.Expectations[t6] += deltaE
								deltaE = self.alpha * (1-t6.Expectations[t5])
								t6.Confidence *= (1-self.beta*abs(deltaE))
								t6.Expectations[t5] += deltaE
							elif hasA or hasB:
								deltaE = -self.alpha * t5.Expectations[t6]
								t5.Confidence *= (1-self.beta*abs(deltaE))
								t5.Expectations[t6] += deltaE
								deltaE = -self.alpha * t6.Expectations[t5]
								t6.Confidence *= (1-self.beta*abs(deltaE))
								t6.Expectations[t5] += deltaE

	#!!!!!!!!!!!!!!!!CHECK THIS LOGIC!!!!!!!!!!!!!!!!!!!!!!!!!!!
	def ApplyReward(self):
		t = 1
		for i in range(len(self.OmicronDist),-1,-1):
			distribution = self.OmicronDist[i].PDelta
			symbol = self.Omicron[i]
			distribution[symbol] = (distribution[symbol] + self.zeta*t*self.sd*1/self.OmicronDist[i].GetConfidence())/(1+self.zeta*t*self.sd*1/self.OmicronDist[i].GetConfidence())
			for b in self.Sigma:
				if b != symbol:
					distribution[b] = (distribution[symbol])/(1+self.zeta*t*self.sd*1/self.OmicronDist[i].GetConfidence())
			self.OmicronDist[i].Confidence += self.zeta*t*self.sd

	#!!!!!!!!!!!!!!!!CHECK THIS LOGIC!!!!!!!!!!!!!!!!!!!!!!!!!!!		
	def ApplyPunishment(self):
		pass

	def ApplyConditioning(self):
		pass

	def UpdateConditioning(self):
		pass

	def PrintModel(self):
		output = '\n'
		output += 'Current State: '+self.c.PrintState()+'\n'
		output += 'Last State: '+self.ql.PrintState()+'\n'
		output += '\n------- All States ------\n'
		for q in self.Q:
			output += '[+] '+ q.PrintState() +'\n'
			for a in self.Sigma:
				t = q.transitions[GetSymbolIndex(a)]
				if t != None:
					output += '['+a+']'+t.PrintTransition()
					if t.isTemporary:
						output += ' [Temp]\n'
					else:
						output += '\n'
					output += 'Confidence: '+str(t.GetConfidence())+'\n'
					for to in t.Expectations.keys():
						output += '('+t.PrintTransition()+') + ('+to.PrintTransition()+') = '+str(t.Expectations[to]) +'\n'
				else:
					output += '['+a+'] None\n'
			output += '\n'
		output += '\n'
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
			print('Transition for the symbol %s already exists for this state %s' %(symbol,self.PrintState()))
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
EPSILON = ''
m = None

'''Script Functions  ----------------------------------------------------------------------------------------------'''	

def main():
	global SIGMA, DELTA, m
	SIGMA = [EPSILON,'a','b']
	DELTA = [EPSILON,'alpha','beta']
	m = Model(SIGMA,DELTA,eta=0.2)
	s0 = State(0)
	s1 = State(1)
	t = Transition(s0,s1)
	t.GenerateNew(m.eta,DELTA)
	t.SetConfidence (100)
	s0.AddTransitionOn('a',t)
	m.Q = m.Q + [s1]
	m.Start(s0)
	#GetInput()

'''Gets input from user in form of symbol:strength pairs seperated by commas
i.e. A:0.2,B:0.4
DOES NOT CHECK IF INPUT IS VALID
'''
def GetInput():
	Iin = []
	userInput = input('\nPlease enter symbol streangth pairs seperated by , :\n')
	if (userInput == EPSILON):
		return EPSILON
	quit = ['quit','q']
	if (userInput.lower() in quit):
		exit()
	if userInput.lower() == 'status':
		print(m.PrintModel())
		return GetInput()
	pairs = userInput.split(',')
	count = 0
	for pair in pairs:
		toks = pair.split(':')
		Iin = Iin+[[toks[0],float(toks[1])]]
		count += 1
	return Iin

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

if __name__ == '__main__':
	main()