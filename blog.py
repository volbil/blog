import json
import markdown
import hashlib
from datetime import datetime
from locale import *
import os

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
            
    return hash_md5.hexdigest()

def generate():
	setlocale(LC_ALL, "uk_UA")
	resultDir = "website"
	templatesDir = "templates"
	preview = ""

	print("Reading posts")

	with open("posts.json", "r") as postsData:
		postsList = json.loads(postsData.read())

	print("Reading templates")
	with open("{}/head.html".format(templatesDir), "r") as content:
		headTemplate = content.read()

	with open("{}/love.html".format(templatesDir), "r") as content:
		love = content.read()

	with open("{}/post.html".format(templatesDir), "r") as content:
		postTemplate = content.read().replace("!HEAD!", headTemplate).replace("!LOVE!", love)

	with open("{}/home.html".format(templatesDir), "r") as content:
		homeTemplate = content.read().replace("!HEAD!", headTemplate).replace("!LOVE!", love)

	print("Generating posts")
	for post in postsList["posts"]:
		postTitle = post["title"]
		postDescription = post["description"]
		postDate = post["date"]
		postPath = post["template"]
		postPathWeb = "{}/{}".format(resultDir, postPath)

		if not os.path.exists(postPathWeb):
			os.makedirs(postPathWeb)

		postChecksum = md5("{}/page.md".format(postPath))

		with open("{}/page.md".format(postPath), "r") as content:
			markdownText = content.read()

		postTemplate = postTemplate.replace("!TITLE!", postTitle)
		postTemplate = postTemplate.replace("!DESCRIPTION!", postDescription)
		postTemplate = postTemplate.replace("!DATE!", datetime.fromtimestamp(postDate).strftime('%d %B %Y, %H:%M:%S'))
		postTemplate = postTemplate.replace("!CONTENT!", markdown.markdown(markdownText))
		postTemplate = postTemplate.replace("!CHECKSUM!", postChecksum[:8])

		file = open("{}/index.html".format(postPathWeb), "w")
		file.write(postTemplate)
		file.close()

		with open("{}/preview.html".format(templatesDir), "r") as content:
			postPreview = content.read()

		postPreview = postPreview.replace("!TITLE!", postTitle)
		postPreview = postPreview.replace("!DESCRIPTION!", postDescription)
		postPreview = postPreview.replace("!LINK!", postPath)

		preview += postPreview

	print("Generating posts list")
	file = open("{}/index.html".format(resultDir), "w")
	file.write(homeTemplate.replace("!POSTS!", preview).replace("!TITLE!", "Список постів"))
	file.close()

	print("Done")

generate()
