#!Python
import random
import re

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

	def __init__(self,Sigma,Delta,tau=1,alpha=0.05,beta=0.05,gamma=0.2,eta=1.0,zeta=0.0,nu=0.0,kappa=0.0):
		#Hyperparameters
		self.tau = tau
		self.alpha = alpha
		self.beta = beta
		self.gamma = gamma
		self.eta = eta 
		self.zeta = zeta
		self.nu  = nu
		self.kappa = kappa
		self.EPSILON = ''
		#Variables
		self.Q = [] #List of all states
		self.Sigma = Sigma 
		self.Delta = Delta
		self.Omicron = [] #List of outputed symbols
		self.c = None
		self.I = [] #List of input symbol and strength pairs
		self.Il = I

	'''
	Starts up the model.
	Sets the global alphabets to the inputed ones for reference
	'''
	def Start(self):
		#Create or read in experiment
		global SIGMA,DELTA
		SIGMA = self.sigma
		DELTA = self.delta

	def HandleInput(self,inputString):
		pass

	def CreateTransitions(self):
		pass

	def UpdateExpectations(self):
		pass

	def ApplyReward(self):
		pass

	def ApplyPunishment(self):
		pass

	def ApplyConditioning(self):
		pass

	def UpdateConditioning(self):
		pass

'''State Class ----------------------------------------------------------------------------------------------
Has:
	delta = {[]} get next state from 
	R = bool is it a reward state
	P = bool is it a punishment state
	'''
class State(object):

	def __init__(self,model,isPunishment=False,isReward=True):
		global SIGMA
		self.isReward = isReward
		self.isPunishment = isPunishment
		self.transitions = [None] * len(SIGMA) #List of transitions where index matches symbols in SIGMA

	'''delta
	Takes in a symbol and follows that transition
	Returns the next state or None if the transition is not defined'''
	def GetNextState(self,symbol):
		return self.transitions[GetSymbolIndex(symbol)].TakeTransition(symbol)

	'''adds the transition to the array of transitions at the index of the given symbol if it does not exists already'''
	def AddTransitionOn(self,symbol,transition):
		index = GetSymbolIndex(symbol)
		if self.transitions[index] == None:
			self.transitions[index] = transition
		else:
			#DEBUG
			print('Transition for the symbol %s already exists for this state %s' %(symbol,str(self)))
	
'''Transition Class ----------------------------------------------------------------------------------------------
Has:
	lambda = sigma(P^Delta) the ability to choose output from its own distribution of outputs
	PDelta = {} probablistic disribution of outputs
	C = float the confidence in this transition
	E = {} expectation that this transition is related to other transitions
	'''
class Transition(object):

	def __init__(self,fromState,goToState,confidence=100000):
		self.startState = fromState
		self.endState = goToState
		self.PDelta = {} #Key: Symbol | Value [0,1] probability of it being produced
		self.C = float
		self.E = {} #Key: Transition | Value: [0,1] expectation value

	'''lamdba'''
	def ChooseOuput(self):
		global DELTA
		rand = random.range(0,len(DELTA)-1)
		level = 0
		for symbol in self.PDelta.keys():
			level += self.PDelta[symbol]
			if rand <= level:
				#!TODO! enable proper output and working with model's omicron
				Output('Output: '+str(symbol))

	'''returns the next endState and chooses the output'''
	def TakeTransition(self,symbol):
		self.ChooseOuput()
		return self.endState

	'''returns the confidence'''
	def GetConfidence(self):
		return self.C

	'''returns the expectation value with transition, if E(t1,t2) does not exist it returns None'''
	def GetExpectationWith(self,transition):
		if transition not in self.E.keys():
			return None
		else:
			return self.E[transition]

	'''
	TODO:
		update probabilities
		update expectations
		mark distribution
		mark output	
	'''

'''Globals  ----------------------------------------------------------------------------------------------'''
SIGMA = []
DELTA = []

'''Script Functions  ----------------------------------------------------------------------------------------------'''	

def main():
	GetInput()

'''Gets input from user in form of symbol:strength pairs seperated by commas
i.e. A:0.2,B:0.4
'''
def GetInput():
	rawPattern = "\w+:\d.\d,*"
	pattern = re.compile(rawPattern)
	print('Enter set of symbol strength pairs linked by : and seperated by ,')
	userInput = input()
	toks = pattern.split(userInput)
	if toks:
		print("We got one!")
		print(toks)
	else:
		print("We fucked up")


'''Outputs to the console, will be updated as needed'''
def Output(outputString):
	print(outputString)

'''Takes a symbol in and returns the index of it within SIGMA'''
def GetSymbolIndex(symbol):
	for i in range(len(SIGMA)):
		if symbol == SIGMA[i]:
			return i
	return -1

if __name__ == '__main__':
	main()