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
            sql_select_data = "SELECT * FROM `awarded_to` WHERE opportunity_id is null"
            cursor.execute(sql_select_data)
            db_awarded_to_list = cursor.fetchall()

            for db_awarded_to in db_awarded_to_list:
                resource_cn_id = db_awarded_to.get("resource_cn_id", None)

                print("cn_id: ", resource_cn_id)

                opportunities_id = 0
                sql_select_opp = "SELECT * FROM `awarding_agencies` WHERE resource_cn_id = %s limit 0,1"
                cursor.execute(sql_select_opp, (resource_cn_id))
                db_awarding_agencies = cursor.fetchone()

                if (db_awarding_agencies != None):
                    opportunities_id = db_awarding_agencies.get("opportunity_id")

                if (opportunities_id == None):
                    opportunities_id = 0

                print("opportunities_id: ", opportunities_id)

                if (opportunities_id > 0):
                    sql_update = "UPDATE awarded_to set opportunity_id = %s where resource_cn_id = %s"
                    cursor.execute(sql_update, (
                        opportunities_id,
                        resource_cn_id
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