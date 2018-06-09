# -*- coding: utf-8 -*-
# 爬取ATMS页面 https://www.tenders.gov.au/?event=public.ATM.list
import json
import os

import redis
import uuid
from urllib.parse import urlencode

import requests
import time

from bs4 import BeautifulSoup
from scrapy import Selector

from ..items import *

SPIDER_DEBUG = False
SPIDER_TYPE = 1
SPIDER_ATM_DOCUMENT_TYPE = 4
WEB_SITE_URL = "https://www.tenders.gov.au/"


class AtmsSpider(scrapy.Spider):
    name = "atms"
    allowed_domains = ["www.tenders.gov.au"]

    cookies = None

    with open(os.getcwd() + "/config.json", "r") as config_file:
        config = json.load(config_file)
        db_redis = redis.StrictRedis(host=config['redis_host'], port=config['redis_port'], db=0,
                                     password=config['redis_pass'])

    start_urls = ['https://www.tenders.gov.au/?event=public.ATM.list']

    def start_requests(self):
        request_body = {
            'event': "public.ATM.list"
        }
        request_url = "https://www.tenders.gov.au/?" + urlencode(request_body)

        # 加入每次爬取的版本号
        version = uuid.uuid1()
        yield scrapy.Request(url=request_url, meta={'version': str(version)})
        pass

    def parse(self, response):
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        # 所有内容的集合
        item_box = soup.find('', class_='boxEQH')
        item_list = item_box.find_all("a", attrs={'href': True}, class_="detail")

        if (SPIDER_DEBUG):
            # item_url = WEB_SITE_URL + item_list[0]['href']
            item_url = "https://www.tenders.gov.au/?event=public.atm.showClosed&ATMUUID=AD629C3C-E285-8F10-AF83A4F3A4A6876E"
            yield scrapy.Request(url=item_url, callback=self.process_detail, meta=response.meta)

        else:
            for item in item_list:
                item_url = WEB_SITE_URL + item['href']
                yield scrapy.Request(url=item_url, callback=self.process_detail, meta=response.meta)

        if (SPIDER_DEBUG == False):
            # 分页处理
            pagination = soup.find('ul', class_='pagination')
            next_page_btn = pagination.find('li', class_='next')
            if next_page_btn != None:
                next_page_url = WEB_SITE_URL + next_page_btn.find('a', attrs={'href': True})['href']

                print("Request url: {0}".format(next_page_url))
                yield scrapy.Request(url=next_page_url, callback=self.parse, meta=response.meta)

            else:
                print('=========== page finish ==========')
                pass

        pass

    # 处理详情页，获取对应字段的数据
    def process_detail(self, response):
        sel = Selector(response)
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        content_box = soup.find('div', class_='listInner')
        if (content_box == None):
            print("------------- atm detail is none --------------")

        else:

            list_desc_list = content_box.find_all('div', class_='list-desc')

            data_dict = {}

            data_dict['version'] = response.meta['version']

            # 获取左边的订单标题
            atm_title = sel.xpath('//p[@class=\"lead\"]/text()').extract_first()
            data_dict['atm_title'] = atm_title

            # 左边联系方式
            contact_box = sel.xpath("//div[@class=\"contact\"]/p/text()").extract()
            print("contact box ,", contact_box)

            data_dict['contact_name'] = ""
            data_dict['contact_phone'] = ""
            data_dict['contact_mobile'] = ""

            if (len(contact_box) >= 4):
                data_dict['contact_name'] = contact_box[1]
                data_dict['contact_phone'] = contact_box[2]
                data_dict['contact_mobile'] = contact_box[3]

            if (len(contact_box) >= 3):
                data_dict['contact_name'] = contact_box[1]
                data_dict['contact_phone'] = contact_box[2]

            # 左边联系邮箱
            contact_email = sel.xpath("//div[@class=\"contact\"]/p/a/text()").extract_first()
            data_dict['contact_email'] = contact_email

            # 获取右边一整串的数据
            for list_desc_item in list_desc_list:
                label_title = list_desc_item.find('span').get_text().lower().replace(' ', '_').replace(':', '')
                label_desc = ""

                # 判断该项内容值是否存在
                list_desc_item_obj = list_desc_item.find("div", class_='list-desc-inner')
                if (list_desc_item_obj != None):
                    label_desc = list_desc_item_obj.get_text()

                    # 解析close date
                    if (label_title == 'close_date_&_time'):
                        label_desc = list_desc_item_obj.contents[0].replace("\n", "").replace("\t", "").replace(
                            "(ACT Local Time)", "")

                    # 判断是否是附件下载的项
                    if (label_title == 'addenda_available'):
                        label_desc = list_desc_item_obj.find('a', attrs={'href': True})['href']
                        if (label_desc != ''):
                            request_document_url = WEB_SITE_URL + label_desc
                            print("request document url", request_document_url)

                            self.cookies = self.login(label_desc)
                            print("cookies", self.cookies)

                            yield scrapy.Request(url=request_document_url, cookies=self.cookies,
                                                 callback=self.parse_document, meta=response.meta)

                data_dict[label_title] = label_desc

            if (SPIDER_DEBUG):
                print("===== atm data ====")
                print(data_dict)

            yield self.process_data(data_dict)

        pass

    # 处理附件
    def parse_document(self, response):
        sel = Selector(response)
        content = response.body
        soup = BeautifulSoup(content, 'html5lib')

        print("===== parse document page =====")

        atm_id = sel.xpath("//div[@class=\"box boxW r9 boxInner\"]/p/text()").extract_first()

        data_dict = {}

        data_dict['version'] = response.meta['version']

        file_list_ul = soup.find('ul', class_='file-list')

        if (file_list_ul == None):
            print("============== file a list none ==============")
        else:
            file_a_list = file_list_ul.find_all("a", attrs={'href': True})
            file_info_list_arr = []
            for file_a in file_a_list:
                title = file_a['title']
                url = WEB_SITE_URL + file_a['href']
                print("download document url " + url)

                # cookies = self.login(file_a['href'])
                # print("download cookies: ", cookies)

                dir_path = "./files/" + atm_id
                file_path = dir_path + "/" + title

                print("dir_path: ", dir_path)
                print("file_path: ", file_path)
                # 对文件进行判断是否已经下载
                if (os.path.exists(dir_path) == False):
                    os.makedirs(dir_path)
                else:
                    print("dir path is exists: ", dir_path)

                if (os.path.isfile(file_path) == False):
                    req = requests.get(url, cookies=self.cookies)
                    print("req headers: ", req.headers)
                    with open(file_path, "wb") as code:
                        code.write(req.content)

                    print("download document success: " + file_path)

                else:
                    print("file is download: ", file_path)

                obj = {
                    'title': file_a['title'],
                    'url': WEB_SITE_URL + file_a['href']
                }
                file_info_list_arr.append(obj)

            data_dict['document_list'] = file_info_list_arr
            data_dict['atm_id'] = atm_id

            print("===== atm document data ====")
            print(data_dict)

            yield self.process_atms_document(data_dict)
        pass

    def process_data(self, data_dict):

        item = JshCrawlItem()

        item['type'] = SPIDER_TYPE
        item['version'] = self.process_dict(data_dict, "version")

        item['atm_title'] = self.process_dict(data_dict, "atm_title")
        item['atm_id'] = self.process_dict(data_dict, "atm_id")
        item['agency'] = self.process_dict(data_dict, "agency")
        item['category'] = self.process_dict(data_dict, "category")
        item['close_date_time'] = self.process_dict(data_dict, "close_date_&_time")
        item['publish_date'] = self.process_dict(data_dict, "publish_date")
        item['location'] = self.process_dict(data_dict, "location")
        item['atm_type'] = self.process_dict(data_dict, "atm_type")
        item['description'] = self.process_dict(data_dict, "description")
        item['conditions_for_participation'] = self.process_dict(data_dict, "conditions_for_participation")
        item['timeframe_for_delivery'] = self.process_dict(data_dict, "timeframe_for_delivery")
        item['address_for_lodgement'] = self.process_dict(data_dict, "address_for_lodgement")
        item['addenda_available'] = self.process_dict(data_dict, "addenda_available")

        item['contact_name'] = self.process_dict(data_dict, "contact_name")
        item['contact_phone'] = self.process_dict(data_dict, "contact_phone")
        item['contact_mobile'] = self.process_dict(data_dict, "contact_mobile")
        item['contact_email'] = self.process_dict(data_dict, "contact_email")

        return item

    def login(self, url_path):

        login_url = WEB_SITE_URL + url_path
        sessiona = requests.Session()
        headers_login = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            "Origin": "https://www.tenders.gov.au",
        }

        login_response = sessiona.get(login_url, headers=headers_login)
        post_cookie = login_response.cookies.get_dict()

        soup = BeautifulSoup(login_response.content, 'lxml')
        _xsrf = soup.find("input", attrs={'name': 'CSRFtoken'}).get('value')
        redirect_string = soup.find("input", attrs={'name': 'redirectString'}).get('value')

        time.sleep(1)
        # print(_xsrf)
        # print(redirect_string)

        data = {
            "redirectString": url_path,
            "CSRFtoken": ' ' + post_cookie.get('CTK'),
            "pub-auth-username": "xiexinliangwang@gmail.com",
            'pub-auth-password': "HELIWEI1987!"
        }

        headers_login_post = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.tenders.gov.au",
        }

        # print(data)
        resp = requests.post("https://www.tenders.gov.au/?event=public.login", urlencode(data), cookies=post_cookie,
                             headers=headers_login_post, allow_redirects=False)

        # cookie_url = resp.cookies.get("UR_L")
        # self.db_redis.setex('login-cookie', 300, cookie_url)

        return resp.cookies.get_dict()

        # if (self.db_redis.get("login-cookie") != None):
        #
        #     data = {
        #         'UR_L': self.db_redis.get("login-cookie")
        #     }
        #     return data
        #     pass
        #
        # else:
        #
        #     return ""

        pass

    def process_atms_document(self, data_dict):
        item = JshCrawlItem()
        item['type'] = SPIDER_ATM_DOCUMENT_TYPE
        item['version'] = self.process_dict(data_dict, "version")

        item['atm_id'] = self.process_dict(data_dict, "atm_id")
        item['document_list'] = self.process_dict(data_dict, "document_list")

        return item

    # 处理字典数据，如果存在则取出，不存在返回空
    def process_dict(self, data, key):
        if (data.get(key, 'none') != 'none'):
            return data.get(key)
        else:
            return ""
        pass
