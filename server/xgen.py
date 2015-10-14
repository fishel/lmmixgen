import gen
import common
import createlm

from collections import defaultdict

from json import dumps

def loadFlatLm(filename, ngramSize):
	result = defaultdict(lambda: defaultdict(float))
	result[common.sizeKey] = ngramSize
	
	i = 0
	for tokens in createlm.loadCorpus(filename):
		i += 1
		
		if not i % 100000:
			gen.log("line " + str(i))
		
		for idx, token in enumerate(tokens + [common.sntEndKey]):
			for histSize in range(1, ngramSize):
				history = " ".join([common.getToken(tokens, histIdx) for histIdx in range(idx - histSize, idx)])
				result[history][token] += 1
				result[history][common.countKey] += 1
	return result

def createLms(lmFileList, ngramSize = common.maxNgramSize):
	gen.log("loading")
	
	lms = list()
	
	for filename in lmFileList:
		lms += [gen.tofloat(gen.filter(loadFlatLm(filename, ngramSize), cutoff=30))]
		gen.log("loaded " + filename)
	
	return lms

if __name__ == "__main__":
	try:
		lmFileList, doStdin = gen.doArgs()
		lms = createLms(lmFileList)
		ids = gen.getIds(lmFileList)
		
		if doStdin:
			gen.stdinFilter(lms, ids)
		else:
			gen.startServer(lms, ids)
	except (IndexError):
		sys.stderr.write("Usage: gen.py [-stdin] lm1 [lm2 [...]]\n")
		sys.exit(-1)
