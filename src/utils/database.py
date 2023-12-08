import pymysql
import time
import json
import os


class SqlClient:

    KEYS = ['host', 'user', 'password', 'database', 'port']

    def __init__(self, sqlconf):
        for key in self.KEYS:
            setattr(self, key.lower(), sqlconf[key])
        self._init()

    def _init(self):
        self.conn = pymysql.connect(host=self.host, user=self.user, password=self.password, port=self.port)
        self.cursor = self.conn.cursor()
        with open(os.path.join(os.path.abspath('.'), 'sqls.json'), 'r') as ff:
            self.sqls = json.load(ff)

    def _check_table_exists(self, table_name="auto_prove"):
        self.cursor.execute("show tables;")
        table_list = self.cursor.fetchall()
        try:
            assert (table_name,) in table_list
            return True
        except AssertionError:
            return False

    def _create_table(self, table_name="auto_approve"):
        self.cursor.execute(self.sqls[table_name])
        self.conn.commit()

    def get_approved_list(self):
        sql = self.sqls['approved_list']
        return self._execute(sql)

    def get_someday_approved_list(self, someday):
        sql = self.sqls['approved_one_day'].format(create_date=someday)
        return self._execute(sql)

    def get_today_approved_list(self):
        today = time.strftime("%Y-%m-%d", time.localtime())
        return self.get_someday_approved_list(today)

    def add_new_approved_info(self, **kwargs):
        pass

    def _execute(self, sql):
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result

