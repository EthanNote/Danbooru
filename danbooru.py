import urllib.request as request
import urllib
import json
import sqlite3
import os
import threading
import shutil

class Danbooru:

	class Searchoption:
		class Rating:
			safe = 'rating:safe'
			questionable = 'rating:questionable'
			explicit = 'rating:explicit'
			ratings = [safe, questionable, explicit]
		class Order:
			score = 'order:score'

	def __init__(self, sitename='Konachan', baseurl='http://www.konachan.net'):
		self.db = sqlite3.connect(sitename + '.sqlite')
		try:
			self.db.execute('CREATE TABLE posts( \
								id INT PRIMARY KEY, \
								tags VARCHAR(512), \
								sample_url VARCHAR(512), \
								file_url VARCHAR(512), \
								file_size INT, \
								width INT,\
								height INT \
							)')
		except Exception as e:
			print(e)

		self._18X = True
		
		self.baseurl = baseurl
		self.sitename = sitename

	def get_post(self, tags=[], page=[1], page_limit=5):
		if(type(page) is int):
			page = [page]
		if type(tags) is list:
			tags = ' '.join(tags)
		if self._18X:
			tags +='+' + Danbooru.Searchoption.Rating.safe

		post_list = []
		for i in page:
			url = self.baseurl + '/post.json?tags=%s&page=%s&limit=%s' % (tags, i, page_limit)
			print('Request url: ' + url)
			headers = ('User-Agent','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')
			opener = urllib.request.build_opener()
			opener.addheaders = [('User-Agent','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
								('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
			response_json=data = opener.open(url).read()
			#response_json = request.urlopen(url)
			post_list += json.loads(response_json.decode())
			print('Get %d post(s)'%(len(post_list),))
			for post in post_list:
				try:
					self.db.cursor().execute('insert into posts values(%d,\'%s\',\'%s\',\'%s\',%d,%d,%d)' % (post['id'],post['tags'],post['sample_url'], post['file_url'],post['file_size'],post['width'],post['height']))
					self.db.commit()
				except:
					pass
			
		return PostList(self, post_list)

	def download(self, dir=None):
		if dir == None:
			dir = self.sitename
			
		if not os.path.exists(dir):
			os.mkdir(dir)
		def progress_bar(a,b,c):
			per = 100.0 * a * b / c  
			if per > 100:  
				per = 100  
			print('\r[ %.2f%% ]' % per, end='')

		posts = self.db.cursor().execute('select id, file_url, file_size from posts').fetchall()
		for post in posts:
			id = post[0]
			url = 'http:' + post[1]		
			size = post[2]	
			path = dir + '/' + str(id) + url[-4:]
			
			if(os.path.exists(path) and os.path.getsize(path)==size):
				continue
			try:
				print('Downloading %s from %s' % (path, url))
				request.urlretrieve(url,path,progress_bar)
				print("Done           ")
			except:
				print('Error, skip')

	def multi_download(self, dir=None, threadcount=5, postlist=None):
		if dir == None:
			dir = self.sitename

		if not os.path.exists(dir):
			os.mkdir(dir)

		threadlist = []

		def download_thread(url, path):
			if(os.path.exists(path)):
				return
			print('Downloading ' + url)
			request.urlretrieve(url, path)
			print('Done ' + path)

		if postlist == None:
			postlist = []#self.db.cursor().execute('select id, file_url, file_size from posts').fetchall()
			query_result = self.db.cursor().execute('select id, file_url, file_size from posts')
			while True:
				post = query_result.fetchone()
				if post == None:
					break
				postlist.append({'id':post[0], 'file_url':post[1]})

		for post in postlist:
			id = post['id']
			url = 'http:' + post['file_url']			
			path = dir + '/' + str(id) + url[-4:]

			if dir != self.sitename:
				basepath = self.sitename + '/' + str(id) + url[-4:]
				if os.path.exists(basepath):
					shutil.copy(basepath ,dir)
					continue

			thread = threading.Thread(target=download_thread, args=(url, path))
			threadlist.append(thread)
			thread.start()
			while len(threadlist) > threadcount:
				for t in threadlist:
					if not t.is_alive():
						t.join()
						threadlist.remove(t)

		for t in threadlist:
			t.join()

import pickle

class PostList:
	def __init__(self, danbooru, postlist=[]):
		self.danbooru = danbooru
		self.postlist = postlist

	def download(self, dir=None,threadcount=5):
		self.danbooru.multi_download(dir=dir, threadcount=threadcount, postlist=self.postlist)

	def save(self, name):
		with open(name, 'wb') as f:
			pickle.dump(self,f)
	
	@classmethod
	def load(self, name):
		with open(name, 'rb') as f:
			p=pickle.load(f)
			if type(p) is PostList:
				return p			
		return None
