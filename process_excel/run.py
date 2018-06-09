from datetime import datetime

import pymysql
import xlrd

mysql_connection = pymysql.connect(host='db',
                                       user='root',
                                       password="7",
                                       db="csm",
                                       charset='utf8mb4',
                                       cursorclass=pymysql.cursors.DictCursor)

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


    file_path = "./quick-reply.xls"

    tables = excel_table_by_index(file_path, 11)

    try:
        for row in tables:

            group_name = row[0].value
            title = row[1].value
            content = row[2].value

            with mysql_connection.cursor() as cursor:

                quick_reply_group_id = findQuickReplyGroupId(group_name)

                if (quick_reply_group_id <= 0):
                    sql_insert = "INSERT INTO `quick_reply_group`(`name`) VALUES (%s)"
                    cursor.execute(sql_insert, (group_name))
                    mysql_connection.commit()

                quick_reply_group_id = findQuickReplyGroupId(group_name)

                if (quick_reply_group_id > 0):

                    sql = "INSERT INTO `quick_reply`(`quick_reply_group_id`, `title`, `content`) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (
                        quick_reply_group_id,
                        title,
                        content
                    ))

                    mysql_connection.commit()

                pass

    finally:
        mysql_connection.close()

    pass

def findQuickReplyGroupId(name):
    quick_reply_group_id = 0
    with mysql_connection.cursor() as cursor:
        sql_group = 'SELECT * FROM `quick_reply_group` where name = %s'
        cursor.execute(sql_group, (name))
        db_quick_reply_group = cursor.fetchone()

        if (db_quick_reply_group != None):
            quick_reply_group_id = db_quick_reply_group.get('id')

    return quick_reply_group_id

def time_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    start()