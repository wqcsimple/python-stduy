# -*- coding: utf-8 -*-
# 爬取 Contract Notice List
import json
import uuid
from urllib.parse import urlencode
from datetime import datetime
import time
import scrapy
from bs4 import BeautifulSoup
from scrapy import Selector

from ..items import *


SPIDER_DEBUG = False
SPIDER_TYPE = 3
WEB_SITE_URL = "https://www.tenders.gov.au"

class CnSpider(scrapy.Spider):
    name = "cn"
    allowed_domains = ["www.tenders.gov.au"]
    # start_urls = ['https://www.tenders.gov.au/?event=public.CNSON.list&cn_weekly=%7Bts+%272017-07-02+00%3A00%3A00%27%7D%2C%7Bts+%272017-07-08+23%3A59%3A59%27%7D&cn_weekly_submit=']
    # start_urls = ['https://www.tenders.gov.au/']

    def start_requests(self):

        week_ago_time = time.strftime('%Y-%m-%d 00:00:00', time.localtime(time.time() - 86400 * 7)) # 一周前时间
        today_time = time.strftime('%Y-%m-%d 23:59:59', time.localtime()) # 当前时间

        request_body = {
            'event': "public.CNSON.list",
            'cn_weekly': "{ts '" + week_ago_time +"'}, {ts '" + today_time + "'}",
            'cn_weekly_submit': ""
        }
        print(request_body)
        request_url = "https://www.tenders.gov.au/?" + urlencode(request_body)

        # 加入每次爬取的版本号
        version = uuid.uuid1()
        yield scrapy.Request(url=request_url, meta={'version': str(version)})

        pass

    def parse(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        ## 所有内容的集合
        item_box_list = soup.find_all('div', class_='boxEQH')

        if (SPIDER_DEBUG):
            item_href_link = item_box_list[0].find("a", attrs={'href': True}, class_="detail")
            item_url = WEB_SITE_URL + item_href_link['href']

            print("request url : " + item_url)

            item_url = 'https://www.tenders.gov.au/?event=public.cn.view&CNUUID=77B9CA55-C1B8-99F4-E5EE713A477B41B1'
            yield scrapy.Request(url=item_url, callback=self.process_detail, meta=response.meta)

        else:
            for item_box in item_box_list:
                item_href_link = item_box.find("a", attrs={'href': True}, class_="detail")
                item_url = WEB_SITE_URL + item_href_link['href']

                print("request url : " + item_url)
                yield scrapy.Request(url=item_url, callback=self.process_detail, meta=response.meta)

        if (SPIDER_DEBUG == False):
            # 分页处理
            pagination = soup.find('ul', class_='pagination')
            next_page_btn = pagination.find('li', class_='next')
            if next_page_btn != None:
                next_page_url = WEB_SITE_URL + "/" + next_page_btn.find('a', attrs={'href': True})['href']

                print("Request page url: {0}".format(next_page_url))
                yield scrapy.Request(url=next_page_url, callback=self.parse, meta=response.meta)

            else:
                print('=========== page finish ==========')

        pass

    def process_detail(self, response):
        sel = Selector(response)
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        content_box = soup.find('div', class_='listInner')
        list_desc_list = content_box.find_all('div', class_='list-desc')

        data_dict = {}

        data_dict['version'] = response.meta['version']

        # 左边标题
        cn_title = sel.xpath('//p[@class=\"lead\"]/text()').extract_first()
        data_dict['cn_title'] = cn_title

        for list_desc_item in list_desc_list:
            label_title = list_desc_item.find('span').get_text().lower().replace(' ', '_').replace(':', '')
            label_desc = ""
            # 判断这个内容是否存在
            if (list_desc_item.find("div", class_='list-desc-inner') != None):
                label_desc = list_desc_item.find("div", class_='list-desc-inner').get_text()

            data_dict[label_title] = label_desc

        print("====== cn data ======")
        print(data_dict)
        yield self.process_data(data_dict)

        pass

    def process_data(self, data_dict):
        item = JshCrawlItem()

        item['type'] = SPIDER_TYPE
        item['version'] = self.process_dict(data_dict, "version")

        item['cn_title'] = self.process_dict(data_dict, 'cn_title')
        item['cn_id'] = self.process_dict(data_dict, 'cn_id').strip()
        item['atm_id'] = self.process_dict(data_dict, 'atm_id')
        item['agency'] = self.process_dict(data_dict, 'agency')
        item['publish_date'] = self.process_dict(data_dict, 'publish_date')
        item['category'] = self.process_dict(data_dict, 'category')
        item['contract_period'] = self.process_dict(data_dict, 'contract_period')
        item['contract_value'] = self.process_dict(data_dict, 'contract_value_(aud)')
        item['description'] = self.process_dict(data_dict, 'description')
        item['procurement_method'] = self.process_dict(data_dict, 'procurement_method')
        item['confidentiality_contract'] = self.process_dict(data_dict, 'confidentiality_-_contract')
        item['confidentiality_outputs'] = self.process_dict(data_dict, 'confidentiality_-_outputs')
        item['consultancy'] = self.process_dict(data_dict, 'consultancy')
        item['agency_reference_id'] = self.process_dict(data_dict, 'agency_reference_id')
        item['cn_name'] = self.process_dict(data_dict, 'name').strip()
        item['cn_address'] = self.process_dict(data_dict, 'postal_address')
        item['cn_town'] = self.process_dict(data_dict, 'town/city')
        item['cn_postcode'] = self.process_dict(data_dict, 'postcode')
        item['cn_state'] = self.process_dict(data_dict, 'state/territory')
        item['cn_country'] = self.process_dict(data_dict, 'country')
        item['cn_abn'] = self.process_dict(data_dict, 'abn')

        return item

    # 处理字典数据，如果存在则取出，不存在返回空
    def process_dict(self, data, key):
        if (data.get(key, 'none') != 'none'):
            return data.get(key)
        else:
            return ""
        pass