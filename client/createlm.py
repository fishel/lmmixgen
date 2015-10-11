import sys

from collections import defaultdict

from common import *

def loadCorpus(filename):
	fh = open(sys.argv[1], 'r')
	
	for line in fh:
		yield line.rstrip().split()

def estimateLm(corpus):
	lm = defaultdict(float)
	
	for tokens in corpus:
		for idx in range(-maxNgramSize + 1, len(tokens)):
			tgt = lm
			
			for ngramSize in range(maxNgramSize):
				tgt[countKey] += 1.0
				
				token = getToken(tokens, idx + ngramSize)
				
				if ngramSize == maxNgramSize - 1:
					tgt[token] += 1.0
				else:
					if not token in tgt:
						tgt[token] = defaultdict(float)
					
					tgt = tgt[token]
	
	return lm

if __name__ == "__main__":
	try:
		corpus = loadCorpus(sys.argv[1])
		
		lm = estimateLm(corpus)
		
		savelm(lm, sys.argv[2])
		
		print "ok"
	except IndexError:
		sys.stderr.write("Usage: createlm.py  corpus-file.txt  lm-file.txt\n")
		sys.exit(-1)