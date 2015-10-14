import sys
import time

from collections import defaultdict

from common import *

def loadCorpus(filename):
	fh = open(sys.argv[1], 'r')
	
	for line in fh:
		yield line.rstrip().split()

def estimateLm(corpus, ngramSize = maxNgramSize):
	lm = defaultdict(float)
	lm[sizeKey] = ngramSize
	
	i = 0
	for tokens in corpus:
		i += 1
		if not i % 100000:
			log("line " + str(i))
		for idx in range(-ngramSize + 1, len(tokens)):
			tgt = lm
			
			for ngramIter in range(ngramSize):
				tgt[countKey] += 1.0
				
				token = getToken(tokens, idx + ngramIter)
				
				if ngramIter == ngramSize - 1:
					tgt[token] += 1.0
				else:
					if not token in tgt:
						tgt[token] = defaultdict(float)
					
					tgt = tgt[token]
	if i % 100000:
		log("line " + str(i))
	
	return lm

if __name__ == "__main__":
	try:
		log("loading")
		corpus = loadCorpus(sys.argv[1])
		
		lm = estimateLm(corpus, ngramSize = maxNgramSize)
		
		log("saving")
		savelm(lm, sys.argv[2])
		
		log("done")
	except IndexError:
		sys.stderr.write("Usage: createlm.py  corpus-file.txt  lm-file.txt\n")
		sys.exit(-1)
