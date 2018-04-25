#!Python

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
		self.Q = []
		self.Sigma = Sigma
		self.Delta = Delta
		self.Omicron = []
		self.c = None
		self.I = []
		self.Il = I

	def Start():
		#Create or read in experiment

		pass

	def CreateTransition():
		pass

	'''Has 
	Hyper parameters
	Q = [] list of states
	q0 = starting state
	Sigma = [] list of input symbols (mutable)
	Delta = [] list of output symbols (imutable?)
	Omicron = [] list of marked output symbols
	'''

class State(object):

	def __init__(self,isPunishment=False,isReward=True):
		self.isReward = isReward
		self.isPunishment = isPunishment
		self.transitions = []

	'''
	Has
	delta = {[]} get next state from 
	R = bool is it a reward state
	P = bool is it a punishment state
	'''

class Transition(object):

	def __init__(self,goToState,confidence=100000):
		pass

	'''
	has
	lambda = sigma(P^Delta) the ability to choose output from its own distribution of outputs
	PDelta = {} probablistic disribution of outputs
	C = float the confidence in this transition
	E = {} expectation that this transition is related to other transitions
	'''

def main():
	pass

if __name__ == '__main__':
	main()