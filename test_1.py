#!python
import copy, random, pprint

# TRANSITION class
class Transition(object):

	def __init__(self,goToState,probability=0.0):
		self.nextState = goToState
		self.probability = probability
		self.isTemporary = False
		self.isPermanent = False

	def markTemporary(self):
		self.isTemporary = True

	def markPermanent(self):
		self.isPermanent = True

	def getNextState(self):
		return self.nextState

	def changeNextState(state):
		self.nextState = state

	def getProbability(self):
		return self.probability

	def setProbability(self,pNew):
		self.probability = pNew

	def updateProbability(self,delta,isTarget=False):
		if isTarget:
			self.probability = (self.probability + delta) / (1+delta)
		else:
			self.probability = (self.probability) / (1+delta)

	def getComplementaryEpsilonTransition(self,state):
		return Transition(state,1-self.probability)

	def toString(self):
		return str(self.probability)

# STATE class
class State(object):
	SIGMA = ['epsilon']
	accepting = True

	def __init__(self,name=''):
		self.transitions = {}
		self.name = name

	def addTransition(self,stimuli,transition):
		if stimuli in self.transitions.keys():
			stimTransitions = self.transitions[stimuli]
			if transition not in stimTransitions:
				pCur = transition.getProbability()
				self.transitions[stimuli] = stimTransitions + [transition]
				for t in self.transitions[stimuli]:
					t.updateProbability(pCur)
			else:
				print("Error in addTransition: transition already added for stimuli '%s'" %(str(stimuli)))
		else:
				self.transitions[stimuli] = [transition]
				if stimuli not in State.SIGMA and State.accepting:
					State.SIGMA = State.SIGMA + [stimuli]

	def createTransition(self,stimuli,weight,state,absoluteWeight = False):
		temp = Transition(state,weight)
		self.addTransition(stimuli,temp)
		if absoluteWeight:
			setTransitionWeight(stimuli,temp,weight)

	def updateStimuliTransitionWeight(self,stimuli,transition,weight):
		if stimuli in self.transitions.keys():
			if transition in self.transitions[stimuli]:
				for t in self.transitions[stimuli]:
					t.updateProbability(weight,t == transition)
			else:
				print("Error in updateStimuliTransitionWeight: Transition not in the stimuli %s" %(str(stimuli)))
		else:
			print("Error in updateStimuliTransitionWeight: Stimuli '%s' not registered as a transition cue" %(str(stimuli)))

	def getTransition(self,stimuli,index):
		if stimuli not in self.transitions.keys():
			print('Error in getTransition: Stimuli \'%s\' not registered' %(str(stimuli)))
			return None
		if index <= len(self.transitions[stimuli]) and index >= 0:
			return self.transitions[stimuli][index]
		else:
			print(str(index)+' is not a valid index for Transitions')

	def setTransitionWeight(self, stimuli, transition, newWeight):
		if stimuli not in self.transitions.keys():
			print('Error in setTransitionWeight: \'%s\' not in stimuli' %(stimuli))
		if transition not in self.transitions[stimuli]:
			print('Error in setTransitionWeight: transition does not exist')
		oldWeight = transition.getProbability()
		delta = (oldWeight - newWeight)/(newWeight - 1)
		for t in self.transitions[stimuli]:
			t.updateProbability(delta,t == transition)


	def goToNextState(self,stimuli): #delta
		if stimuli not in State.SIGMA:
			print('Stimuli not within accepted alphabet')
			return None
		if stimuli not in self.transitions.keys():
			print('Error in goToNextState: Stimuli \'%s\' not registered' %(str(stimuli)))
			return None
		value = random.uniform(0,1)
		transitionIndex = 0
		stimTransitions = self.transitions[stimuli]
		curTransition = stimTransitions[transitionIndex]
		total = curTransition.getProbability()
		while value > total:
			transitionIndex += 1
			if transitionIndex > len(stimTransitions):
				return None
			curTransition = stimTransitions[transitionIndex]
			total = total + curTransition.getProbability()
		return curTransition.getNextState()

	def getTransitions(self):
		return self.transitions

	def getStimuli(self):
		return self.transitions.keys()

	def getName(self):
		return self.name

	def toString(self):
		out = 'State: '+self.name+'\n'
		for stimuli in self.transitions.keys():
			out = out + 'Stimuli = ' +str(stimuli) + ':\n'
			count = 0
			for transition in self.transitions[stimuli]:
				out = out + str(count) + ': ' + transition.toString() + ' -> ' + transition.getNextState().getName() + '\n'
				count += 1
		return out

#Variables:
Q = []

#EXPERIMENT CODE:
def main():
	manuallyRunExperiment(experiment1())

def experiment1():
	global Q
	State.accepting = True
	#Models Figure 2.1
	q0 = State('q0')
	q1 = State('q1')
	Q = Q + [q0,q1]

	q0.createTransition('0',1.0,q0)
	q0.createTransition('1',1.0,q1)
	q1.createTransition('0',1.0,q1)
	q1.createTransition('1',1.0,q0)
	q1.createTransition('1',1.0,q1)


	print(q0.toString())
	print(q1.toString())
	return q0

def experiment2():
	base = State('Base')
	salivating = State('Salivating')
	notHungry = State('Not Hungry')
	full = State('Full')

	t_b_s = Transition(salivating,1.0)
	t_s_f = Transition(full,1.0)
	t_f_b = Transition(base,1.0)
	t_b_nh = Transition(notHungry,.2)
	t_nh_b = Transition(base,1.0)

	base.addTransition('food given',t_b_s)
	salivating.addTransition('food eaten',t_s_f)
	full.addTransition('epsilon',t_f_b)
	base.addTransition('food given',t_b_nh)
	notHungry.addTransition('epsilon',t_nh_b)

	salivating.createTransition('epsilon',1.0,base)
	base.createTransition('epsilon',1.0,base)

	print(base.toString())
	print(salivating.toString())
	print(full.toString())
	return base

def manuallyRunExperiment(startingState):
	State.accepting = False
	quit = ['q','quit','exit' ]
	curState = startingState
	print (State.SIGMA)
	print ('Enter stimuli, enter exit parameter to stop experiment...')
	print ("Current state = " + curState.getName())
	stimuli = input()
	while stimuli.lower() not in quit:
		if stimuli == '':
			stimuli = 'epsilon'
		nextState = curState.goToNextState(stimuli)
		if nextState == None:
			#TODO Maybe have non known stimuli grow knew states
			if stimuli in State.SIGMA:
				GrowNewState(curState,stimuli)
			#print ('Stimuli had no effect')
		else:
			curState = nextState
		print ("Current state = " + curState.getName())
		stimuli = input()
	print ('Experiment concluded')

def timeStep():
	#Take one step through time
	#runExperiment does a step by taking in a stimuli as input
	pass

def GrowNewState(startState,stimuli):
	global Q
	qn = State('q'+str(len(Q)))
	Q = Q + [qn]
	startState.createTransition(stimuli,1.0,qn)
	print('New State Formed')

def MaintainTransitionsThatRelate():
	#Cannot go to two states at the same time or coexist in states
	#Does not know that any transitions are related in any way
	pass

def DetermineConfidence():
	#Transitions hold their confidence and states update it
	pass

def ModifyProbabiliteis():
	#States have this ability to all transitions relating to a stimuli
	pass

'''TODO need to handle temporal relationships between stimuli and
	need to handle condition starting and ending.
'''
#def copyState(state):
#	return copy.copy(state)

if __name__ == '__main__':
	main()