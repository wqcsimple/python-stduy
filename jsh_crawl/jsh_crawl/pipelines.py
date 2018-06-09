# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import logging
import os

import pytz
from dateutil.parser import parse
import pymongo
import pymysql
from datetime import datetime
import hashlib
from time import time, sleep
import redis
import requests
from time import mktime, time


# MYSQL_HOST = "db"
# MYSQL_USER = "root"
# MYSQL_PASSWORD = "dd@zju"
# MYSQL_DB = "jsk_crawl"
#
# REDIS_HOST = "redis"
# REDIS_PORT = 6379
# REDIS_PASS = "5WSZZ86WvQIenkyTP6fHAZUio1OzcEb"


class JshCrawlPipeline(object):

    STATUS_INIT = 0

    def open_spider(self, spider):
        # mysql
        self.mysql_connection = None
        self.db_redis = None
        with open(os.getcwd() + "/config.json", "r") as config_file:
            config = json.load(config_file)
            self.mysql_connection = pymysql.connect(host=config['mysql_host'],
                                                    user=config['mysql_user'],
                                                    password=config['mysql_password'],
                                                    db=config['mysql_db'],
                                                    charset='utf8mb4',
                                                    cursorclass=pymysql.cursors.DictCursor)

            self.db_redis = redis.StrictRedis(host=config['redis_host'],
                                              port=config['redis_port'],
                                              db=0,
                                              password=config['redis_pass'])

        pass

    def process_item(self, item, spider):
        type = item['type']
        if (type == 1): # atm
            print("=============== process atm")
            self.process_atms_spider(item, spider)

        elif (type == 2): # son
            print("=============== process son")
            self.process_son_spider(item, spider)

        elif (type == 3): # cn
            print("=============== process cn")
            self.process_cn_spider(item, spider)

        elif (type == 4): # atm document
            print("=============== process atm document")
            self.process_atm_document_spider(item, spider)

        return item

    def process_atms_spider(self, item, spider):
        data = {
            'atm_title':                        item['atm_title'],
            'atm_id':                           item['atm_id'],
            'agency':                           item['agency'],
            'category':                         item['category'],
            'close_date_time':                  self.time_format(item['close_date_time'], '%d-%b-%Y %I:%M %p'),
            'publish_date':                     self.time_format(item['publish_date'], "%d-%b-%Y"),
            'location':                         item['location'],
            'atm_type':                         item['atm_type'],
            'description':                      item['description'],
            'conditions_for_participation':     item['conditions_for_participation'],
            'timeframe_for_delivery':           item['timeframe_for_delivery'],
            'address_for_lodgement':            item['address_for_lodgement'],
            'contact_name':                     item['contact_name'],
            'contact_phone':                    item['contact_phone'],
            'contact_mobile':                   item['contact_mobile'],
            'contact_email':                    item['contact_email'],
        }

        type = item['type']
        hash = hashlib.md5(json.dumps(data).encode('utf-8')).hexdigest()
        status = self.STATUS_INIT
        crawl_version = item['version']

        self.save_data_to_spider_data_table(type, crawl_version, hash, data, status)

        opportunity_id = self.find_opportunity_id_by_atm_id(data['atm_id'])

        now_time = self.time_now()
        state = "OPEN"
        if (now_time > data['close_date_time']):
            state = "CLOSED"

        with self.mysql_connection.cursor() as cursor:
            if (opportunity_id > 0):
                sql = "UPDATE `opportunities` SET `x` = %s, `x_title` = %s, `x_no` = %s, `agency` = %s, `published` = %s, `closing_on` = %s, `remarks` = %s, `procurement_category` = %s, `state` = %s WHERE id = %s"
                cursor.execute(sql, (
                    data['atm_type'],
                    data['atm_title'],
                    data['atm_id'],
                    data['agency'],
                    data['publish_date'],
                    data['close_date_time'],
                    data['description'],
                    data['category'],
                    state,
                    opportunity_id
                ))

            else:
                sql = "INSERT INTO `opportunities`(`x`, `x_title`, `x_no`, `agency`, `published`, `closing_on`, `remarks`, `procurement_category`, `state`, `update_time`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (
                    data['atm_type'],
                    data['atm_title'],
                    data['atm_id'],
                    data['agency'],
                    data['publish_date'],
                    data['close_date_time'],
                    data['description'],
                    data['category'],
                    state,
                    self.time_now()
                ))

            self.mysql_connection.commit()

            opportunity_id = self.find_opportunity_id_by_atm_id(data['atm_id'])
            if (opportunity_id > 0):
                # person 联系人和代理人信息表
                person_id = self.find_person_id_by_opportunity_id(opportunity_id)
                if (person_id > 0):
                    sql_update_person = "UPDATE `person` SET `name` = %s, `mail` = %s, `telephone` = %s, `mobilephone` = %s, `address` = %s WHERE `opportunity_id` = %s"
                    cursor.execute(sql_update_person, (
                        data['contact_name'],
                        data['contact_email'],
                        data['contact_phone'],
                        data['contact_mobile'],
                        data['address_for_lodgement'],
                        opportunity_id
                    ))

                else:
                    sql_insert_person = "INSERT INTO `person` (`opportunity_id`, `name`, `mail`, `telephone`, `address`) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql_insert_person, (
                        opportunity_id,
                        data['contact_name'],
                        data['contact_email'],
                        data['contact_phone'],
                        data['address_for_lodgement']
                    ))

                self.mysql_connection.commit()

            delivery_information_id = self.find_delivery_information_id(data['location'], data['timeframe_for_delivery'])
            if (delivery_information_id > 0):
                sql_update_delivery_information = "UPDATE `delivery_information` SET `location` = %s, `delivery_date` = %s WHERE id = %s"
                cursor.execute(sql_update_delivery_information, (
                    data['location'],
                    data['timeframe_for_delivery'],
                    delivery_information_id
                ))
            else:
                sql_insert_delivery_information = "INSERT INTO `delivery_information` (`location`, `delivery_date`) VALUES (%s, %s)"
                cursor.execute(sql_insert_delivery_information, (
                    data['location'].strip(),
                    data['timeframe_for_delivery']
                ))

            self.mysql_connection.commit()
        pass

    def process_son_spider(self, item, spider):
        data = {
            'son_title':                item['son_title'],
            'son_id':                   item['son_id'],
            'description':              item['description'],
            'atm_id':                   item['atm_id'],
            'supplier':                 item['supplier'],
        }

        type = item['type']
        hash = hashlib.md5(json.dumps(data).encode('utf-8')).hexdigest()
        status = self.STATUS_INIT
        crawl_version = item['version']

        self.save_data_to_spider_data_table(type, crawl_version, hash, data, status)

        # get opportunities by atm_id
        opportunity = self.find_opportunity_by_atm_id(data['atm_id'])
        opportunity_id = 0
        opportunity_state = None
        if (opportunity != None):
            opportunity_id = opportunity.get('id')
            opportunity_state = opportunity.get('state')

        with self.mysql_connection.cursor() as cursor:

            # 如果能查找到，先更新opportunity状态, 如果没有先用该atm_id生成一条opportunity记录
            if (opportunity_id > 0 and opportunity_state == 'OPEN'):
                sql_update_opportunity_state = "UPDATE `opportunities` SET `state` = %s, `update_time` = %s WHERE id = %s"
                cursor.execute(sql_update_opportunity_state,
                               ("PENDING AWARD", self.time_now(), opportunity_id))

            else:
                if (data['atm_id'] != ''):
                    sql_insert_opportunity = "INSERT INTO `opportunities` (`x_no`, `state`, `update_time`) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insert_opportunity,
                                   (data['atm_id'], "PENDING AWARD", self.time_now()))

            self.mysql_connection.commit()
            sleep(1)

            opportunity_id = self.find_opportunity_id_by_atm_id(data['atm_id'])

            # insert respondents 提交报价人列表
            sql = "INSERT INTO `respondents` (`resource_son_id`, `resource_atm_id`, `company_name`) VALUES (%s, %s, %s)"
            if (opportunity_id > 0):
                sql = "INSERT INTO `respondents` (`opportunity_id`, `resource_son_id`, `resource_atm_id`, `company_name`) VALUES (%s, %s, %s, %s)"
            if (len(item['supplier']) > 0):
                for supplier_item in item['supplier']:

                    logging.info("supplier item:  " + supplier_item)

                    respondents_id = self.find_respondents_id_by_company_name(data['son_id'], supplier_item)
                    # 没有respondents记录
                    if (respondents_id <= 0):
                        if (opportunity_id > 0):
                            cursor.execute(sql, (opportunity_id, data['son_id'], data['atm_id'], supplier_item))
                        else:
                            cursor.execute(sql, (data['son_id'], data['atm_id'], supplier_item))

                        self.mysql_connection.commit()

                        respondent_id = self.find_respondent_id_by_company_name(data['son_id'], supplier_item)

                        if (respondent_id > 0):
                            sql_insert_respondent_item = "INSERT INTO `respondent_items` (`respondent_id`, `resource_son_id`, `name`) VALUES (%s, %s, %s)"
                            cursor.execute(sql_insert_respondent_item,
                                           (respondent_id, data['son_id'], data['son_title']))

                            self.mysql_connection.commit()


            respondent_item_bids_id = self.find_respondent_item_bids_id_by_son_id(data['son_id'])
            if (respondent_item_bids_id <= 0):
                sql_insert_respondent_item_bids = "INSERT INTO `respondent_item_bids` (`resource_son_id`, `remarks`) values (%s, %s)"
                cursor.execute(sql_insert_respondent_item_bids,
                               (data['son_id'], data['description']))

                self.mysql_connection.commit()

            else:
                sql_update_respondent_item_bids = "UPDATE `respondent_item_bids` SET `remarks` = %s WHERE `resource_son_id` = %s"
                cursor.execute(sql_update_respondent_item_bids,
                               (data['description'], data['son_id']))

                self.mysql_connection.commit()

        pass

    def process_cn_spider(self, item, spider):
        data = {
            'cn_title':                 item['cn_title'],
            'cn_id':                    item['cn_id'].strip(),
            'atm_id':                   item['atm_id'],
            'agency':                   item['agency'],
            'contract_period':          self.time_format(item['contract_period'].strip().split("to")[0], "%d-%b-%Y"),
            'contract_value':           item['contract_value'],
            'procurement_method':       item['procurement_method'],
            'cn_name':                  item['cn_name'],
            'cn_address':               item['cn_address']
        }

        type = item['type']
        hash = hashlib.md5(json.dumps(data).encode('utf-8')).hexdigest()
        status = self.STATUS_INIT
        crawl_version = item['version']

        self.save_data_to_spider_data_table(type, crawl_version, hash, data, status)

        # get opportunities by atm_id
        opportunity = self.find_opportunity_by_atm_id(data['atm_id'])
        opportunity_id = 0
        opportunity_state = None
        if (opportunity != None):
            opportunity_id = opportunity.get("id")
            opportunity_state = opportunity.get('state')
            pass

        with self.mysql_connection.cursor() as cursor:

            if (opportunity_id > 0):
                sql_update_opportunity = "UPDATE `opportunities` SET `state` = %s, `update_time` = %s WHERE id = %s"
                cursor.execute(sql_update_opportunity,
                               ("AWARDED", self.time_now(), opportunity_id))

            else:
                if (data['atm_id'] != ''):
                    sql_insert_opportunity = "INSERT INTO `opportunities` (`resource_cn_id`, `x_no`, `state`, `update_time`) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql_insert_opportunity,
                                   (data['cn_id'], data['atm_id'], "AWARDED", self.time_now()))

                else:

                    sql_insert_opportunity = "INSERT INTO `opportunities` (`resource_cn_id`, `state`, `update_time`) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insert_opportunity,
                                   (data['cn_id'], "AWARDED", self.time_now()))

                    pass

            self.mysql_connection.commit()
            sleep(1)

            opportunity_id = self.find_opportunity_id_by_resource_cn_id(data['cn_id'])

            if opportunity_id == None:
                opportunity_id = 0

            # 1. 获奖代理人及获奖信息
            awarding_agencies_id = self.find_awarding_agencies_by_cn_id(data['cn_id'])
            if (awarding_agencies_id > 0):
                sql_update_awarding_agencies = "UPDATE `awarding_agencies` SET `opportunity_id` = %s, `resource_atm_id` = %s,  `name` = %s, `no_of_suppliers_awarded` = %s, `awarded_date` = %s, `total_awarded_value` = %s, `procurement_method` = %s WHERE resource_cn_id = %s"
                cursor.execute(sql_update_awarding_agencies, (
                    opportunity_id,
                    data['atm_id'],
                    data['agency'],
                    1,
                    data['contract_period'],
                    data['contract_value'],
                    data['procurement_method'],
                    data['cn_id']
                ))

            else:
                sql_insert_awarding_agencies = "INSERT INTO `awarding_agencies` (`opportunity_id`, `resource_cn_id`, `resource_atm_id`, `name`, `no_of_suppliers_awarded`, `awarded_date`, `total_awarded_value`, `procurement_method`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql_insert_awarding_agencies, (
                    opportunity_id,
                    data['cn_id'],
                    data['atm_id'],
                    data['agency'],
                    1,
                    data['contract_period'],
                    data['contract_value'],
                    data['procurement_method']
                ))

            self.mysql_connection.commit()

            # 2. 获奖人信息表
            awarded_to_id = self.find_awarded_to_id_by_cn_id(data['cn_id'])

            if (awarded_to_id > 0):
                sql_update_awarded_to = "UPDATE `awarded_to` SET `opportunity_id` = %s, `company_name` = %s, `address` = %s, `awarded_value` = %s WHERE `resource_cn_id` = %s"
                cursor.execute(sql_update_awarded_to, (
                    opportunity_id,
                    data['cn_name'],
                    data['cn_address'],
                    data['contract_value'],
                    data['cn_id']
                ))

            else:
                sql_insert_awarded_to = "INSERT INTO `awarded_to` (`opportunity_id`, `resource_cn_id`, `company_name`, `address`, `awarded_value`) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_insert_awarded_to, (
                    opportunity_id,
                    data['cn_id'].strip(),
                    data['cn_name'],
                    data['cn_address'],
                    data['contract_value']
                ))

            self.mysql_connection.commit()

            sleep(2)
            awarded_to_id = self.find_awarded_to_id_by_cn_id(data['cn_id'])

            if (awarded_to_id > 0):
                awarded_id = self.find_awarded_item_id(awarded_to_id)
                if (awarded_id > 0):
                    sql_update_awarded_item = "UPDATE `awarded_item` SET `name` = %s, `awarded_value` = %s WHERE `awarded_to_id` = %s"
                    cursor.execute(sql_update_awarded_item, (
                        data['cn_title'],
                        data['contract_value'],
                        awarded_to_id
                    ))

                else:
                    sql_insert_awarded_item = "INSERT INTO `awarded_item` (`awarded_to_id`, `name`, `awarded_value`) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insert_awarded_item, (
                        awarded_to_id,
                        data['cn_title'],
                        data['contract_value']
                    ))

            self.mysql_connection.commit()

        pass

    # 处理atm文档
    def process_atm_document_spider(self, item, spider):
        data = {
            'atm_id': item['atm_id'],
            'document_list': item['document_list'],
        }

        type = item['type']
        hash = hashlib.md5(json.dumps(data).encode('utf-8')).hexdigest()
        status = self.STATUS_INIT
        crawl_version = item['version']

        self.save_data_to_spider_data_table(type, crawl_version, hash, data, status)

        # get opportunities by atm_id
        opportunity_id = self.find_opportunity_id_by_atm_id(item['atm_id'])

        print("whis-0")
        print(opportunity_id)
        with self.mysql_connection.cursor() as cursor:

            if (opportunity_id > 0):

                # 将附件地址存入到documents表
                sql = "INSERT INTO `documents`( `opportunity_id`, `name`, `hash`, `file_path`) VALUES (%s, %s, %s, %s)"
                for document in item['document_list']:
                    dir_path = "./files/" + data['atm_id']
                    file_path = dir_path + "/" + document['title']

                    print('whis-1')
                    if (os.path.isfile(file_path) == True):
                        document_id = self.find_document_id_by_file_name(opportunity_id, document['title'])
                        if (document_id <= 0):
                            hash = self.md5_file(file_path)

                            true_file_path = data['atm_id'] + '/' + document['title']
                            cursor.execute(sql, (opportunity_id, document['title'], hash, true_file_path))
                            self.mysql_connection.commit()
        pass

    # 爬虫关闭
    def close_spider(self, spider):
        self.mysql_connection.close()


    # 将数据线存入到爬虫数据表
    def save_data_to_spider_data_table(self, type, crawl_version, hash, data, status):
        create_time = self.time_now()
        with self.mysql_connection.cursor() as cursor:
            # 1. 插入到spider_data 数据表
            sql_insert_data = "INSERT INTO `spider_data` (`type`, `crawl_version`, `hash`, `data`, `status`, `create_time`) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql_insert_data, (type, crawl_version, hash, str(json.dumps(data)), status, create_time))

            self.mysql_connection.commit()
        pass

    # 根据atm_id 获取opportunity_id
    def find_opportunity_id_by_atm_id(self, atm_id):
        opportunity_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `opportunities` WHERE `x_no` = %s limit 0, 1"
            cursor.execute(sql, (atm_id))
            db_opportunities = cursor.fetchone()

            if (db_opportunities != None):
                opportunity_id = db_opportunities.get('id')

        logging.info("opportunity_id: %s", opportunity_id)
        return opportunity_id
        pass

    def find_opportunity_id_by_resource_cn_id(self, cn_id):
        opportunity_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `opportunities` WHERE `resource_cn_id` = %s limit 0, 1"
            cursor.execute(sql, (cn_id))
            db_opportunities = cursor.fetchone()

            if (db_opportunities != None):
                opportunity_id = db_opportunities.get('id')

        logging.info("opportunity_id: %s", opportunity_id)
        return opportunity_id
        pass

    def find_opportunity_by_atm_id(self, atm_id):
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `opportunities` WHERE `x_no` = %s limit 0, 1"
            cursor.execute(sql, (atm_id))
            db_opportunities = cursor.fetchone()

        return db_opportunities
        pass

    def find_respondents_id_by_company_name(self, son_id, company_name):
        respondents_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM respondents WHERE resource_son_id = %s and company_name = %s limit 0, 1"
            cursor.execute(sql, (son_id, company_name))
            db_respondents = cursor.fetchone()

            if (db_respondents != None):
                respondents_id = db_respondents.get("id")

        logging.info("respondents_id: %s", respondents_id)
        return respondents_id
        pass

    def find_person_id_by_opportunity_id(self, opportunity_id):
        person_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `person` WHERE `id` = %s limit 0, 1"
            cursor.execute(sql, (opportunity_id))
            db_person = cursor.fetchone()

            if (db_person != None):
                person_id = db_person.get("id")

        logging.info("person_id: %s", person_id)
        return person_id
        pass

    # 根据company_name 获取respondent_id
    def find_respondent_id_by_company_name(self, son_id, company_name):
        respondent_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `respondents` WHERE `resource_son_id` = %s AND `company_name` = %s limit 0, 1"
            cursor.execute(sql, (son_id, company_name))
            db_respondent = cursor.fetchone()

            if (db_respondent != None):
                respondent_id = db_respondent.get('id')

        logging.info("respondent_id: %s", respondent_id)
        return respondent_id
        pass

    def find_respondent_items_id_by_son_id(self, resource_son_id):
        respondent_item_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `respondent_items` WHERE `resource_son_id` = %s limit 0, 1"
            cursor.execute(sql, (resource_son_id))
            db_respondent_item_bids = cursor.fetchone()

            if (db_respondent_item_bids != None):
                respondent_item_id = db_respondent_item_bids.get("id")

        logging.info("respondent_item_id: %s", respondent_item_id)
        return respondent_item_id
        pass


    def find_respondent_item_bids_id_by_son_id(self, resource_son_id):
        respondent_item_bids_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `respondent_item_bids` WHERE `resource_son_id` = %s limit 0, 1"
            cursor.execute(sql, (resource_son_id))
            db_respondent_item_bids = cursor.fetchone()

            if (db_respondent_item_bids != None):
                respondent_item_bids_id = db_respondent_item_bids.get("id")

        logging.info("respondent_item_bids_id: %s", respondent_item_bids_id)
        return respondent_item_bids_id
        pass

    # 根据cn_id 获取 awarded_to_id
    def find_awarded_to_id_by_cn_id(self, cn_id):
        awarded_to_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `awarded_to` WHERE `resource_cn_id` = %s limit 0, 1"
            cursor.execute(sql, (cn_id))
            db_awarded_to = cursor.fetchone()

            if (db_awarded_to != None):
                awarded_to_id = db_awarded_to.get("id")

        logging.info("awarded_to_id: %s", awarded_to_id)
        return awarded_to_id
        pass

    def find_awarding_agencies_by_cn_id(self, cn_id):
        awarding_agencies_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `awarding_agencies` WHERE `resource_cn_id` = %s limit 0, 1"
            cursor.execute(sql, (cn_id))
            db_awarded_to = cursor.fetchone()

            if (db_awarded_to != None):
                awarding_agencies_id = db_awarded_to.get("id")

        logging.info("awarding_agencies_id: %s", awarding_agencies_id)
        return awarding_agencies_id
        pass

    def find_awarded_item_id(self, awarded_to_id):
        awarded_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `awarded_item` WHERE `awarded_to_id` = %s"
            cursor.execute(sql, (awarded_to_id))
            db_awarded_item = cursor.fetchone()

            if (db_awarded_item != None):
                awarded_id = db_awarded_item.get("id")

        logging.info("awarded_id: %s", awarded_id)
        return awarded_id
        pass

    def find_delivery_information_id(self, location, delivery_date):
        delivery_information_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `delivery_information` WHERE `location` = %s and `delivery_date` = %s"
            cursor.execute(sql, (location, delivery_date))
            db_delivery_information = cursor.fetchone()

            if (db_delivery_information != None):
                delivery_information_id = db_delivery_information.get("id")

        logging.info("delivery_information_id: %s", delivery_information_id)
        return delivery_information_id
        pass

    def check_spider_data_by_hash(self, hash):
        result = False
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `spider_data` WHERE `hash` = %s ORDER BY create_time DESC"
            cursor.execute(sql, (hash))
            db_spider_data = cursor.fetchone()

            if (db_spider_data != None):
                result = True

        return result

    def find_document_id_by_file_name(self, atm_id, file_name):
        document_id = 0
        with self.mysql_connection.cursor() as cursor:
            sql = "SELECT * FROM `documents` WHERE `opportunity_id` = %s AND `name` = %s"
            cursor.execute(sql, (atm_id, file_name))
            db_document = cursor.fetchone()

            if (db_document != None):
                document_id = db_document.get("id")

        logging.info("document_id: %s", document_id)
        return document_id

    @classmethod
    def time_format(self, str, fmt):
        tz_shanghai = pytz.timezone('Asia/Shanghai')
        tz_sydney = pytz.timezone('Australia/Sydney')
        str = str.strip()
        if (str == ''):
            return ''

        t = parse(str, fuzzy=True)
        loc_t = tz_sydney.localize(t)

        china_t = loc_t.astimezone(tz_shanghai)

        return china_t.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def time_now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def md5_file(self, name):
        m = hashlib.md5()
        a_file = open(name, 'rb')  # 使用二进制格式读取文件内容
        m.update(a_file.read())
        a_file.close()
        return m.hexdigest()


