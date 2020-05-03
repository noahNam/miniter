import config
import pytest
import bcrypt
import json

# app.py파일에서 create_app 함수를 임포트 한다.
from app import create_app
from sqlalchemy import create_engine, text

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)


@pytest.fixture
def api():
    """
     def api() --> fixture 함수 이름. 동일한 이름의 인자를 해당 함수의 리턴 값으로 적용시켜 준다.
     create_app 함수를 사용해서 API 어플리케이션을 생성해 준다.
     app.config['TESTING'] --> Flask가 에러가 났을 경우 HTTP 요청 오류 부분은 핸들링 하지 않음으로써 불필요한 오류 메세지는 출력하지 않는다.
     test_client() --> 테스트용 클라이언트를 생성한다. 테스트용 클라이언트를 사용해서 URI기반으로 원하는 엔드포인트들을 호출할 수 있다.
    """
    app = create_app(config.test_config)
    app.config['TESTING'] = True
    api = app.test_client()

    return api


# 실행 명령어 --> $ pytest -p no:warnings -vv
def test_ping(api):
    """
    test_ --> test 함수로 인식한다.
    api 인자는 pytest.fixture decorator가 적용되어 있는 함수를 찾아서 해당 함수의 리턴값을 인자에 적용시켜 준다.

    api.get('/ping') --> test_client의 get 메소드를 통해서 가상의 GET 요청을 /ping URI와 연결되어 있는 엔드포인트에 보낸다.
    assert b'pong' in resp.data --> resp.data는 스트링이 아니라 byte이므로 byte로 변환해서 비교한다.
    """
    resp = api.get('/ping')
    assert b'pong' in resp.data
