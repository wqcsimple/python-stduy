# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import logging

class PortrayPipeline(object):

    def open_spider(self, spider):
        self.client = pymongo.MongoClient('mongodb', 27017)
        self.db = self.client['spider']
        self.rosi = self.db['portray']

    def process_item(self, item, spider):
        data = {
            'title': item['title'],
            'img': item['img'],
            'type': item['type'],
            'status': 0
        }
        if not self.rosi.find_one({'img': item['img']}) :
            self.rosi.insert_one(data)
        else:
            logging.info("%s - %s exists", item['img'], item['title'])

        return item
