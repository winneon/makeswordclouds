import os
import random

import numpy
import pyimgur

from PIL import Image
from wordcloud import WordCloud, ImageColorGenerator

"""

mask = numpy.array(Image.open(path.join(path.dirname(path.dirname(__file__)), "resources") + "/earth.png"))
cloud = WordCloud(font_path=path.join(path.dirname(path.dirname(__file__)), "resources") + "/fonts/quartzo.ttf", background_color="#1A1A1A", mask=mask, scale=2, max_words=None, relative_scaling=0.5, prefer_horizontal=1.0)

cloud.generate(r.flatten("4d1yv4"))

image_colors = ImageColorGenerator(mask)
cloud.recolor(color_func=image_colors)

cloud.to_file("cloud.png")

"""

def generate(text):
	resources = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources")
	masks = os.path.join(resources, "masks")
	fonts = os.path.join(resources, "fonts")

	mask = numpy.array(Image.open(os.path.join(masks, random.choice(os.listdir(masks)))))

	cloud = WordCloud(
		font_path=os.path.join(fonts, random.choice(os.listdir(fonts))),
		background_color="#1A1A1A",
		mask=mask,
		scale=2,
		max_words=None,
		relative_scaling=0.5,
		prefer_horizontal=1.0
	)

	cloud.generate(text)

	image_colors = ImageColorGenerator(mask)
	cloud.recolor(color_func=image_colors)

	cloud.to_file("cloud.png")

def upload(client):
	imgur = pyimgur.Imgur(client)
	upload = imgur.upload_image("cloud.png")
	os.remove("cloud.png")

	return upload.link