import json

def write(config, file):
	
	conf = json.dumps(config, indent = 4, sort_keys = True)
	
	with open(file, 'w') as w:
	
		w.write(conf)
		
def load(file):
	
	conf = json.loads(open(file).read())
	
	return conf