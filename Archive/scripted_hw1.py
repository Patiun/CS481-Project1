#HP
tau = 1#?
alpha = 0.05
beta = 0.05
gamma = 0.2
eta = 1.0
zeta = 0.0
nu  = 0.0
kappa = 0.0
EPSILON = ''
#VAR
q0 = None
o = EPSILON
Sigma = []
Delta = []
c = []
ql = []
I = [[]]
Isymbols = []
Il = I
Q = [] #states
delta = {{}} #[state][symbol]
PoDelta = {{{}}} #[state][inputsybol][outputsymbol]
C = {{}} #[state][symbol]
E = {{}} #[transition1][transition2]

def main():
	pass

def runExperient(startState):
	global q0
	q0 = startState
	step1()

def step1():
	c = [q0]
	ql= [q0]
	al = EPSILON
	ol = EPSILON
	step2()

def step2():
	if time > tau:
		qnx = deta(c,EPSILON)
		if qnx in Q: #THIS MIGHT MEAN TRANSITION NOT STATE
			if qnx.isTemporary:
				qnx.isPermanent
			ql = c
			c = qnx
		qa = c
		al = EPSILON
		ol = EPSILON
		#unmark things

		step2()
	else:
		step3()

def step3On():
	Il = I
	I = getInput()
	createNewTransitions()
	strongestPair = getStrongest(I)
	ad = strongestPair[0]
	sd = strongestPair[1]
	ql = c
	al = ad
	ol = o
	#markThings
	c = delta(c,a)
	updateExpectations()
	if c in R:
		applyReward()
	else if c in P:
		applyPunishment()
	else:
		applyConditioning()
	step2()

def getInput(): #sequence of "A:0.5,B:0.6"
	It = [[]]
	ItCount = 0
	recentInput = input()
	It[ItCount] = recentInput.split(',')
	while recentInput != EPSILON:
		ItCount += 1
		It[ItCount] = recentInput.split(',')

	for i in range(len(It)):
		temp = []
		row = It[i]
		for element in row:
			toks = element.split(':')
			count = len(temp)
			temp[count] = {toks[0]:toks[1]}
			if toks[0] not in Isymbol:
				Isymbol = Isymbol + [toks[0]]
		It[i] = temp

	return It

def getStrongest(I):
	best = ('',0)
	for row in I:
		for symbol in row.keys():
			if row[symbol] > best[1]:
				best = (symbol,row[symbol])
	return best

def delta(state,symbol):
	pass

def createNewTransitions():
	global Q
	qnx = delta(c,EPSILON)
	if qnx != None and qnx.isTemporary:
		#Remove transition to qnx
	for row in I:
		for ai in row.keys():
			si = row[ai]
			if delta(c,ai) == None:
				qn = new State() #make new state
				Q = Q + [qn]
				c.addTransition(ai,qn)
				c.addTransition(EPSILON,qa)
				for qprime in Q:
					if delta(qprime,ai) != None:
						PoDelta[c][ai] = PoDelta[qprime][ai]
						C[c][ai] = C[qprime][ai]
					else:
						PoDelta[qn][ai][EPSILON] = eta
						#Do the rest of the output symbols

def updateExpectations():
	t1 = delta[ql][al]
	t2 = delta[c][ad]
	if t1 in E.keys() and t2 in E[t1].keys():
		Eo = E[t1][t2]
		Ed = E[t2][t1]
		deltaElast = alpha*(1-Eo)
		C[ql][al] = C[ql][al]*(1-beta*abs(deltaElast))
		deltaEcur = alpha*(1-Ed)
		C[c][ad] = C[c][ad]*(1-beta*abs(deltaEcur))
		E[t1][t2] += Eo
		E[t2][t1] += Ed
	else:
		E[t1][t2] = alpha
		E[t2][t1] = alpha

	for a in Sigma:
		t3 = delta[c][a]
		if t1 in E.keys() and t3 in E[t1].keys():
			deltaE = -alpha*E[t1][t3]
			C[c][ad] = C[c][ad]*(1-beta*abs(deltaE))
			E[t1][t3] += deltaE

	for q in Q:
		for a in Sigma:
			if q != ql or a != al:
				if t1 in E.keys() and t4 in E[t1].keys():
				t4 = delta[q][a]
				Eo = E[t2][t4]
				deltaE = -alpha*Eo
				C[c][ad] = C[c][ad]*(1-beta*abs(deltaE))
				E[t1][t4] += Eo

	for a in Sigma:
		for b in sigma:
			if a != b:
				if a in Isymbol and b in Isymbol:
					t5 = delta[c][a]
					t6 = delta[c][b]
					Eo = E[t5][t6]
					deltaE = alpha*(1-Eo)
					C[c][a] = C[c][a]*(1-beta*abs(deltaE))
					E[t5][t6] += deltaE
				else if a in Isymbol or b in Isymbol:
					t5 = delta[c][a]
					t6 = delta[c][b]
					Eo = E[t5][t6]
					deltaE = -alpha*(1-Eo)
					C[c][a] = C[c][a]*(1-beta*abs(deltaE))
					E[t5][t6] += deltaE

	pass

def applyReward():
	pass

def applyPunishment():
	pass

def applyConditioning():
	pass


if __name__ == '__main__':
	main()