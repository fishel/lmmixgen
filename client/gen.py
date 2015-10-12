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
		distr = dict([ (k, currRes[k][countKey] / float(total)) for k in currRes if not k in (countKey, sizeKey, sntStartKey)])
	except TypeError:
		distr = dict([ (k, currRes[k] / float(total)) for k in currRes if not k in (countKey, sizeKey, sntStartKey)])
	
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
	
	result = " ".join(output)
	
	result = re.sub(r'([0-9]) : ([0-9])', r'\1:\2', result)
	result = re.sub(r' ([.,?!;:])', r'\1', result)
	result = re.sub(r'(^ *|[.,?!;:] +)([a-z])', lambda pat: pat.group(1) + pat.group(2).upper(), result)
	result = result.rstrip()
	
	return result

def idFromName(name):
	res = re.match(r'[A-Za-z]+', name)
	if res:
		return res.group(0)
	else:
		return "Unk"

def test(lm):
	print generate([lm], [1.0])

def sizeOk(lms, size):
	for lm in lms:
		if lm[sizeKey] - 1 < size:
			return False
	
	return True

def handleLine(line, lms, ids, v = True):
	print "request:", line
	
	if line == "identify":
		if v:
			print "asked for the id, gave", ids
		return ids
	else:
		toks = line.split()
		weights = [float(strWeight) for strWeight in toks[0].split(',')]
		
		ngramSize = int(toks[1])
		
		if sizeOk(lms, ngramSize):
			startWith = toks[2:]
			
			result = generate(lms, weights, startWith = startWith, ngramSize = ngramSize)
			if v:
				print "asked for a new sentence, gave", result
			return result
		else:
			if v:
				print "asked with history bigger than the LMs we have, fail"
			return "FAIL"

class Handler(SocketServer.BaseRequestHandler):
	def handle(self):
		self.data = self.request.recv(1024).strip()
		
		result = handleLine(self.data, self.server.lms, self.server.ids)
		
		self.request.sendall(result)

if __name__ == "__main__":
	try:
		lmFileList = sys.argv[1:]
		
		if lmFileList[0][0] == '-':
			lmFileList = lmFileList[1:]
			doStdin = True
		else:
			doStdin = False
		
		print time.strftime("%H:%M:%S") + " loading"
		
		lms = [loadlm(filename) for filename in lmFileList]
		
		ids = " ".join([idFromName(name) for name in lmFileList])
		
		if doStdin:
			print time.strftime("%H:%M:%S") + " serving"
			for line in sys.stdin:
				print handleLine(line.rstrip(), lms, ids)
		else:
			server = SocketServer.TCPServer(("localhost", 13579), Handler)
			server.lms = lms
			server.ids = ids
			
			print time.strftime("%H:%M:%S") + " serving"
			server.serve_forever()
	except (IndexError):
		sys.stderr.write("Usage: gen.py [-stdin] lm1 [lm2 [...]]\n")
		sys.exit(-1)
