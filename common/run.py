import sys, os, re, time, argparse, getpass, praw, requests, reddit, config, wordcloud, pyimgur, json, traceback
from requests import HTTPError

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

def bootup():
	
	version = "1.1"
	
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
	
	if args.login or user == "" or passwd == "":
		
		user = raw_input('> Reddit username: ')
		passwd = getpass.getpass("> %s's password: " % user)
		
		print
		
	agent = (
		'/u/' + user + ' running makeswordclouds, version ' + version + ', created by /u/WinneonSword.'
	)
	
	r = praw.Reddit(user_agent = agent)
	utils = Utils(conf, r)
	
	reddit.login(user, passwd, r)
	loop(user, r, utils)
	
def loop(user, reddit, utils):
	
	print('\n> Booting up makeswordclouds. You will be notified when makeswordclouds detects a broken link.')
	print('> To stop the bot, press Ctrl + C.')
	
	try:
		
		while True:
			
			print('\n> Checking submissions for valid entries...')
			submissions = reddit.get_subreddit('all').get_hot(limit = 100)
			
			for submission in submissions:
				
				sub = submission.subreddit.display_name.lower()
				
				if submission.id not in utils.replied and submission.num_comments >= int(utils.config['limit']) and sub not in utils.banned:
					
					print('\n> Found valid submission in the subreddit /r/' + submission.subreddit.display_name + '!')
					
					text = utils.get_submission_comments(submission.id)
					cloud = utils.make_cloud(text)
					upload = utils.upload_image(cloud)
					
					print('> Successfully made word cloud and uploaded to imgur!')
					os.remove(cloud)
					
					try:
						
						reply = (
							'Here is a word cloud of all of the comments in this thread: ' + upload + '\n\n'
							'*****\n'
							'[^source ^code](https://github.com/WinneonSword/makeswordclouds) ^| [^contact ^developer](http://reddit.com/user/WinneonSword)'
						)
						utils.handle_rate_limit(submission, reply)
						
						print('> Comment posted! Link: ' + upload)
						
					except HTTPError, e:
						
						print('\n> An HTTP error occured trying to post the comment.')
						print('> Response: %s' % e.response)
						
						if "403" in str(e.response):
							
							utils.add_banned_subreddit(sub)
							print('> Added the subreddit %s to the banned list!' % sub)
							
					except:
						
						print('> Failed to post comment.')
						traceback.print_exc(file = sys.stdout)
						
					utils.add_replied_submission(submission.id)
					
			print('\n> Sleeping.')
			time.sleep(15)
			
	except KeyboardInterrupt:
		
		print('> Stopped makeswordclouds. Thank you for running this bot!')
		
	except:
		
		print('\n> An error has occured. Restarting the bot.')
		traceback.print_exc(file = sys.stdout)
		loop(user, reddit, utils)
		
class Utils:
	
	def __init__(self, conf, reddit):
		
		self.out = 'cloud.png'
		self.config = conf
		self.reddit = reddit
		self.banned = set(conf['banned'])
		
		current = list(self.banned)
		
		self.config_file = config_name
		self.replied_file = replied_name
		
		resp = []
		
		if os.path.exists(self.replied_file):
		
			temp = config.load(self.replied_file)
			resp = temp['replied']
			
		self.replied = set(resp)
		
	def handle_rate_limit(self, submission, reply):
		
		while True:
			
			try:
				
				submission.add_comment(reply)
				break
				
			except praw.errors.RateLimitExceeded as error:
				
				print('> Rate limit exceeded! Sleeping for %s seconds...' % error.sleep_time)
				time.sleep(error.sleep_time)
				
	def get_submission_comments(self, id):
		
		submission = self.reddit.get_submission(submission_id = id, comment_limit = None)
		comments = praw.helpers.flatten_tree(submission.comments)
		text = ''
		
		for comment in comments:
			
			if isinstance(comment, praw.objects.Comment):
				
				body = re.sub(r'https?://(?:www\.)?[A-z0-9-]+\.[A-z\.]+[\?A-z0-9&=/]*', '', comment.body, flags=re.IGNORECASE)
				body = re.sub(r'&|<|>', '', body)
				text += body + '\n'
				
		return text
		
	def make_cloud(self, text):
		
		words = wordcloud.process_text(text)
		elements = wordcloud.fit_words(words, width = 400, height = 400)
		wordcloud.draw(elements, self.out, width = 400, height = 400, scale = 2)
		
		return self.out
		
	def upload_image(self, file):
		
		imgur = pyimgur.Imgur(self.config['id'])
		upload = imgur.upload_image(file)
		
		return upload.link
		
	def add_replied_submission(self, id):
		
		self.replied.add(id)
		replied_current['replied'] = list(self.replied)
		
		config.write(replied_current, self.replied_file)
		
	def add_banned_subreddit(self, subreddit):
		
		if subreddit not in self.banned:
			
			self.banned.add(subreddit)
			current['banned'] = list(self.banned)
			
			config.write(current, self.config_file)
			
if __name__ == '__main__':
	
	bootup()
	