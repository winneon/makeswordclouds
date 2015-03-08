from imports import *

current = {

	'credentials': {
	
		'username': '',
		'password': '',
		
	},
	
	'limit': '',
	'id': '',
	'banned': '',
	
}

replied_current = {
	
	'replied': [],
	
}

config_name = 'config.json'
replied_name = 'replied.json'

def main():
	
	version = '1.3'
	
	parse = argparse.ArgumentParser(description = 'makeswordclouds')
	parse.add_argument('-l', '--login', action = 'store_true', help = 'Login to a different account than config account')
	args = parse.parse_args()
	
	print('\nMWC // version ' + version)
	print('------------------')
	
	if not os.path.isfile(config_name) or not os.path.isfile(replied_name):
		
		config.write(current, config_name)
		config.write(replied_current, replied_name)
		print('> Created config.json & replied.json. Please edit the values in the config before continuing.')
		sys.exit()
		
	conf = config.load(config_name)
	
	if conf['limit'] == '':
		
		print('> The limit in the config is not set! Please set it to a proper number.')
		sys.exit()
		
	elif int(conf['limit']) > 200:
		
		print('> The limit in the config is over 200! Please make it a lower number.')
		sys.exit()
		
	if conf['id'] == '':
		
		print('> The id in the config is not set! Please set it to an Imgur client id.')
		sys.exit()
		
	user = conf['credentials']['username']
	passwd = conf['credentials']['password']
	
	current['credentials']['username'] = user
	current['credentials']['password'] = passwd
	current['limit'] = conf['limit']
	current['id'] = conf['id']
	
	if args.login or user == '' or passwd == '':
		
		user = raw_input('> Reddit username: ')
		passwd = getpass.getpass('> %s\'s password: ' % user)
		
		print
		
	agent = (
		'/u/' + user + ' running makeswordclouds, version ' + version + ', created by /u/WinneonSword.'
	)
	
	r = praw.Reddit(user_agent = agent)
	u = utils.Utils(conf, r, config_name, replied_name, current, replied_current)
	
	reddit.login(user, passwd, r)
	loop(user, r, u)
	
def loop(user, reddit, utils):
	
	print('\n> Booting up makeswordclouds.')
	print('> To stop the bot, press Ctrl + C.')
	
	try:
		
		while True:
			
			inbox = None
			inbox = reddit.get_unread(limit = None)
			
			print('\n> Checking mailbox for messages...')
			
			for message in inbox:

				if '+create ' in message.body:
					
					print('\n> Found potentially valid request.')

					try:

						url = message.body.replace('+create ', '')
						submission = reddit.get_submission(url = url)
						sub = submission.subreddit.display_name.lower()

					except:

						submission = None

					if submission == None:

						print('> The request is not valid!')
						message.reply(
							'I am deeply sorry, but the link you provided is not a valid link!  ' + utils.get_footer()
						)

					elif submission.id in utils.replied:

						print('> A word cloud has already been made for that post!')
						message.reply(
							'I am deeply sorry, but the submission you have requested, located [here](' + submission.permalink + '), already has a word cloud comment created in it!  ' + utils.get_footer()
						)

					elif sub in utils.banned:

						print('> The subreddit the submission is located in is located in the banned list!')
						message.reply(
							'I am deeply sorry, but the submission you have requested, located [here](' + submission.permalink + '), is in a subreddit currently in our blacklist.  ' + utils.get_footer()
						)

					else:

						try:

							print('> Submission is fully valid. Creating word cloud...')
							utils.create_comment(submission, author = message.author.name)

							print('\n> Word cloud posted!')
							message.reply(
								'Congratulations! The word cloud has been created! Thank you for using makeswordclouds services.  ' + utils.get_footer()
							)

						except:

							print('> An error occured creating the word cloud.')
							message.reply(
								'An error occurred creating the requested word cloud. If the permalink you provided does not have any comments, then this is most likely the issue.  ' + utils.get_footer()
							)
							
					message.mark_as_read()

			print('\n> Checking submissions for valid entries...')
			submissions = reddit.get_subreddit('all').get_hot(limit = 100)
			
			for submission in submissions:
				
				sub = submission.subreddit.display_name.lower()
				
				if submission.id not in utils.replied and submission.num_comments >= int(utils.config['limit']) and sub not in utils.banned:
					
					print('\n> Found valid submission in the subreddit /r/' + submission.subreddit.display_name + '!')
					utils.create_comment(submission)
					
			print('\n> Sleeping for 2 minutes.')
			time.sleep(120)
			
	except KeyboardInterrupt:
		
		print('> Stopped makeswordclouds. Thank you for running this bot!')
		
	except:
		
		print('\n> An error has occured. Restarting the bot.')
		traceback.print_exc(file = sys.stdout)
		loop(user, reddit, utils)
			
if __name__ == '__main__':
	
	main()
	
