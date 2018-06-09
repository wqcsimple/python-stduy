import json
import os
from datetime import datetime

import pymysql


def start():
    with open(os.getcwd() + "/config.json", "r") as config_file:
        config = json.load(config_file)
        mysql_connection = pymysql.connect(host=config['mysql_host'],
                                           user=config['mysql_user'],
                                           password=config['mysql_password'],
                                           db=config['mysql_db'],
                                           charset='utf8mb4',
                                           cursorclass=pymysql.cursors.DictCursor)


    try:
        with mysql_connection.cursor() as cursor:
            sql_select_data = "SELECT * FROM `respondent_item_bids` WHERE respondent_item_id is null"
            cursor.execute(sql_select_data)
            db_respondent_item_bid_list = cursor.fetchall()

            for db_respondent_item_bid in db_respondent_item_bid_list:
                resource_son_id = db_respondent_item_bid.get("resource_son_id", None)

                respondent_items_id = 0
                sql_select_respondent_item = "SELECT * FROM `respondent_items` WHERE resource_son_id = %s limit 0, 1"
                cursor.execute(sql_select_respondent_item, (resource_son_id))
                db_respondent_items = cursor.fetchone()

                if (db_respondent_items != None):
                    respondent_items_id = db_respondent_items.get("id")

                if (respondent_items_id == None):
                    respondent_items_id = 0

                print("respondent_items_id: ", respondent_items_id)

                if (respondent_items_id > 0):
                    sql_update = "UPDATE respondent_item_bids set respondent_item_id  = %s WHERE resource_son_id  = %s"
                    cursor.execute(sql_update, (
                        respondent_items_id,
                        resource_son_id
                    ))
                    mysql_connection.commit()

                pass

        pass
    finally:
        mysql_connection.close()

    pass

def time_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    start()