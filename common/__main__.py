import os
import sys
import time
import traceback

import praw

import config
import reddit
import cloud

class Main:
	def __init__(self):
		self.version = "2.0.0-a"

		self.c = config.Config("config.json",
			{
				"id": "<IMGUR_CLIENT_ID>",
				"min": 100
			}
		)

		self.d = config.Config("database.json",
			{
				"banned": [],
				"replied": []
			}
		)

		print "> Started makeswordclouds, version " + self.version
		self.r = reddit.Reddit(self.c, self.d, praw.Reddit("makeswordclouds: running under version " + self.version))

	def legwork(self, submission, requester=None):
		prepend = ""
		text = self.r.flatten(submission)

		cloud.generate(text)
		upload = cloud.upload(self.c.get()["id"])

		if requester != None:
			prepend = "**Summoned by /u/" + requester + ".**  \n"

		content = (
			prepend +
			"Here is a word cloud of every comment in this thread, as of this time: " + upload
		)

		return self.r.comment(submission, content)

	def loop(self):
		try:
			while True:
				print "> Beginning mailbox check."

				for mail in self.r.mailbox():
					try:
						url = self.legwork(mail.submission.id, requester=mail.message.author.name)

						self.r.message(
							mail.message.author.name,
							"Your word cloud has been created.",
							"Congratulations! Your word cloud can be found here: " + url
						)
					except reddit.BannedSubredditError as e:
						try:
							raise reddit.BannedSubredditError(
								resp=reddit.ErrorResponse(self.r, mail.message.author.name),
								log=False
							)
						except:
							pass
					except Exception as e:
						self.r.message(
							mail.message.author.name,
							"A problem arose creating your word cloud.",
							"An internal error occured. I am unable to furthur explain the issue. Contact the developer if you want to know the full cause."
						)

						print "> An error occrred while creating the word cloud."

				print "> Beginning post check."

				for post in self.r.posts():
					try:
						self.legwork(post)
					except reddit.BannedSubredditError:
						pass

				print "> Sleeping."

				self.d.save()
				time.sleep(120)
		except KeyboardInterrupt:
			print "> Terminated."
			self.d.save()
		except:
			print "> An error occured. Restarting."
			traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
	Main().loop()