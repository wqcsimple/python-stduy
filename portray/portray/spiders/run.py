# -*- coding: utf-8 -*-
import random

import scrapy
from bs4 import BeautifulSoup
from scrapy.conf import settings
from scrapy import log

from ..items import *




class RunSpider(scrapy.Spider):
    name = "run"
    # allowed_domains = ["whis.wang"]
    # start_urls = ['http://whis.wang/']

    # 写真名: 页数
    tag_list = {"rosi": 50, 'xiurenwang': 30}
    process_tag = "" # 待爬的tag

    website_url = "https://www.aitaotu.com"
    spider_website_tag = ""

    def start_requests(self):
        for tag, value in self.tag_list.items():
            self.process_tag = tag
            self.spider_website_tag = "/tag/{0}/".format(self.process_tag)

            for i in range(1, value + 1):
                ua = random.choice(settings.get("USER_AGENT_LIST"))
                url = self.website_url + self.spider_website_tag + "{0}.html".format(i)

                yield scrapy.Request(url=url, callback=self.parse, headers={'User-Agent': ua})

        pass


    def parse(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        section_list_holder = soup.find(id='mainbodypul')
        section_list = section_list_holder.find_all('a')

        for section in section_list:
            title = section['title']
            request_url = self.website_url + section['href']
            yield scrapy.Request(url=request_url, callback=self.parse_content, meta={'title': title})

        # first_item = section_list[0]
        # title_name = first_item['title']
        # url = self.website_url + first_item['href']
        # yield scrapy.Request(url=url, callback=self.parse_content, meta={'title': title_name})
        # pass

    def parse_content(self, response):
        page_title = response.meta['title']

        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        page_count = soup.find(id='big-pic')
        img_list = page_count.find_all('img')

        for img in img_list:
            img_src = img['src']
            yield self.process_data(page_title, img_src)

        # # 列表下方的分页
        page_tag = soup.find('div', class_='pages')
        if len(page_tag) < 1:
            self.log('page list error')
            return

        next_page_el = page_tag.find(id="nl")

        if not next_page_el is None:
            next_page_url = self.website_url + next_page_el.a['href']
            print("request url: ", next_page_url)
            yield scrapy.Request(url=next_page_url, callback=self.parse_content, meta={'title': page_title})
        else :
            print('========= {0} Last page =========='.format(page_title))

        # 获取所有分页a标签
        # link_a_list = page_tag.find_all('a', attrs={'href': True})
        # last_link_a = link_a_list[-2]
        #
        # if last_link_a['href'] != '#':
        #     next_page = self.website_url + last_link_a['href']
        #     yield scrapy.Request(url=next_page, callback=self.parse_content, meta={'title': page_title})
        #     pass
        # else:
        #     print('========= {0} Last page =========='.format(page_title))
        # pass

    def process_data(self, title, img):
        item = PortrayItem()
        item['title'] = title
        item['img'] = img
        item['type'] = self.process_tag

        return item
