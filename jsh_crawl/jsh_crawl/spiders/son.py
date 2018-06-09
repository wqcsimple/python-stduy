# -*- coding: utf-8 -*-
# 爬取Standing Offer Notice List 页面 https://www.tenders.gov.au/?event=public.CNSON.list&son_weekly=%7Bts+%272017-07-02+00%3A00%3A00%27%7D%2C%7Bts+%272017-07-08+23%3A59%3A59%27%7D&son_weekly_submit=
import uuid
from urllib.parse import urlencode

import scrapy
import time
from bs4 import BeautifulSoup
from scrapy import Selector

from ..items import JshCrawlItem


SPIDER_DEBUG = False
SPIDER_TYPE = 2
WEB_SITE_URL = "https://www.tenders.gov.au"

class SonSpider(scrapy.Spider):
    name = "son"
    allowed_domains = ["www.tenders.gov.au"]
    # start_urls = ['https://www.tenders.gov.au/?event=public.CNSON.list&son_weekly=%7Bts+%272017-07-02+00%3A00%3A00%27%7D%2C%7Bts+%272017-07-08+23%3A59%3A59%27%7D&son_weekly_submit=']

    def start_requests(self):
        week_ago_time = time.strftime('%Y-%m-%d 00:00:00', time.localtime(time.time() - 86400 * 7))  # 一周前时间
        today_time = time.strftime('%Y-%m-%d 23:59:59', time.localtime())  # 当前时间

        request_body = {
            'event': "public.CNSON.list",
            'son_weekly': "{ts '" + week_ago_time + "'}, {ts '" + today_time + "'}",
            'son_weekly_submit': ""
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
            item_url = WEB_SITE_URL + item_box_list[0].find("a", attrs={'href': True}, class_="detail")['href']

            yield scrapy.Request(url=item_url, callback=self.process_detail, meta=response.meta)

        else:
            for item_box in item_box_list:
                item_href_link = item_box.find("a", attrs={'href': True}, class_="detail")
                item_url = WEB_SITE_URL + item_href_link['href']

                yield scrapy.Request(url=item_url, callback=self.process_detail, meta=response.meta)

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
        son_title = sel.xpath('//p[@class=\"lead\"]/text()').extract_first()
        data_dict['son_title'] = son_title

        # 左边联系方式
        # contact_box = sel.xpath('//div[@class=\"contact-long\"]/p/text()').extract()
        # data_dict['contact_name'] = contact_box[1]

        # data_dict['contact_phone'] = contact_box[2]

        # 左边联系邮箱
        # contact_email = soup.find('a', class_='email', attrs={'href': True}).get_text()
        # data_dict['contact_email'] = ""

        for list_desc_item in list_desc_list:
            label_title = list_desc_item.find('span').get_text().lower().replace(' ', '_').replace(':', '')
            label_desc = list_desc_item.find("div", class_='list-desc-inner').get_text()

            data_dict[label_title] = label_desc

        # 获取Suppliers
        supplier_tr_td_list = sel.xpath('//table[@class=\"genT\"]/tbody/tr/td[1]/text()').extract()
        data_dict['supplier'] = supplier_tr_td_list

        print("===== son data =======")
        print(data_dict)
        yield self.process_data(data_dict)

        pass

    def process_data(self, data_dict):
        item = JshCrawlItem()

        item['type'] = SPIDER_TYPE
        item['version'] = self.process_dict(data_dict, "version")

        item['son_title'] = self.process_dict(data_dict, "son_title")
        item['son_id'] = self.process_dict(data_dict, "son_id")
        item['agency'] = self.process_dict(data_dict, "agency")
        item['publish_date'] = self.process_dict(data_dict, "publish_date")
        item['primary_category'] = self.process_dict(data_dict, "primary_category")
        item['standing_offer_period'] = self.process_dict(data_dict, "standing_offer_period")
        item['title'] = self.process_dict(data_dict, "title")
        item['description'] = self.process_dict(data_dict, "description")
        item['procurement_method'] = self.process_dict(data_dict, "procurement_method")
        item['atm_id'] = self.process_dict(data_dict, "atm_id")
        item['multi_agency_access'] = self.process_dict(data_dict, "multi_agency_access")
        item['multi_agency_access_type'] = self.process_dict(data_dict, "multi_agency_access_type")
        item['panel_arrangement'] = self.process_dict(data_dict, "panel_arrangement")
        item['agency_reference_id'] = self.process_dict(data_dict, "agency_reference_id")
        item['supplier'] = self.process_dict(data_dict, 'supplier')

        return item

    # 处理字典数据，如果存在则取出，不存在返回空
    def process_dict(self, data, key):
        if (data.get(key, 'none') != 'none'):
            return data.get(key)
        else:
            return ""
        pass
