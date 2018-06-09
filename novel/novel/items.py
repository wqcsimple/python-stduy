# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class NovelItem(scrapy.Item):
    # define the fields for your item here like:
    name = Field()
    pass

class NovelCategoryItem(scrapy.Item):
    type = Field()
    title = Field()
    href = Field()
    pass

class NovelContentItem(scrapy.Item):
    type = Field()
    page_href = Field() # 所属小说的网址，用于做统一标识
    name = Field()
    url = Field()
    content = Field()
    pass