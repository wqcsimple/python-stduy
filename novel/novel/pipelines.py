# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


# type 1 - 武侠
import pymongo
import time


class NovelPipeline(object):

    def open_spider(self, spider):
        self.client = pymongo.MongoClient('mongo', 27017)
        self.db = self.client['spider']
        self.novel_category = self.db['novel_category']
        self.novel_content = self.db['novel_content']

    def process_item(self, item, spider):

        if item['type'] < 100:
            self.process_data(item)
        else:
            self.process_data_for_content(item)

        return item


    def process_data(self, item):
        data = {
            'type': item['type'],
            'title': item['title'],
            'href': item['href']
        }

        if not self.novel_category.find_one({'href': item['href']}) :
            self.novel_category.insert_one(data)

        pass

    def process_data_for_content(self, item):
        data = {
            'page_href': item['page_href'],
            'name': item['name'],
            'url': item['url'],
            'content': item['content'],
            'create_time': int(time.time())
        }
        if not self.novel_content.find_one({'url': item['url']}) :
            self.novel_content.insert_one(data)

        pass