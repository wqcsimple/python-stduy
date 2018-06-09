# -*- coding: utf-8 -*-
import pymongo
import scrapy
from bs4 import BeautifulSoup

from ..items import NovelContentItem

class NovelContentSpider(scrapy.Spider):
    name = "novel_content"

    def __init__(self):
        self.client = pymongo.MongoClient('mongo', 27017)
        self.db = self.client['spider']
        self.novel_category = self.db['novel_category']

    #  1 - 玄幻 2- 武侠 5 - 穿越 6 - 网游
    category = 5
    # start_urls = ['http://novel/']

    def start_requests(self):
        db_novel_category_list = self.novel_category.find({'type': self.category}).limit(1)

        start_urls = []
        for db_novel in db_novel_category_list:
            start_urls.append(db_novel['href'])

        for url in start_urls:
            self.log(url)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        soup = BeautifulSoup(response.body, 'html5lib')

        chapters_holder = soup.find('ul', class_='chapters')

        tag_a_list = chapters_holder.find_all('a', attrs={'href': True})
        # for tag_a in tag_a_list:
        #     name = tag_a.contents[0]
        #     href = tag_a['href']
        #     yield scrapy.Request(url=href, callback=self.parse_chapter_content, meta={"name": name, "page_href": response.url})

        first_item = tag_a_list[0]
        name = first_item.contents[0]
        href = first_item['href']
        yield scrapy.Request(url=href, callback=self.parse_chapter_content, meta={"name": name, "page_href": response.url})

        pass

    def parse_chapter_content(self, response):
        soup = BeautifulSoup(response.body, 'html5lib')

        content_holder = soup.find(id='content')

        meta = response.meta
        novel_content_item = NovelContentItem()
        novel_content_item['type'] = 101
        novel_content_item['page_href'] = meta['page_href']
        novel_content_item['name'] = meta['name']
        novel_content_item['url'] = response.url
        novel_content_item['content'] = str(content_holder)

        return novel_content_item

        pass
