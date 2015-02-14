from imports import *

# Other imports
from requests import HTTPError
from wordcloud import WordCloud

class Utils:
	
	def __init__(self, conf, reddit, config_name, replied_name, current, replied_current):
		
		self.out = 'cloud.png'
		self.config = conf
		self.reddit = reddit
		self.banned = set(conf['banned'])

		self.start = 0
		
		self.config_file = config_name
		self.replied_file = replied_name

		self.current = current
		self.replied_current = replied_current
		
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
				
				body = re.sub(r'https?://(?:www\.)?[A-z0-9-]+\.[A-z\.]+[\?A-z0-9&=/]*', '', comment.body, flags = re.IGNORECASE)
				body = re.sub(r'<.*?>|&.*?;|/.+?(?= )|/.*', '', body)
				text += body + '\n'
				
		return text
		
	def make_cloud(self, text):
		
		self.start = random.randint(0, 255)
		cloud = WordCloud(font_path = 'bot/fonts/' + random.choice(os.listdir('bot/fonts/')), background_color = 'black', width = 1280, height = 720, scale = 1, color_func = self.light_colour_func)
		cloud.generate(text)
		cloud.to_file(self.out)
		
		return self.out
		
	def upload_image(self, file):
		
		imgur = pyimgur.Imgur(self.config['id'])
		upload = imgur.upload_image(file)
		
		return upload.link
		
	def add_replied_submission(self, id):
		
		self.replied.add(id)
		self.replied_current['replied'] = list(self.replied)
		
		config.write(self.replied_current, self.replied_file)
		
	def add_banned_subreddit(self, subreddit):
		
		if subreddit not in self.banned:
			
			self.banned.add(subreddit)
			self.current['banned'] = list(self.banned)
			
			config.write(self.current, self.config_file)
			
	def create_comment(self, submission, author = None):

		reply = ''

		if author is not None:

			reply += 'This bot has been summoned to this post as per the request of /u/' + author + '.  \n'
		
		text = self.get_submission_comments(submission.id)
		cloud = self.make_cloud(text)
		upload = self.upload_image(cloud)
		
		print('> Successfully made word cloud and uploaded to imgur!')
		os.remove(cloud)
		
		try:
			
			reply += 'Here is a word cloud of all of the comments in this thread: ' + upload + '  ' + self.get_footer()
			self.handle_rate_limit(submission, reply)
			
			print('> Comment posted! Link: ' + upload)
			
		except HTTPError as e:
			
			print('\n> An HTTP error occured trying to post the comment.')
			print('> Response: %s' % e.response)
			
			if '403' in str(e.response):
				
				sub = submission.subreddit.display_name.lower()
				
				self.add_banned_subreddit(sub)
				print('> Added the subreddit %s to the banned list!' % sub)
				
		except:
			
			print('> Failed to post comment.')
			traceback.print_exc(file = sys.stdout)
			
		self.add_replied_submission(submission.id)

	def get_footer(self):
		return '\n[^source ^code](http://github.com/Winneon/makeswordclouds) ^| [^contact ^developer](http://reddit.com/user/WinneonSword) ^| [^faq](https://github.com/Winneon/makeswordclouds#faq)'

	def light_colour_func(self, word, font_size, position, oreientation, random_state):
		return 'hsl(%s, %s%%, %s%%)' % (self.start + random.randint(0, 75), random.randint(50, 80), random.randint(50, 100))