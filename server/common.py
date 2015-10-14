import time
import sys
from pickle import dump, load, HIGHEST_PROTOCOL

maxNgramSize = 4

countKey = '___'
sizeKey = '___size'

sntStartKey = '<s>'
sntEndKey = '</s>'

def log(msg):
	sys.stderr.write(time.strftime("%H:%M:%S") + " " + msg + "\n")

def getToken(sentence, idx):
	if idx < 0:
		return sntStartKey
	elif idx >= len(sentence):
		return sntEndKey
	else:
		return sentence[idx]

def savelm(data, filename):
	with open(filename, 'w') as fh:
		dump(data, fh, HIGHEST_PROTOCOL)

def loadlm(filename):
	with open(filename, 'r') as fh:
		return load(fh)
