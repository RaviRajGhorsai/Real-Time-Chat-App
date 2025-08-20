import pymysql
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

pymysql.install_as_MySQLdb()