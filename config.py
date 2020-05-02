# sqlalchemy 모듈에서 필요한 함수들을 import한다. create_engine으로 데이터베이스에 연결하고 text를 사용하여 실행할 SQL을 만든다.
from sqlalchemy import create_engine, text

db = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'port': '3306',
    'database': 'miniter'
}

DB_URL = f"mysql+mysqlconnector://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}?charset=utf8"
JWT_SECRET_KEY = 'SOME_SUPER_SECRET_KEY'
JWT_EXP_DELTA_SECONDS = 7 * 24 * 60 * 60


