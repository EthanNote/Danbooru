import urllib.request as request
import urllib
import json
import sqlite3
import os
import threading
import shutil

def webread(url, readtimeout=10):
	"""read page"""
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
                                    ('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
    return opener.open(url,None, readtimeout).read()

def trywebread(url, timeout, retrytimes=3):
	"""read page, retry if failed"""
    data=None
    retrycount=0
    while retrycount<=retrytimes:
        try:
            if(retrycount>0): 
                print('Retry %d'%(retrycount))
            data=webread(url, timeout)
            return data
        except Exception as e:
            print('Exception while loading %s, %s'%(url, e))
            retrycount+=1


class Danbooru:

	class Searchoption:
		"""search options, use as tags"""
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
								score INT, \
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
		"""send a post request to danbooru site, post data in json format"""
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
			
			response_json=None
			retrycount=0
			while retrycount<5:
				try:
					response_json=webread(url).decode() 
					break
				except Exception as e:
					retrycount+=1
					print('%s. retry %d'%(e, retrycount))
			if(response_json==None):
				print('Failed, maxmium retry times reached')

			response_list= json.loads(response_json)
			post_list += response_list
			insert=0
			ex={}
			for post in response_list:
				try:
					self.db.cursor().execute('insert into posts values(?,?,?,?,?,?,?,?)', 
							(post['id'],post['tags'],post['score'], post['sample_url'], post['file_url'],post['file_size'],post['width'],post['height']))
					self.db.commit()
					insert+=1
				except Exception as e:
					if str(e) not in ex.keys():
						ex[str(e)]=1
					else:
						ex[str(e)]+=1			
			print('%d out of %d posts added to database, %d insertion failure'%(insert,len(response_list), len(response_list)-insert))
			if len(ex)>0:
				print('Failures:')
				for i in ex.keys():
					print('  [ %d ] %s'%(ex[i], i))
			
		return PostList(self, post_list)


	def create_postlist(self, **kwargs):
		"""search local database, create a list for download"""
		table=None
		if('order' in kwargs.keys()):
			if(kwargs['order']=='score'):
				table= self.db.cursor().execute('SELECT id, file_url, file_size FROM posts ORDER BY score DESC').fetchall()
			elif(kwargs['order']=='id'):
				table= self.db.cursor().execute('SELECT id, file_url, file_size FROM posts ORDER BY id').fetchall()
		else:
			table= self.db.cursor().execute('select id, file_url, file_size from posts').fetchall()
		postlist=[]
		for row in table:
			postlist.append({'id':row[0], 'file_url':row[1]})
		return postlist


	def split_download(self, dir, postlist, splitsize,threadcount=5):
		"""split images into defferent directories"""
		for i in range(int(len(postlist)/splitsize)+1):
			sublist=postlist[i*splitsize:(i+1)*splitsize]
			subdir=dir+'/'+str(i+1)
			self.download(subdir, threadcount, sublist)

	def download(self, dir, threadcount, postlist):
		"""multi-thread download"""
		if dir == None:
			dir = self.sitename

		if not os.path.exists(dir):
			os.makedirs(dir)

		threadlist = []
		tasklist=[]		

		if(postlist==None):
			postlist=self.create_postlist()

		def download_thread(url, path, tasklist):
			if(os.path.exists(path)):
				return
			print('Downloading ' + url)
			tasklist.append(path)

			image=trywebread(url, 60)
			if(image!=None):
				with open(path,'wb') as f:
					f.write(image)
					print('Done ' + path)
			else:
				print('Failed ' + path)
			tasklist.remove(path)
			print('Remaining tasks: '+str(tasklist))		
		
		print('%d posts to download'%(len(postlist), ))

		for post in postlist:
			id = post['id']
			url = post['file_url']			
			if(url[0:4] != 'http'):
				url='http:'+url

			path = dir + '/' + str(id) + url[-4:]

			if dir != self.sitename:
				basepath = self.sitename + '/' + str(id) + url[-4:]
				if os.path.exists(basepath):
					shutil.copy(basepath ,dir)
					continue

			thread = threading.Thread(target=download_thread, args=(url, path, tasklist))
			threadlist.append(thread)
			thread.start()
			while len(threadlist) >= threadcount:
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
		self.danbooru.download(dir=dir, threadcount=threadcount, postlist=self.postlist)

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

