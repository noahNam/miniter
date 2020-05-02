# sqlalchemy 모듈에서 필요한 함수들을 import한다. create_engine으로 데이터베이스에 연결하고 text를 사용하여 실행할 SQL을 만든다.
from sqlalchemy import create_engine, text

db = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'port': '3306',
    'database': 'miniter'
}

db_url = f"mysql+mysqlconnector://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}?charset=utf8"
db = create_engine(db_url, encoding='utf-8', max_overflow=0)

params = {'name': '남기혁'}
rows = db.execute(text("select * from users where name = :name"), params).fetchall()

for row in rows:
    print(f"name : {row['name']}")
    print(f"email : {row['email']}")
