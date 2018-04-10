#!/usr/bin/python
# encoding: utf-8

'''***本代码仅供学习交流使用，严禁用于非法用途，各种PR都欢迎***'''

import requests
import re
import json
import os
import sys
import argparse
import threading
from time import sleep

requestSession = requests.session()
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
requestSession.headers.update({'User-Agent': UA})

class ErrorCode(Exception):
    '''自定义错误码:
        1: URL不正确
        2: URL无法跳转为移动端URL
        3: 中断下载'''
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return repr(self.code)

def isLegelID(id):
    if len(id)==6:
        return True
    return False

def getId(id):
    if not isLegelID(id):
        print('请输入正确的ID！ID为6位数字，请在命令行输入-h|--help参数查看帮助文档。')
        raise ErrorCode(1)
    return id

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

def getImgList(pageUrl):
    pageResponse = requestSession.get('http://ac.qq.com'+pageUrl)
    base64data=re.findall(r"""data: '(.+)'""",pageResponse.text)
    imgList=base64.b64decode(base64data[0][1:])
    imgUrl=re.findall(r"""\"url\":\"(.+?)\"""",imgList)
    for i in range(len(imgUrl)):
        imgUrl[i]=imgUrl[i].replace('\\/','/')
    return imgUrl

def downloadImg(imgUrlList, contentPath, one_folder=False):
    count = len(imgUrlList)
    print('该集漫画共计{}张图片'.format(count))
    i = 1
    downloaded_num = 0
    
    def __download_callback():
        nonlocal downloaded_num
        nonlocal count
        downloaded_num += 1
        print('\r{}/{}... '.format(downloaded_num, count), end='')
        
    download_threads = []
    for imgUrl in imgUrlList:
        if not one_folder:
            imgPath = os.path.join(contentPath, '{0:0>3}.jpg'.format(i))
        else:
            imgPath = contentPath + '{0:0>3}.jpg'.format(i)
        i += 1
        
        #目标文件存在就跳过下载
        if os.path.isfile(imgPath):
            count -= 1
            continue
        download_thread = threading.Thread(target=__download_one_img, 
            args=(imgUrl,imgPath, __download_callback))
        download_threads.append(download_thread)
        download_thread.start()
    [ t.join() for t in download_threads ]
    print('完毕!\n')

def __download_one_img(imgUrl,imgPath, callback):
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
          callback()
          break
      except (KeyboardInterrupt, SystemExit):
          print('\n\n中断下载，删除未下载完的文件！')
          if os.path.isfile(imgPath):
              os.remove(imgPath)
          raise ErrorCode(3)
      except:
          retry_num += 1
          if retry_num >= retry_max:
              raise
          print('下载失败，重试' + str(retry_num) + '次')
          sleep(2)

def parseLIST(lst):
    '''解析命令行中的-l|--list参数，返回解析后的章节列表'''
    legalListRE = re.compile(r'^\d+([,-]\d+)*$')
    if not legalListRE.match(lst):
        raise LISTFormatError(lst + ' 不匹配正则: ' + r'^\d+([,-]\d+)*$')

    #先逗号分割字符串，分割后的字符串再用短横杠分割
    parsedLIST = []
    sublist = lst.split(',')
    numRE = re.compile(r'^\d+$')

    for sub in sublist:
        if numRE.match(sub):
            if int(sub) > 0: #自动忽略掉数字0
                parsedLIST.append(int(sub))
            else:
                print('警告: 参数中包括不存在的章节0，自动忽略')
        else:
            splitnum = list(map(int, sub.split('-')))
            maxnum = max(splitnum)
            minnum = min(splitnum)       #min-max或max-min都支持
            if minnum == 0:
                minnum = 1               #忽略数字0
                print('警告: 参数中包括不存在的章节0，自动忽略')
            parsedLIST.extend(range(minnum, maxnum+1))

    parsedLIST = sorted(set(parsedLIST)) #按照从小到大的顺序排序并去重
    return parsedLIST

def main(id, path, lst=None, one_folder=False):
    '''id: 要爬取的漫画ID。 path: 漫画下载路径。 lst: 要下载的章节列表(-l|--list后面的参数)'''
    try:
        if not os.path.isdir(path):
           os.makedirs(path)
        id = getId(id)
        comicName,comicIntrd,count,contentList = getContent(id)
        contentNameList = [i['title'] for i in contentList]

        print('漫画名: {}'.format(comicName))
        print('简介: {}'.format(comicIntrd))
        print('章节数: {}'.format(count))
        print('章节列表:')
        try:
            print('\n'.join(contentNameList))
        except Exception:
            print('章节列表包含无法解析的特殊字符\n')
            
        forbiddenRE = re.compile(r'[\\/":*?<>|]') #windows下文件名非法字符\ / : * ? " < > |
        comicName = re.sub(forbiddenRE, '_', comicName) #将windows下的非法字符一律替换为_
        comicPath = os.path.join(path, comicName)
        if not os.path.isdir(comicPath):
            os.makedirs(comicPath)
        print()
        
        if not lst:
            contentRange = range(1, len(contentList) + 1)
        else:
            contentRange = parseLIST(lst)

        for i in contentRange:
            if i > len(contentList):
                print('警告: 章节总数 {} ,'
                        '参数中包含过大数值,'
                        '自动忽略'.format(len(contentList)))
                break

            contentNameList[i - 1] = re.sub(forbiddenRE, '_', contentNameList[i - 1]) #将windows下的非法字符一律替换为_
            contentPath = os.path.join(comicPath, '第{0:0>4}话-{1}'.format(i, contentNameList[i - 1]))

            try:
                print('正在下载第{0:0>4}话: {1}'.format(i, contentNameList[i -1]))
            except Exception:
                print('正在下载第{0:0>4}话: {1}'.format(i))

            if not one_folder:
                if not os.path.isdir(contentPath):
                    os.mkdir(contentPath)

            imgList = getImgList(contentList[i - 1]['link'])
            downloadImg(imgList, contentPath, one_folder)

    except ErrorCode as e:
        exit(e.code)
    
if __name__ == '__main__':
    defaultPath = 'tencent_comic'

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='*下载腾讯漫画，仅供学习交流，请勿用于非法用途*\n'
                                     '空参运行进入交互式模式运行。')
    parser.add_argument('-i', '--id', help='漫画首页地址的ID，如：\n'
            'http://ac.qq.com/Comic/comicInfo/id/505430\n'
            '则输入：505430')
    parser.add_argument('-p', '--path', help='漫画下载路径。 默认: {}'.format(defaultPath), 
                default=defaultPath)
    parser.add_argument('-d', '--dir', action='store_true', help='将所有图片下载到一个目录(适合腾讯漫画等软件连看使用)')
    parser.add_argument('-l', '--list', help=("要下载的漫画章节列表，不指定则下载所有章节。格式范例: \n"
                                              "N - 下载具体某一章节，如-l 1, 下载第1章\n"
                                              'N,N... - 下载某几个不连续的章节，如 "-l 1,3,5", 下载1,3,5章\n'
                                              'N-N... - 下载某一段连续的章节，如 "-l 10-50", 下载[10,50]章\n'
                                              '杂合型 - 结合上面所有的规则，如 "-l 1,3,5-7,11-111"'))
    args = parser.parse_args()
    id = args.id
    path = args.path
    lst = args.list
    one_folder = args.dir

    if lst:
        legalListRE = re.compile(r'^\d+([,-]\d+)*$')
        if not legalListRE.match(lst):
            print('LIST参数不合法，请参考--help键入合法参数！')
            exit(1)

    if not id:
        id = input('请输入漫画首页地址ID: ')
        path = input('请输入漫画保存路径(默认: {}): '.format(defaultPath))
        if not path:
            path = defaultPath

    main(id, path, lst, one_folder)