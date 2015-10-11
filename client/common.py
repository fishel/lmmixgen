from pickle import dump, load, HIGHEST_PROTOCOL

maxNgramSize = 3

countKey = '___'

sntStartKey = '<s>'
sntEndKey = '</s>'

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
