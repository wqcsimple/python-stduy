# -*- coding: utf-8 -*-
import pymysql
import scrapy
import  time
from bs4 import BeautifulSoup

from ..items import *

class MhSpider(scrapy.Spider):
    name = "mh"
    arr = []
    # allowed_domains = ["whis"]
    # start_urls = ['http://manhua.dmzj.com/yiquanchaoren/']

    def start_requests(self):
        for i in range(1, 11):
            url = "http://www.dazui88.com/tag/xiuren/list_87_{0}.html".format(i)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        section_list_holder = soup.find('div', class_='lbtcimg1')
        section_list = section_list_holder.find_all('img')
        href_prefix = 'http://www.dazui88.com'

        for section in section_list:
            title = section['alt']
            request_url = href_prefix + section.parent['href']
            yield scrapy.Request(url=request_url, callback=self.parse_content, meta={'title': title})

        # first_item = section_list[0]
        # title_name = first_item['alt']
        # url = href_prefix + first_item.parent['href']
        # yield scrapy.Request(url=url, callback=self.parse_content, meta={'title': title_name})

    def parse_content(self, response):
        page_title = response.meta['title']

        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        page_count = soup.find(id='efpBigPic')
        img_list = page_count.find_all('img')

        for img in img_list:
            img_src = img['src']
            yield self.process_data(page_title, img_src)

        # # 列表下方的分页
        page_tag = soup.find('div', class_='pagebreak1')
        if len(page_tag) < 1:
            self.log('page list error')
            return

        # 获取所有分页a标签
        link_a_list = page_tag.find_all('a', attrs={'href': True})
        last_link_a = link_a_list[-1]

        href_prefix = 'http://www.dazui88.com/tag/xiuren/'
        if last_link_a['href'] != '#':
            # self.log(last_link_a['href'])
            next_page = href_prefix + last_link_a['href']
            yield scrapy.Request(url=next_page, callback=self.parse_content, meta={'title': page_title})
            pass
        else:
            print('========= {0} Last page =========='.format(page_title))


    def process_data(self, title, img):
        item = ManhuaItem()
        item['title'] = title
        item['img'] = img

        return item
