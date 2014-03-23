import sys

def login(user, passwd, reddit):
	
	try:
		
		reddit.login(user, passwd)
		print('> Logged in as ' + user)
		
	except:
		
		print('> Failed to connect to Reddit. Check your credentials.')
		sys.exit()