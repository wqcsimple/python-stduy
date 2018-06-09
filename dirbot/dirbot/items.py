# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import os

import scrapy
from scrapy.item import Item, Field


class Article(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = Field()
    url = Field()

class T66yItem(Item):
    title = Field()
    url = Field()


