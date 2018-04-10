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
def getContent(id):
    url='http://ac.qq.com/Comic/comicInfo/id/{}'.format(id)
    mainResponse=requests.get(url)
    ol=re.findall(r"""<ol class="chapter-page-all works-chapter-list">(.+?)</ol>""",mainResponse.text,re.S)
    allTitleLink=re.findall(r"<a(.+?)>",ol[0])
    listTitleUrl=[{} for i in allTitleLink]
    for i in range(len(allTitleLink)):
        title=re.findall(r"""title=(.+?)\"""",allTitleLink[i])[0]
        #print title
        listTitleUrl[i]['title']=re.findall(r"""title=\"(.+?)\"""",allTitleLink[i])[0]
        listTitleUrl[i]['link']=re.findall(r"""href=\"(.+?)\"""",allTitleLink[i])[0]
    author=re.findall(r"""<em style=\"max-width: 168px;\">(.+?)</em>""",mainResponse.text)
    comicName=re.findall(r"""<h2 class="works-intro-title ui-left"><strong>(.+?)</strong></h2>""",mainResponse.text)
    comicIntrd=re.findall(r"""<p class="works-intro-short ui-text-gray9">(.+?)</p>""",mainResponse.text,re.S)
    return comicName,comicIntrd,str(len(listTitleUrl)),listTitleUrl

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
#__download_one_img(imgUrl[0].replace('\\/','/'),'test.jpg')
def getImgList(pageUrl):
    print pageUrl
    pageResponse = requestSession.get('http://ac.qq.com'+pageUrl)
    #print pageResponse.text
    #base64data=re.findall(r"""var DATA(\s+)= '(.+)'""",pageResponse.text)
    base64data=re.findall(r"""data: '(.+)'""",pageResponse.text)
    #print base64data[0]
    imgList=base64.b64decode(base64data[0][1:])
    #print imgList,"url":
    imgUrl=re.findall(r"""\"url\":\"(.+?)\"""",imgList)
    for i in range(len(imgUrl)):
        imgUrl[i]=imgUrl[i].replace('\\/','/')
    return imgUrl
    
def main(id):
    comicName,comicIntrd,count,contentList = getContent(id)
    contentNameList = [i['title'] for i in contentList]

    #print '漫画名:',comicName[0]
    #print '简介: ',comicIntrd[0]
    #print('章节数: {}'.format(count))
    #print('章节列表:')

    #try:
    #    print('\n'.join(contentNameList))
    #except Exception:
    #    print('章节列表包含无法解析的特殊字符\n')
    for i in contentList:
        imgList=getImgList(i['link'])
        print imgList

main('505430')