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
            sql_select_data = "SELECT * FROM `awarded_item` where `awarded_to_id` is not null"
            cursor.execute(sql_select_data)
            db_awarded_item_list = cursor.fetchall()

            for db_awarded_item in db_awarded_item_list:

                awarded_to_id = db_awarded_item.get("awarded_to_id", 0)
                x_title = db_awarded_item.get("name", "")

                sql_select_awarded_to = "SELECT * FROM `awarded_to` WHERE `id` = %s AND `opportunity_id` is not null"
                cursor.execute(sql_select_awarded_to, (awarded_to_id))
                db_awarded_item = cursor.fetchone()


                if (db_awarded_item != None):
                    opportunity_id = db_awarded_item.get("opportunity_id", 0)

                    sql_select_opportunity = "SELECT * FROM `opportunities` WHERE `id` = %s AND `x_title` is null"
                    cursor.execute(sql_select_opportunity, (opportunity_id))
                    db_opportunity = cursor.fetchone()

                    if (db_opportunity != None):
                        sql_update = "UPDATE `opportunities` SET `x_title` = %s WHERE `id` = %s"
                        cursor.execute(sql_update, (
                            x_title,
                            opportunity_id
                        ))

                        mysql_connection.commit()

                        print("process success: ", opportunity_id)

                        pass

                pass

        pass
    finally:
        mysql_connection.close()

    pass

def time_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    start()