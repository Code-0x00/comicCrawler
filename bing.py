# coding=utf-8

import urllib
import requests
from requests import exceptions
import json
import pprint
import time
import os
import re
import socket
#import chardet

englishlist=[
'British Shorthair',
'Chihuahua'
]
URL = 'http://cn.bing.com/images/async'
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
           'AppleWebKit/537.36 (KHTML, like Gecko) '
           'Chrome/56.0.2924.87 Safari/537.36',
           'Referer': 'https://cn.bing.com/images/'}

def getPicURL(searchWord, pn):
    params = {
              'q': searchWord,
              'first':str(36*int(pn)),
              'count':'35',
              'relp':'35',
              'mmasync':'1',
              }
    try:
        response = requests.get(URL, params=params,
                                headers=headers, timeout=10)
        print response.url
        response.raise_for_status()
    except exceptions.Timeout as e:
        print e.message
    except exceptions.HTTPError as e:
        print e.message
    except Exception as e:
        print 'something wrong!'
        raise Exception
    else:
	urls=re.findall('src="(http:.*?)"',response.content) 
	print len(urls)
	if len(urls)<35:
		return 1
	for i in range(len(urls)):
		print i
    		socket.setdefaulttimeout(15)
		try:
			urllib.urlretrieve(urls[i],searchWord+'/'+searchWord+'.'+"%03d"%pn+'.'+ "%04d"%(i) +'.jpg')
		except socket.timeout:
			print 'time out'
			continue
    return 0
       
def startCrawler(searchWord):
    Page=9999
    if not os.path.isdir(searchWord):
        try:
            os.mkdir(searchWord)
        except OSError:
            print 'there is a file named '+searchWord+'!!!!'
            exit()

    for i in range(0, Page):
        try:
            if getPicURL(searchWord, i)==0:
            	time.sleep(5)
	    else :
		return 0
        except Exception as e:
            print e.message
            print 'start download next page'


if __name__ == '__main__':
    	for i in range(37):
		startCrawler(englishlist[i])
