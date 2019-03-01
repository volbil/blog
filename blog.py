#!/usr/bin/env python3

import json
import mistune
import hashlib
from datetime import datetime
from os.path import isfile, isdir, join
from os import listdir
from yaml import load_all as yaml_header
import shutil
import re
import os

class Core():
	def __init__(self):
		self.know = []
		self.force_rebuild = True
		self.known_file = 'known.json'
		self.path = {
			'website': 'website',
			'pagination': 'pagination',
			'pages': 'pages'
		}

		if isfile(self.known_file) is True:
			try:
				self.know = json.loads(Misc().open(self.known_file))
			except Exception:
				print('Known file empty')

	def build(self, text, check):
		data = {}
		raw_header = re.findall(r'^---[\s\S]+?---', text, re.DOTALL)
		if len(raw_header) > 0:
			text = re.sub(raw_header[0] + '\n' * 2, '', text)
			data = next(yaml_header(raw_header[0]))
			data['content'] = mistune.markdown(text)
			data['checksum'] = check

		return data

	def pages(self):
		path = self.path['pages']
		raw_pages = [d for d in [f for f in listdir(path) if isfile(join(path, f))] if d[-3:] == '.md']
		new_know = {}

		result = []
		for raw_page in raw_pages:
			check = Misc().checksum(path + '/' + raw_page)
			page_data = {}

			if check not in self.know or self.force_rebuild is True:
				text = Misc().open(path + '/' + raw_page)
				page_data = self.build(text, check)
				page_data['slug'] = raw_page[:-3]
				result.append(page_data)
			else:
				page_data['timestamp'] = self.know[check][0]
				page_data['slug'] = self.know[check][1]
				page_data['title'] = self.know[check][2]
			
			if not page_data['title'].isdigit():
				new_know[check] = [page_data['timestamp'], page_data['slug'], page_data['title']]

		Misc().save(self.known_file, json.dumps(new_know))

		return [page for page in result if len(page) > 0]

class Layouts():
	def __init__(self):
		self.conf = {
			'dir': 'layouts',
			'content': 'content.html',
			'page': 'page.html',
			'head': 'head.html',
			'preview': 'preview.html',
			'pagination': 'pagination.html',
			'header': 'header.html'
		}

	def content(self, head, content):
		layout = Misc().open('{}/{}'.format(self.conf['dir'], self.conf['content']))
		layout = re.sub(r'{{ HEAD }}', head, layout)
		layout = re.sub(r'{{ CONTENT }}', content, layout)
		return layout

	def page(self, date, author, checksum, content, title):
		layout = Misc().open('{}/{}'.format(self.conf['dir'], self.conf['page']))
		layout = re.sub(r'{{ DATE }}', date, layout)
		layout = re.sub(r'{{ AUTHOR }}', author, layout)
		layout = re.sub(r'{{ CHECKSUM }}', checksum, layout)
		layout = re.sub(r'{{ CONTENT }}', content, layout)
		layout = re.sub(r'{{ TITLE }}', title, layout)
		return layout

	def head(self, title, description='Опис - заглушка'):
		layout = Misc().open('{}/{}'.format(self.conf['dir'], self.conf['head']))
		layout = re.sub(r'{{ TITLE }}', title, layout)
		layout = re.sub(r'{{ DESCRIPTION }}', description, layout)
		return layout

	def preview(self, timestamp, link, title):
		layout = Misc().open('{}/{}'.format(self.conf['dir'], self.conf['preview']))
		layout = re.sub(r'{{ DATE }}', Misc().date(timestamp), layout)
		layout = re.sub(r'{{ LINK }}', link, layout)
		layout = re.sub(r'{{ TITLE }}', title, layout)
		return layout

	def header(self):
		layout = Misc().open('{}/{}'.format(self.conf['dir'], self.conf['header']))
		return layout

	def pagination(self, current, total):
		if total > 1:
			layout = Misc().open('{}/{}'.format(self.conf['dir'], self.conf['pagination']))
			pagination = '<a href="/" class="{}">1</a>'.format(('disabled' if 0 == current else ''))
			for page in range(1, total):
				link = '/pagination/' + str(page + 1)
				disabled = 'disabled' if page == current else ''
				pagination += '<a href="{}" class="{}">{}</a>'.format(link, disabled, str(page + 1))

			layout = re.sub(r'{{ PAGINATION }}', pagination, layout)
			return layout
		else:
			return ''

class Misc():
	def sha256(self, data, size=12):
		return hashlib.sha256(data).hexdigest()[:size]

	def checksum(self, filename):
		with open(filename, "rb") as file:
			return self.sha256(file.read())

	def date(self, timestamp, full=False):
		template = '%d %B %Y, %H:%M:%S' if full else '%d %b %Y'
		return datetime.fromtimestamp(timestamp).strftime(template)

	def save(self, filename, content):
		with open(filename, 'w+') as file:
			file.write(content)

	def open(self, filename):
		with open(filename, 'r') as content:
			return content.read()

	def dir(self, directory):
		if not os.path.exists(directory):
			os.makedirs(directory)

	def sort(self, pages, chunks=10):
		pages_raw = [[pages[k][0], pages[k][1], pages[k][2]] for k in pages]
		pages_sorted = sorted(pages_raw, key=lambda e: e[0], reverse=True)
		return [pages_sorted[i:i + chunks] for i in range(0, len(pages_sorted), chunks)]

	def rm(self, path):
		try:
			shutil.rmtree(path)
		except Exception:
			pass

def generate():
	core = Core()
	layouts = Layouts()
	misc = Misc()

	pages_dir = '{}/{}/'.format(core.path['website'], core.path['pages'])
	misc.dir(pages_dir)

	pages = core.pages()
	know = json.loads(Misc().open(core.known_file))
	slugs = [know[k][1] for k in know]

	for page in pages:
		l_head = layouts.head(page['title'], page['description'])
		l_page = layouts.page(misc.date(page['timestamp']), page['author'], page['checksum'], page['content'], page['title'])
		l_content = layouts.content(l_head, l_page)
		l_path = '{}/{}/'.format(pages_dir, page['slug'])
		
		misc.dir(l_path)
		misc.save('{}/index.html'.format(l_path), l_content)

	existing = [d for d in [f for f in listdir(pages_dir) if isdir('{}/{}'.format(pages_dir, f))]]
	for page in existing:
		if page not in slugs:
			misc.rm('{}/{}'.format(pages_dir, page))

	previews = misc.sort(know)
	misc.rm('{}/{}/'.format(core.path['website'], core.path['pagination']))
	for index, page in enumerate(previews):
		title = 'Головна сторінка' if index == 0 else 'Сторінка {}'.format(index)
		path = core.path['website'] + '/' if index == 0 else '{}/{}/{}/'.format(core.path['website'], core.path['pagination'], index + 1)
		l_head = layouts.head(title)
		l_previews = layouts.header()

		for preview in page:
			l_previews += layouts.preview(preview[0], '/' + core.path['pages'] + '/' + preview[1], preview[2])

		misc.dir(path)
		l_previews += layouts.pagination(index, len(previews))
		l_content = layouts.content(l_head, l_previews)
		misc.save(path + 'index.html', l_content)

generate()
