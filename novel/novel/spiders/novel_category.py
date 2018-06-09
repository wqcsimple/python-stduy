# -*- coding: utf-8 -*-
import scrapy
from bs4 import BeautifulSoup

from ..items import NovelCategoryItem


class NovelCategorySpider(scrapy.Spider):
    name = "novel_category"
    allowed_domains = ["novel"]

    #  1 - 玄幻 2- 武侠 5 - 穿越 6 - 网游
    category = 5
    limit = 2  # 页数
    start_urls = []
    for i in range(1, limit):
        url = "http://maxdd.com/list/{0}_{1}.shtml".format(category, i)
        start_urls.append(url)

    # start_urls = [
    #     'http://maxdd.com/list/6_1.shtml',
        # 'http://maxdd.com/list/6_2.shtml',
        # 'http://maxdd.com/list/6_3.shtml',
        # 'http://maxdd.com/list/6_4.shtml',
        # 'http://maxdd.com/list/6_5.shtml',
        # 'http://maxdd.com/list/6_6.shtml',
        # 'http://maxdd.com/list/6_7.shtml',
        # 'http://maxdd.com/list/6_8.shtml',
        # 'http://maxdd.com/list/6_9.shtml',
    # ]

    def parse(self, response):
        soup = BeautifulSoup(response.body, 'html5lib')

        tag_li_list = soup.find_all('li', class_='min-width')

        for tag_li in tag_li_list:
            tag_a = tag_li.find('a', attrs={'title': True})
            yield self.processCategoryData(tag_a['title'], tag_a['href'])



    def processCategoryData(self, title, href):
        novel_category_item = NovelCategoryItem()
        novel_category_item['type'] = self.category    # 武侠系列
        novel_category_item['title'] = title[0:-4]
        novel_category_item['href'] = href

        return novel_category_item