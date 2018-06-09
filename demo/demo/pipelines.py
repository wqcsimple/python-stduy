# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import pymongo
import time

class DemoPipeline(object):

    def open_spider(self, spider):
        self.client = pymongo.MongoClient('localhost', 27017)
        self.db = self.client.spider
        self.t66y = self.db.t66y

    def process_item(self, item, spider):

        data = {
            'title': item['title'],
            'url': item['url'],
            'time': int(time.time()),
            'status': 0
        }
        if not self.t66y.find_one({'url': item['url']}) :
            self.t66y.insert_one(data)

        return item

    # def close_spider(self):