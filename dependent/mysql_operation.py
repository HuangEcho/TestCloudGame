import pymysql


class MysqlOperation(object):
    def connect_mysql(self, mysql_env):
        db = pymysql.Connect(
            host=mysql_env["host"],
            port=mysql_env["port"],
            user=mysql_env["user"],
            password=mysql_env["password"],
            database=mysql_env["database"]
        )
        return db

    # 修改数据库
    def commit_mysql(self, db, sql):
        cursor = db.cursor()
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.roolback()

    def query_mysql(self, db, sql):
        cursor = db.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        return res

    def close_mysql(self, db):
        db.close()
