# -*- coding: utf-8 -*-
import scrapy
from bs4 import BeautifulSoup

from ..items import Article

class WhisSpider(scrapy.Spider):
    name = 'whis'
    # allowed_domains = ['whis']
    start_urls = ['http://whis.wang']

    def parse(self, response):
        url = 'http://whis.wang'
        yield scrapy.Request(url, callback=self.detail)

    def detail(self, response):
        response_body = BeautifulSoup(response.body, 'html5lib')

        article = Article();

        article_list = response_body.find('section', class_='article-list')

        title_a_list = article_list.find_all('a', attrs={'href': True})

        for title_a in title_a_list:
            article['title'] = title_a.contents[0]
            article['url'] = title_a['href']
            self.log(article)

        return article
        # i = Article()
        # i['title'] = 'whis'
        # i['url'] = 'http://www.baidu.com'

