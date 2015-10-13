import random
import SocketServer
import re
import sys
import time

from collections import defaultdict

from common import *

def combKey(key, subkey):
	return key + " " + subkey if subkey else key

def tofloat(lm):
	result = dict()
	result[sizeKey] = lm[sizeKey]
	
	for k in lm:
		if k != sizeKey:
			result[k] = dict([(p, lm[k][p] / lm[k][countKey]) for p in lm[k] if not p in (countKey, sntStartKey)])
	
	return result

def filter(lm, cutoff = 10):
	result = dict()
	result[sizeKey] = lm[sizeKey]
	
	for k in lm:
		if k != sizeKey:
			result[k] = dict(sorted([(p, lm[k][p]) for p in lm[k]], key = lambda z: -z[1])[:cutoff])
	
	return result

def flatten(lm):
	result = dict()
	result[""] = dict()
	result[""][countKey] = lm[countKey]
	
	for key in lm:
		if not key in (countKey, sizeKey):
			# flat dictionary:
			try:
				_ = lm[key][countKey]
			except (TypeError):
				return {"": lm}
			
			# non-flat dictionary
			leaf = flatten(lm[key])
			result[""][key] = lm[key][countKey]
			
			#leaf is a flat dictionary
			for subkey in leaf:
				result[combKey(key, subkey)] = leaf[subkey]
	
	if sizeKey in lm:
		result[sizeKey] = lm[sizeKey]
	
	return result

def getHistDistr(lm, ngram):
	return lm[" ".join(ngram)]

def xgetHistDistr(lm, ngram):
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
	result = re.sub(r'&#91;', '[', result)
	result = re.sub(r'&#93;', ']', result)
	result = re.sub(r'&amp;', '&', result)
	result = re.sub(r'&apos;', '\'', result)
	result = re.sub(r'&gt;', '>', result)
	result = re.sub(r'&lt;', '<', result)
	result = re.sub(r'&quot;', '"', result)

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
	if size <= 0:
		return False
		
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
				print "asked with history bigger than the LMs we have (or <= 0), fail"
			return "FAIL"

class Handler(SocketServer.BaseRequestHandler):
	def handle(self):
		self.data = self.request.recv(1024).strip()
		
		result = handleLine(self.data, self.server.lms, self.server.ids)
		
		self.request.sendall(result)

def startServerOrFilter():
	try:
		lmFileList = sys.argv[1:]
		
		if lmFileList[0][0] == '-':
			lmFileList = lmFileList[1:]
			doStdin = True
		else:
			doStdin = False
		
		print time.strftime("%H:%M:%S") + " loading"
		
		lms = [filter(tofloat(flatten(loadlm(filename))), cutoff=30) for filename in lmFileList]
		
		ids = " ".join([idFromName(name) for name in lmFileList])
		
		print time.strftime("%H:%M:%S") + " serving"
		if doStdin:
			for line in sys.stdin:
				handleLine(line.rstrip(), lms, ids)
			print time.strftime("%H:%M:%S") + " done"
		else:
			server = SocketServer.TCPServer(("localhost", 13579), Handler)
			server.lms = lms
			server.ids = ids
			
			server.serve_forever()
	except (IndexError):
		sys.stderr.write("Usage: gen.py [-stdin] lm1 [lm2 [...]]\n")
		sys.exit(-1)

if __name__ == "__main__":
	startServerOrFilter()
