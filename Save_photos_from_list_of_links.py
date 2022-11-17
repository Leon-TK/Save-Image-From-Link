from typing import NamedTuple
import enum
from abc import ABC, abstractmethod
import requests
import time
import random

class IDataSaverFromUrls(ABC):

	@abstractmethod
	def doJob():
		pass

class ImageSaverFromUrls(IDataSaverFromUrls):

	def __init__(self, rootPath:str, urlsFilePath: str, cachePath:str, errorLinksPath: str ):
		self.urlCount: int = 0
		self.rootPath: str = rootPath
		self.urlsFilePath: str = urlsFilePath
		self.cacheFilePath: str = cachePath
		self.errorLinksFilePath: str = errorLinksPath
		self.errorLinksList = []
		self.cacheList: list = []
		self.urlsList: list = []
		self.bContentError = False
		self.bSetTimer = True

	def loadUrlsFile(self):

		# open file and read by lines
		urlsFile = open(self.urlsFilePath)
		self.urlsList = urlsFile.readlines()

		#delete chars
		self.urlsList =self.deleteCharsFromList(self.urlsList, "\r\n")

		print("LOG. Urls loaded: ", len(self.urlsList))
		urlsFile.close()

	def loadCacheFile(self):

		# open file and read by lines
		cacheFile = open(self.cacheFilePath)
		self.cacheList = cacheFile.readlines()

		#delete invalid chars
		self.cacheList =self.deleteCharsFromList(self.cacheList, "\r\n")

		print("LOG. Cache loaded: ", len(self.cacheList))
		cacheFile.close()

	def deleteCharsFromList(self, ls: list, chars: str) -> list:
		for i in range (0, len( ls ) - 1):
			ls[i] = self.deleteChars(ls[i], chars)
		return ls

	def addErrorLink(self, url: str):
		self.errorLinksList.append(url)

	def saveErrorLinks(self):
		file = open(self.errorLinksFilePath, "w")
		for element in self.errorLinksList:
			file.write(element + '\r')

	def isUrlInCache(self, url: str) -> bool:
		if url in self.cacheList:
			print("DB. Url is in the cache!")
			return True
		else:
			print("DB. Url isnt in the cache!")
			return False

	def addUrlToCache(self, url: str):
		if (self.isUrlInCache(url)):
			return
		else:
			self.cacheList.append(url)

	def deleteChars(self, s: str, chars: str) ->str:
		for char in chars:
				s = s.replace(char, '')
		#print("DB. del chars name: ", s)
		return s

	def saveCache(self):
		print("LOG. Saving cache")
		cacheFile = open(self.cacheFilePath, 'w')

		for element in self.cacheList:
			cacheFile.write(element + '\r')

		cacheFile.close()

	def shuffleUrlList(self):
		random.shuffle(self.urlsList)

	def doJob(self):
		#prepare files and lists

		print("LOG. Pre job")
		self.loadUrlsFile()
		self.loadCacheFile()
		self.handleDuplicats()
		self.shuffleUrlList()

		print("LOG. Begin loop")

		#begin loop over urls
		for url in self.urlsList:
			print('\r')
			url = self.deleteChars(url, "\r\n")

			if len(url) < 2:
				print("WARNING. Url is too short! ", url)
				continue
			print("LOG. Current url: ", url, "\r")

			if self.isUrlInCache(url):
				continue
			#do request and write on disk
			self.saveDataFromUrl(url)

			#on disk
			if ((self.urlCount % 10) ==0):
				self.saveCache()

			print("LOG. ", self.urlCount, "/", len(self.urlsList))

			#sleep for API tickets
			if self.bSetTimer:
				time.sleep(random.randint(0, 3))
			

		#save cache after loop
		self.saveCache()
		self.saveErrorLinks()

	def getFileExtention(self, url) -> str:

		extentionIndex = url.rfind('.')

		extention = url[extentionIndex:]

		print("LOG. Extention: ", (extention + '\r'))
		return extention

	def saveDataFromUrl(self, url: str):

		try:
			if self.is_downloadable(url):

				try:
					extention = self.getFileExtention(url)
					response = requests.get(url)

				except requests.exceptions.ConnectionError:
					print("WARNING. requests.get() request refused!")
					self.addErrorLink(url)
					self.urlCount +=1
					return

    			#name generation
				if self.bContentError:
					file = open(self.rootPath + "noHeaderImage@" + self.getImageName(url) + str(self.urlCount) + extention, "wb")
				else:
					file = open(self.rootPath + "image@" + self.getImageName(url) + str(self.urlCount) + extention, "wb")
				self.bContentError = False

				file.write(response.content)

				self.addUrlToCache(url)
				self.urlCount +=1

		except requests.exceptions.ConnectionError:
			print("WARNING. is_downloadable() request refused!")
			self.addErrorLink(url)
			self.urlCount +=1
			return

		print("WARNING. is_downloadable() is false!")
		self.addErrorLink(url)
		self.urlCount +=1

	def is_downloadable(self, url) -> bool:

		#try to handle content type of responce
		h = requests.head(url, allow_redirects=True)
		header = h.headers
		content_type = header.get('content-type')

		if(content_type != None):
			if 'text' in content_type.lower():
				return False
			if 'html' in content_type.lower():
				return False
			return True
		print("WARNING. Header does not contain \'content-type\'")
		self.bContentError = True
		return True

	def handleDuplicats(self):
		tr = self.getSetWithoutDupl(self.urlsList)
		print("LOG. urlsList has been truncted from ", len(self.urlsList), " to ", len(tr))
		self.urlsList =  tr

	def getSetWithoutDupl(self, listOfElems):
		listOfElems = list(dict.fromkeys(listOfElems))
		return listOfElems

	def getImageName(self, url: str) -> str:
		extentionIndex = url.rfind('.')
		#print("DB ext ind: ", extentionIndex)
		slashIndex = url.rfind('/', len(url) - extentionIndex)
		#print("DB sl ind: ", slashIndex)
		name = url[slashIndex + 1:extentionIndex]
		name = self.checkName(name)
		print("LOG. Image name: ", name)
		return name

	def checkName(self, name: str) ->str :
		disallowed_characters = "._!?$%^&*\\<>=-+`"
		name = self.deleteChars(name, disallowed_characters)

		if len(name) < 1:
			print("WARNING. image name is too short!")
		if len(name) >=60:
			print("WARNING. image name is too long! Will be truncuated")
			name = name[:60]
		

		#print("DB. checked name: ", name)

		return name


if __name__ == '__main__':
	cacheFileName = "cache.txt"
	parsedUrlsFileName = "parsed.txt"
	errorLonksFileName = "errorLinks.txt"
	rootPath = 'E:\\Images\\'
	urlsPath = rootPath + parsedUrlsFileName
	cacheFilePath = rootPath + cacheFileName
	errorLinksFilePath = rootPath + errorLonksFileName

	
	Saver: IDataSaverFromUrls = ImageSaverFromUrls(rootPath, urlsPath, cacheFilePath, errorLinksFilePath)

	Saver.doJob()

	#teststr = ["asdasd\r", "asdasdsad\n", "asdsadsad"]

	#for i in range (0, len(teststr) - 1):
	#	teststr[i] = ImageSaverFromUrls(rootPath, urlsPath, cacheFilePath).deleteChars(teststr[i], "\r\n")

	#for el in teststr: 
	#	print(el + "\r")