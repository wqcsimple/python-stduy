# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo


class ManhuaPipeline(object):

    def open_spider(self, spider):
        self.client = pymongo.MongoClient('mongo', 27017)
        self.db = self.client['spider']
        self.rosi = self.db['rosi']

    def process_item(self, item, spider):
        data = {
            'title': item['title'],
            'img': item['img'],
            'status': 0
        }
        if not self.rosi.find_one({'img': item['img']}) :
            self.rosi.insert_one(data)

        return item
