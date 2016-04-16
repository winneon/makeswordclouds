import sys
import re
import traceback

import praw

class ErrorResponse:
	def __init__(self, reddit, recipient):
		self.reddit = reddit
		self.recipient = recipient

class MakesWordCloudsErrorDummy(Exception):
	def __init__(self, resp, message, log):
		Exception.__init__(self, message)

		if resp == None:
			self.makeswordclouds_cont = True
		else:
			resp.reddit.message(
				resp.recipient,
				"A problem arose creating your word cloud.",
				message
			)

		if log:
			print "> " + message

class InvalidPermalinkError(MakesWordCloudsErrorDummy):
	def __init__(self, resp=None, message="The permalink is invalid.", log=True):
		MakesWordCloudsErrorDummy.__init__(self, resp, message, log)

class PreexistingCloudError(MakesWordCloudsErrorDummy):
	def __init__(self, resp=None, message="The permalink already has a word cloud in its comments.", log=True):
		MakesWordCloudsErrorDummy.__init__(self, resp, message, log)

class BannedSubredditError(MakesWordCloudsErrorDummy):
	def __init__(self, resp=None, message="The subreddit is on the blacklist.", log=True):
		MakesWordCloudsErrorDummy.__init__(self, resp, message, log)

class ValidMail:
	def __init__(self, submission, message):
		self.submission = submission
		self.message = message

class Reddit:
	def __init__(self, config, database, reddit):
		self.config = config
		self.database = database

		self.reddit = reddit
		self.reddit.refresh_access_information()

		self.footer = (
			"---\n\n"
			"[^[source ^code]](https://github.com/Winneon/makeswordclouds) "
			"[^[contact ^developer]](https://reddit.com/user/WinneonSword) "
			"[^[request ^word ^cloud]](https://www.reddit.com/message/compose/?to=makeswordcloudsagain&subject=Requesting%20word%20cloud.&message=%2Bcreate%20REPLACE_THIS_WITH_A_REDDIT_POST_PERMALINK)"
		)

		print "> Authenticated as /u/" + self.reddit.get_me().name

	def _format_comment(self, text):
		return text + "\n\n" + self.footer

	def flatten(self, submission):
		submission = self.reddit.get_submission(submission_id=submission, comment_limit=None)
		flattened = praw.helpers.flatten_tree(submission.comments)
		text_mass = ""

		for comment in flattened:
			if isinstance(comment, praw.objects.Comment):
				# i hate these 3 lines of code but i'm too lazy to redo them
				body = re.sub(r"https?://(?:www\.)?[A-z0-9-]+\.[A-z\.]+[\?A-z0-9&=/]*", "", comment.body, flags=re.IGNORECASE)
				body = re.sub(r"<.*?>|&.*?;|/.+?(?= )|/.*", "", body)
				text_mass = text_mass + body + "\n"

		return text_mass

	def mailbox(self):
		collected = []

		for message in self.reddit.get_unread(limit=None):
			if "+create " in message.body:
				submission = None

				try:
					permalink = message.body.replace("+create ", "")

					if "redd.it" in permalink:
						short = permalink.replace("http://redd.it/", "").replace("https://redd.it/", "")
						submission = self.reddit.get_submission(submission_id=short)
					else:
						submission = self.reddit.get_submission(url=permalink)
				except:
					pass

				try:
					if submission == None:
						raise InvalidPermalinkError(resp=ErrorResponse(self, message.author.name))
					elif submission.id in self.database.get()["replied"]:
						raise PreexistingCloudError(resp=ErrorResponse(self, message.author.name))
					elif submission.subreddit.display_name.lower() in self.database.get()["banned"]:
						raise BannedSubredditError(resp=ErrorResponse(self, message.author.name))
					else:
						collected.append(ValidMail(submission, message))
				except MakesWordCloudsErrorDummy:
					pass

			message.mark_as_read()

		return collected

	def posts(self):
		collected = []

		for post in self.reddit.get_subreddit("all").get_hot(limit=200):
			subreddit = post.subreddit.display_name
			limit = int(self.config.get()["min"])

			banned = self.database.get()["banned"]
			replied = self.database.get()["replied"]

			if subreddit.lower() not in banned and post.id not in replied and post.num_comments >= limit:
				collected.append(post.id)

		return collected

	def comment(self, submission, message):
		submission = self.reddit.get_submission(submission_id=submission)

		try:
			url = submission.add_comment(self._format_comment(message)).permalink
			self.database.get()["replied"].append(submission.id)

			print "> Comment posted. "
			print "> " + url

			return url
		except praw.errors.Forbidden as e:
			subreddit = submission.subreddit.display_name.lower()
			banned = self.database.get()["banned"]

			if subreddit not in banned:
				banned.append(subreddit)
				raise BannedSubredditError()
		except:
			print "> Failed to post comment."

			self.database.get()["replied"].append(submission.id)
			traceback.print_exc(file=sys.stdout)

	def message(self, recipient, subject, message):
		self.reddit.send_message(recipient, subject, self._format_comment(message))