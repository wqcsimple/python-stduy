# -*- coding: utf-8 -*-
import json
import os

import scrapy
from bs4 import BeautifulSoup
from ..items import T66yItem

DEFAULT_HEADERS = [
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
    },
    {
        'User-Agent': 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)'
    }
]

class T66ySpider(scrapy.Spider):
    name = 't66y'


    def start_requests(self):
        urls = ['http://t66y.com/thread0806.php?fid=16']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        content = response.body

        soup = BeautifulSoup(content, 'html5lib')
        title_list = soup.find_all('font', attrs={'color': 'green'})
        t66y_item = T66yItem()
        for title in title_list:
            t66y_item['title'] = title.contents[0]
            t66y_item['url'] = 'http://t66y.com/' + title.parent['href']

            # result.append(item)

        return t66y_item
        # self.log(result)

        # self.writeContent(json.dumps(result, ensure_ascii=False))


    # 把内容写入文件
    def writeContent(self, content):
        file_path = os.getcwd() + '/file/t66y/'
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        f = open(file_path + 'content.txt', 'w')
        f.write(content)
        f.write('\n')
        f.write('\n')
        f.close()

