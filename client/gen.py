import random
import SocketServer
import re
import sys
import time

from json import dumps

from collections import defaultdict

from common import *

def getHistDistr(lm, ngram):
	currRes = lm
	
	for token in ngram:
		if not token in currRes:
			return False
		currRes = currRes[token]
	
	if not countKey in currRes:
		return False
	total = currRes[countKey]
	
	try:
		distr = dict([ (k, currRes[k][countKey] / float(total)) for k in currRes if k != countKey ])
	except TypeError:
		distr = dict([ (k, currRes[k] / float(total)) for k in currRes if k != countKey ])
		
	
	return distr

def getLastNgram(sentence, ngramSize):
	return [getToken(sentence, len(sentence) - 1 - idx) for idx in reversed(range(ngramSize))]

def addWeightedDistr(tgtDistr, srcDistr, weight):
	if srcDistr:
		for k in srcDistr:
			tgtDistr[k] += weight * srcDistr[k]

def getRandomFromDistr(distr):
	rndVal = random.random() * sum([distr[k] for k in distr])
	baseSum = 0.0
	
	for k in distr:
		baseSum += distr[k]
		if rndVal < baseSum:
			return k
	
	#raise Exception("Oops " + str(rndVal) + ", " + str(baseSum) + "; " + str(distr))
	return "</s>";

def getPrediction(output, lms, weights, ngramSize):
	lastNgram = getLastNgram(output, ngramSize)
	
	baseDistr = defaultdict(float)
	
	for lm, weight in zip(lms, weights):
		distr = getHistDistr(lm, lastNgram)
		
		addWeightedDistr(baseDistr, distr, weight)
	
	prediction = getRandomFromDistr(baseDistr)
	
	return [prediction]

def donePredicting(prediction):
	return prediction == [sntEndKey]

def generate(lms, weights, startWith = [], ngramSize = maxNgramSize - 1):
	output = []
	
	prediction = startWith
	
	while not donePredicting(prediction):
		output += prediction
		
		prediction = getPrediction(output, lms, weights, ngramSize)
	
	return " ".join(output)

def idFromName(name):
	res = re.match(r'[A-Za-z]+', name)
	if res:
		return res.group(0)
	else:
		return "Unk"

def test(lm):
	print generate([lm], [1.0])

class Handler(SocketServer.BaseRequestHandler):
	def handle(self):
		self.data = self.request.recv(1024).strip()
		print "request:", self.data
		
		if self.data == "identify":
			result = self.server.ids
			print "asked for the id, gave", result
		else:
			lms = self.server.lms
			
			toks = self.data.split()
			weights = [float(strWeight) for strWeight in toks[0].split(',')]
			
			ngramSize = int(toks[1])
			
			startWith = toks[2:]
			
			result = generate(lms, weights, startWith = startWith, ngramSize = ngramSize)
			print "asked for a new sentence, gave", result
		
		self.request.sendall(result)

if __name__ == "__main__":
	print time.strftime("%H:%M:%S") + " loading"
	lms = [loadlm(filename) for filename in sys.argv[1:]]
	ids = " ".join([idFromName(name) for name in sys.argv[1:]])
	
	server = SocketServer.TCPServer(("localhost", 13579), Handler)
	server.lms = lms
	server.ids = ids
	
	print time.strftime("%H:%M:%S") + " serving"
	server.serve_forever()
