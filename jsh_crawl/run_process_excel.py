import json
import os
from datetime import datetime, date

from time import sleep
import logging
import pymysql
import sys
import xlrd

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def open_excel(file=""):
    try:
        data = xlrd.open_workbook(file)
        return data
    except Exception:
        print("open file fail or file not exists")

    pass

def excel_table_by_index(file="", row_index_start=0, col_name_index=0, by_index=0):
    excel_data = open_excel(file)
    table = excel_data.sheet_by_index(by_index)

    nrows = table.nrows  # 行数
    ncols = table.ncols  # 列数
    colnames = table.row_values(col_name_index)  # 某一行数据

    list = []

    for row_num in range(row_index_start, nrows):
        row = table.row(row_num)

        if row:
            list.append(row)

    return list
    pass


def start():
    file_path = "./excel/all_agencies2016_origin.xls"
    # file_path = "./excel/all_agencies2016.xls"

    if (os.path.isfile(file_path) == False):
        logging.error("file not exists")

    else:

        tables = excel_table_by_index(file_path, 11)

        with open(os.getcwd() + "/config.json", "r") as config_file:
            config = json.load(config_file)
            mysql_connection = pymysql.connect(host=config['mysql_host'],
                                               user=config['mysql_user'],
                                               password=config['mysql_password'],
                                               db=config['mysql_db'],
                                               charset='utf8mb4',
                                               cursorclass=pymysql.cursors.DictCursor)

        try:
            for row in tables:
                # print(row)

                cn_id = row[1].value
                cn_agency = row[0].value
                cn_supplier_name = row[2].value
                cn_description = row[4].value
                cn_category = row[5].value
                cn_start_date = ""
                if (row[11].ctype == 3):
                    date_value = xlrd.xldate_as_tuple(row[11].value, 0)
                    cn_start_date = date(*date_value[:3]).strftime('%Y-%m-%d %H:%M:%S')

                cn_closing_on = ""
                if (row[13].ctype == 3):
                    closing_date_value = xlrd.xldate_as_tuple(row[13].value, 0)
                    cn_closing_on = date(*closing_date_value[:3]).strftime('%Y-%m-%d %H:%M:%S')

                cn_value = row[14].value

                print("=================")
                print(cn_id)
                # print(cn_id, cn_agency, cn_supplier_name, cn_description, cn_start_date, cn_value)
                print("=================")

                opportunity_id = 0
                with mysql_connection.cursor() as cursor:
                    sql = "SELECT * FROM `opportunities` WHERE `resource_cn_id` = %s limit 0, 1"
                    cursor.execute(sql, (cn_id))
                    db_opportunities = cursor.fetchone()

                    if (db_opportunities != None):
                        opportunity_id = db_opportunities.get('id')

                    if (opportunity_id <= 0):
                        state = "CLOSED"
                        insert_opportunities_sql = "INSERT INTO `opportunities`(`resource_cn_id`, `agency`, `published`, `closing_on`, `procurement_category`, `state`) VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(insert_opportunities_sql, (
                            cn_id,
                            cn_agency,
                            cn_start_date,
                            cn_closing_on,
                            cn_category,
                            state
                        ))
                        mysql_connection.commit()

                    # sleep(1)
                    cursor.execute(sql, (cn_id))
                    db_opportunities = cursor.fetchone()

                    if (db_opportunities != None):
                        opportunity_id = db_opportunities.get('id')

                print("opportunity_id", opportunity_id)

                if (opportunity_id > 5600):

                    db_awarding_agencies = None
                    with mysql_connection.cursor() as cursor:

                        sql = "SELECT * FROM `awarding_agencies` WHERE `resource_cn_id` = %s limit 0, 1"
                        cursor.execute(sql, (cn_id))
                        db_awarding_agencies = cursor.fetchone()

                    with mysql_connection.cursor() as cursor:

                        if (db_awarding_agencies != None):
                            sql_update_awarding_agencies = "UPDATE `awarding_agencies` SET `opportunity_id` = %s, `name` = %s, `awarded_date` = %s, `total_awarded_value` = %s WHERE resource_cn_id = %s"
                            cursor.execute(sql_update_awarding_agencies, (
                                opportunity_id,
                                cn_agency,
                                cn_start_date,
                                cn_value,
                                cn_id
                            ))

                        else:
                            sql_insert_awarding_agencies = "INSERT INTO `awarding_agencies` (`opportunity_id`, `resource_cn_id`, `name`, `awarded_date`, `total_awarded_value`) VALUES (%s, %s, %s, %s, %s)"
                            cursor.execute(sql_insert_awarding_agencies, (
                                opportunity_id,
                                cn_id,
                                cn_agency,
                                cn_start_date,
                                cn_value
                            ))

                        mysql_connection.commit()

                    awarded_to_id = 0
                    with mysql_connection.cursor() as cursor:
                        sql = "SELECT * FROM `awarded_to` WHERE `resource_cn_id` = %s limit 0, 1"
                        cursor.execute(sql, (cn_id))
                        db_awarded_to = cursor.fetchone()

                        if (db_awarded_to != None):
                            awarded_to_id = db_awarded_to.get("id")

                    with mysql_connection.cursor() as cursor:

                        if (awarded_to_id > 0):
                            sql_update_awarded_to = "UPDATE `awarded_to` SET `opportunity_id` = %s, `company_name` = %s, `awarded_value` = %s WHERE `resource_cn_id` = %s"
                            cursor.execute(sql_update_awarded_to, (
                                opportunity_id,
                                cn_supplier_name,
                                cn_value,
                                cn_id
                            ))

                        else:

                            sql_insert_awarded_to = "INSERT INTO `awarded_to` (`opportunity_id`, `resource_cn_id`, `company_name`, `awarded_value`) VALUES (%s, %s, %s, %s)"
                            cursor.execute(sql_insert_awarded_to, (
                                opportunity_id,
                                cn_id,
                                cn_supplier_name,
                                cn_value
                            ))

                        mysql_connection.commit()

                    # sleep(1)
                    awarded_to_id = 0
                    with mysql_connection.cursor() as cursor:
                        sql = "SELECT * FROM `awarded_to` WHERE `resource_cn_id` = %s limit 0, 1"
                        cursor.execute(sql, (cn_id))
                        db_awarded_to = cursor.fetchone()

                        if (db_awarded_to != None):
                            awarded_to_id = db_awarded_to.get("id")

                    with mysql_connection.cursor() as cursor:
                        if (awarded_to_id > 0):
                            awarded_id = 0
                            sql = "SELECT * FROM `awarded_item` WHERE `awarded_to_id` = %s"
                            cursor.execute(sql, (awarded_to_id))
                            db_awarded_item = cursor.fetchone()

                            if (db_awarded_item != None):
                                awarded_id = db_awarded_item.get("id")

                            if (awarded_id > 0):
                                sql_update_awarded_item = "UPDATE `awarded_item` SET `name` = %s, `awarded_value` = %s WHERE `awarded_to_id` = %s"
                                cursor.execute(sql_update_awarded_item, (
                                    cn_description,
                                    cn_value,
                                    awarded_to_id
                                ))

                            else:
                                sql_insert_awarded_item = "INSERT INTO `awarded_item` (`awarded_to_id`, `name`, `awarded_value`) VALUES (%s, %s, %s)"
                                cursor.execute(sql_insert_awarded_item, (
                                    awarded_to_id,
                                    cn_description,
                                    cn_value
                                ))
                            mysql_connection.commit()

                else:
                    print("next")
        finally:
            mysql_connection.close()

    pass


if __name__ == "__main__":
    start()
