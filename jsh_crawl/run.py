import logging

from datetime import datetime
import schedule
import time
import sys
import os

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def atm_spider():
    logging.info("===== begin atm spider =======")
    os.system('scrapy crawl atms')
    pass

def son_spider():
    logging.info("===== begin son spider =======")
    os.system('scrapy crawl son')
    pass

def cn_spider():
    logging.info("===== begin cn spider =======")
    os.system('scrapy crawl cn')
    pass

def update_res_item_bid():
    logging.info("===== begin update res item bid =======")
    os.system('python run_update_respondent_item_bids.py')
    pass

def update_awarded_to():
    logging.info("===== begin update awarded to =======")
    os.system('python run_update_awarded_to.py')
    pass

def update_award_agencies():
    logging.info("===== begin update award_agencies =======")
    os.system('python run_process_db_awarding_agencies.py')
    pass

def update_award_agencies_two():
    logging.info("===== begin update award_agencies two =======")
    os.system('python run_process_db_awarding_agencies_two.py')
    pass

def process_awarded_item():
    logging.info("===== begin process awarded_item =======")
    os.system('python run_process_awarded_item.py')
    pass

def first():
    atm_spider()
    son_spider()
    cn_spider()
    # update_res_item_bid()
    # update_awarded_to()
    # update_award_agencies()
    # update_award_agencies_two()

schedule.every(2).hours.do(atm_spider)
schedule.every(2).hours.do(son_spider)
schedule.every(2).hours.do(cn_spider)
schedule.every(5).hours.do(update_res_item_bid)
schedule.every(5).hours.do(update_awarded_to)
schedule.every(6).hours.do(update_award_agencies)
schedule.every(7).hours.do(update_award_agencies_two)
schedule.every(8).hours.do(process_awarded_item)

def run():
    first()
    while True:
        schedule.run_pending()
        time.sleep(1)
    pass

if __name__ == '__main__':
    run()