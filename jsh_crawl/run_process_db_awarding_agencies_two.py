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
            sql_select_aa = "SELECT * FROM `awarding_agencies` WHERE resource_atm_id != '' AND opportunity_id is null"
            cursor.execute(sql_select_aa)
            db_awarding_agencies_list = cursor.fetchall()

            for db_awarding_agencies in db_awarding_agencies_list:
                cn_id = db_awarding_agencies.get('resource_cn_id').strip()
                atm_id = db_awarding_agencies.get('resource_atm_id').strip()

                opportunity_id = 0
                sql_select_opportunities_by_cn_id = "SELECT * FROM `opportunities` WHERE resource_cn_id = %s"
                cursor.execute(sql_select_opportunities_by_cn_id, (cn_id))
                db_opportunities = cursor.fetchone()

                if (db_opportunities == None):
                    sql_select_opportunities_by_atm_id = "SELECT * FROM `opportunities` WHERE `x_no` = %s"
                    cursor.execute(sql_select_opportunities_by_atm_id, (atm_id))
                    db_opportunities = cursor.fetchone()

                if (db_opportunities != None):
                    opportunity_id = db_opportunities.get("id")

                print("opportunity_id: ", opportunity_id)
                if (opportunity_id > 0):

                    sql_update_aa = "update `awarding_agencies` set `opportunity_id` = %s where `resource_cn_id` = %s"
                    cursor.execute(sql_update_aa, (opportunity_id, cn_id))
                    mysql_connection.commit()

                else:

                    sql_insert_opp = "INSERT INTO `opportunities` (`resource_cn_id`, `x_no`, `state`, `update_time`) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql_insert_opp,
                                   (cn_id, atm_id, "CLOSED", time_now()))
                    mysql_connection.commit()

    finally:
        mysql_connection.close()


    pass

def time_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    start()