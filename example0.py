#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

import requests
import os
import re
import base64

requestSession = requests.session()
UA = 'Mozilla/5.0 (Linux; U; Android 4.0.3; zh-CN; \
HTC Velocity 4G X710s Build/IML74K) AppleWebKit/534.30 \
(KHTML, like Gecko) Version/4.0 UCBrowser/10.1.3.546 \
U3/0.8.0 Mobile Safari/534.30' # UC UA
requestSession.headers.update({'User-Agent': UA})

r"""
主页-所有画列表获取代码段
"""
mainResponse=requests.get('http://ac.qq.com/Comic/comicInfo/id/505430')
#print type(mainResponse.text)
#print mainResponse.text

ol=re.findall(r"""<ol class="chapter-page-all works-chapter-list">(.+?)</ol>""",mainResponse.text,re.S)
#for i in xOl:
#    print i
#print xOl

allTitleLink=re.findall(r"<a(.+?)>",ol[0])
#print len(allTitleLink

OPList=[{} for i in allTitleLink]
for i in range(len(allTitleLink)):
    title=re.findall(r"""title=(.+?)\"""",allTitleLink[i])[0]
    #print title
    OPList[i]['title']=re.findall(r"""title=(.+?)\"""",allTitleLink[i])[0]
    OPList[i]['link']=re.findall(r"""href=\"(.+?)\"""",allTitleLink[i])[0]
#for i in OPList:
#    print i['title'],i['link']
r"""
一画中图片列表获取
"""
url='http://ac.qq.com'+OPList[1]['link']
#url='http://m.ac.qq.com/chapter/index/id/505430/cid/1'
comicResponse=requests.get(url)
#print comicResponse.text

base64data=re.findall(r"""var DATA(\s+)= '(.+)'""",comicResponse.text)
#print base64data[0][1][1:]
#print base64.b64decode(base64data[0][1][1:])
imgList=base64.b64decode(base64data[0][1][1:])
imgUrl=re.findall(r"""http:.+?jpg""",imgList)

f=open('url.txt','w')
for i in imgUrl:
    #print i
    f.write(i)
    f.write('\n')
f.close()

def __download_one_img(imgUrl,imgPath):
    print imgUrl
    retry_num = 0
    retry_max = 2
    while True:
      try:
          downloadRequest = requestSession.get(imgUrl, stream=True)
          with open(imgPath, 'wb') as f:
              for chunk in downloadRequest.iter_content(chunk_size=1024): 
                  if chunk: # filter out keep-alive new chunks
                      f.write(chunk)
                      f.flush()
          break
      except:
          print('下载失败，重试' + str(retry_num) + '次')
          sleep(2)
__download_one_img(imgUrl[0].replace('\\/','/'),'test.jpg')