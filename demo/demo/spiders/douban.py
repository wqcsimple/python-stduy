# -*- coding: utf-8 -*-
import scrapy
from bs4 import BeautifulSoup

from ..items import *

class DoubanSpider(scrapy.Spider):
    name = 'douban'
    # allowed_domains = ['douban.com']
    # start_urls = [
    #     'http://t66y.com/thread0806.php?fid=16&search=&page=1',
    #     'http://t66y.com/thread0806.php?fid=16&search=&page=2',
    # ]

    def start_requests(self):
        # urls = [
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=1',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=2',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=3',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=4',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=5',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=6',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=8',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=9',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=10',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=11',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=12',
        #     'http://t66y.com/thread0806.php?fid=16&search=&page=13',
        # ]
        for i in range(1):
            url = '{0}{1}'.format("http://t66y.com/thread0806.php?fid=16&search=&page=", i+1)
            self.log("request url: " + url)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        content = response.body

        soup = BeautifulSoup(content, 'html5lib')
        title_list = soup.find_all('font', attrs={'color': 'green'})
        for title in title_list:
            title_name = title.contents[0]
            self.log("wait request title: " + title.contents[0])
            url = 'http://t66y.com/' + title.parent['href']
            yield scrapy.Request(url, meta={'title': title_name}, callback=self.parse_post)

        # self.log("wait request title: " + title_list[0].contents[0])
        # url = 'http://t66y.com/' + title_list[0].parent['href']
        # self.log(url)
        # yield scrapy.Request(url, self.parse_post)

    def parse_post(self, response):
        title = response.meta['title']
        soup = BeautifulSoup(response.body, 'html5lib')

        pic_list_content = soup.find('div', class_='tpc_content do_not_catch')
        pic_list = pic_list_content.find_all('input')

        for pic in pic_list:
            yield self.process_img(title, pic['src'])

    def process_img(self, title, url):
        item = DemoItem()
        item['title'] = title
        item['url'] = url

        return item



