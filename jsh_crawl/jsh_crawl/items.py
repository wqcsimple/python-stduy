# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class JshCrawlItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    # 公共参数
    type = Field()   # 1 - atms

    # 第一部分  ATMS字段 start
    atm_title = Field()
    atm_id = Field()
    agency = Field()
    category = Field()
    close_date_time = Field()
    publish_date = Field()
    location = Field()
    atm_type = Field()
    description = Field()
    conditions_for_participation = Field()
    timeframe_for_delivery = Field()
    address_for_lodgement = Field()
    addenda_available = Field()

    # contact_name = Field()
    # contact_phone = Field()
    # contact_email = Field()

    document_list = Field()
    # 第一部分  ATMS字段 end




    # 第二部分 SON字段start
    son_title = Field()
    son_id = Field()
    # agency = Field()
    # publish_date = Field()
    primary_category = Field()
    standing_offer_period = Field()
    title = Field()
    # description = Field()
    procurement_method = Field()
    # atm_id = Field()
    multi_agency_access = Field()
    multi_agency_access_type = Field()
    panel_arrangement = Field()
    agency_reference_id = Field()
    supplier = Field()
    contact_name = Field()
    contact_phone = Field()
    contact_mobile = Field()
    contact_email = Field()
    # 第二部分 SON字段end



    # 第三部分 CN 字段start
    cn_excel_url = Field()
    cn_title = Field()
    cn_id = Field()
    # agency = Field()
    # publish_date = Field()
    # category = Field()
    contract_period = Field()
    contract_value = Field()
    # description = Field()
    # procurement_method = Field()
    # son_id = Field()
    confidentiality_contract = Field()
    confidentiality_outputs = Field()
    consultancy = Field()
    # agency_reference_id = Field()
    cn_name = Field()
    cn_address = Field()
    cn_town = Field()
    cn_postcode = Field()
    cn_state = Field()
    cn_country = Field()
    cn_abn = Field()
    # 第三部分 CN 字段end

    version = Field()


    pass



# CN 参数
class JshCnCrawlItem(scrapy.Item):
    type = Field()
    cn_title = Field()
    cn_id = Field()
    agency = Field()
    publish_date = Field()
    category = Field()
    contract_period = Field()
    contract_value = Field()
    description = Field()
    procurement_method = Field()
    confidentiality_contract = Field()
    confidentiality_outputs = Field()
    consultancy = Field()
    agency_reference_id = Field()
    cn_name = Field()
    cn_address = Field()
    cn_town = Field()
    cn_postcode = Field()
    cn_state = Field()
    cn_country = Field()
    cn_abn = Field()

    pass