import config

from flask import Flask
from sqlalchemy import create_engine
from flask_cors import CORS

from view import create_endpoints
from model import *
from service import *


'''
Default JSON encoder는 set을 JSON으로 변환할 수 없다.
그러므로 커스텀 엔코더를 작성해서 set을 list로 변환하여 JSON으로 변환가능하게 해주어야 한다.
'''


# Flask가 create_app 이라는 이름의 함수를 자동으로 팩토리(Factory) 함수로 인식해서 해당 함수를 통해 Flask를 실행한다.
# test_config 파라미터를 받는 이유는 단위 테스트 할 때, 테스트용 데이터베이스 등의 테스트 설정 정보를 적용하기 위함이다.
# test_config가 None이면 config.py 파일에서 설정을 읽어 들인다. test_config 인자가 None이 아니라면 해당 설정을 적용시킨다.
# current_app은 create_app 함수에서 생성한 app 변수를 create_app 함수 외부에서도 사용할 수 있게 해준다.

class Services:
    # service class 들을 담고 있을 class 이다.
    pass


################################
# Create App
################################
def create_app(test_config=None):
    app = Flask(__name__)

    CORS(app)

    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)

    database = create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0)

    # Persistenace Layer
    user_dao = UserDao(database)
    tweet_dao = TweetDao(database)

    # Business Layer
    services = Services
    services.user_service = UserService(user_dao, config)
    services.tweet_service = TweetService(tweet_dao)

    # 엔드포인트 생성
    create_endpoints(app, services)

    return app
