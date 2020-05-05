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


def setup_function():
    # Create a test user
    hashed_password = bcrypt.hashpw(b"test", bcrypt.gensalt())
    new_users = [
        {
            'id': 1,
            'name': 'noah',
            'email': 'noah@gmail.com',
            'profile': 'noah profile',
            'hashed_password': hashed_password
        },
        {
            'id': 2,
            'name': 'sinbee',
            'email': 'sinbee@gmail.com',
            'profile': 'sinbee profile',
            'hashed_password': hashed_password
        }
    ]
    database.execute(text("""
        INSERT INTO users (
            id,
            name,
            email,
            profile,
            hashed_password
        ) VALUES (
            :id,
            :name,
            :email,
            :profile,
            :hashed_password
        )
    """), new_users)

    # User 2 의 트윗 미리 생성해 놓기
    database.execute(text("""
        INSERT INTO tweets (
            user_id,
            tweet
        ) VALUES (
            2,
            "I am sinbee!"
        )
    """))


def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))


# 실행 명령어 --> $ pytest -p no:warnings -vv -s
def test_ping(api):
    """
    test_ --> test 함수로 인식한다.
    api 인자는 pytest.fixture decorator가 적용되어 있는 함수를 찾아서 해당 함수의 리턴값을 인자에 적용시켜 준다.

    api.get('/ping') --> test_client의 get 메소드를 통해서 가상의 GET 요청을 /ping URI와 연결되어 있는 엔드포인트에 보낸다.
    assert b'pong' in resp.data --> resp.data는 스트링이 아니라 byte이므로 byte로 변환해서 비교한다.

    json.dumps() : Python 객체를 json 데이터로 쓰기, 직렬화, 인코딩
    json.loads() : json 타입을 Python Dict 형식으로 Convert

    (참고) byte --decode--> str(json type) --json.loads--> python dict
    """
    resp = api.get('/ping')
    assert b'pong' in resp.data


def test_login(api):
    resp = api.post(
        '/login',
        data=json.dumps({
            'email': 'noah@gmail.com',
            'password': 'test'
        }),
        content_type='application/json'
    )
    assert b"access_token" in resp.data


# access token이 없이는 401 응답을 리턴하는지 확인
def test_unahtorize(api):
    resp = api.post(
        '/tweet',
        data=json.dumps({'tweet': "Hello World!"}),
        content_type='application/json'
    )
    assert resp.status_code == 401

    resp = api.post(
        '/follow',
        data=json.dumps({'follow': 2}),
        content_type='application/json'
    )
    assert resp.status_code == 401

    resp = api.post(
        '/unfollow',
        data=json.dumps({'unfollow': 2}),
        content_type='application/json'
    )
    assert resp.status_code == 401


def test_tweet(api):
    # 로그인
    resp = api.post(
        '/login',
        data=json.dumps({
            'email': 'noah@gmail.com',
            'password': 'test'
        }),
        content_type='application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']

    # tweet
    resp = api.post(
        '/tweet',
        data=json.dumps({'tweet': "Hello World!"}),
        content_type='application/json',
        headers={'Authorization': access_token}
    )
    assert resp.status_code == 200

    # tweet 확인
    resp = api.get(f'timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id': 1,
        'timeline': [{
            'user_id': 1,
            'tweet': "Hello World!"
        }]
    }


def test_follow(api):
    # 로그인
    resp = api.post(
        '/login',
        data=json.dumps({
            'email': 'noah@gmail.com',
            'password': 'test'
        }),
        content_type='application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']

    # 먼저 유저 1의 tweet 확인 해서 tweet 리스트가 비어 있는것을 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id': 1,
        'timeline': []
    }

    # follow 유저 아이디 = 2
    resp = api.post(
        '/follow',
        data=json.dumps({'id': 1, 'follow': 2}),
        content_type='application/json',
        headers={'Authorization': access_token}
    )
    assert resp.status_code == 200

    # 이제 유저 1의 tweet 확인 해서 유저 2의 tweet의 리턴 되는것을 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id': 1,
        'timeline': [
            {
                'user_id': 2,
                'tweet': "I am sinbee!"
            }
        ]
    }


def test_unfollow(api):
    # 로그인
    resp = api.post(
        '/login',
        data=json.dumps({
            'email': 'noah@gmail.com',
            'password': 'test'
        }),
        content_type='application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']

    # follow 유저 아이디 = 2
    resp = api.post(
        '/follow',
        data=json.dumps({'id': 1, 'follow': 2}),
        content_type='application/json',
        headers={'Authorization': access_token}
    )
    assert resp.status_code == 200

    # 이제 유저 1의 tweet 확인 해서 유저 2의 tweet의 리턴 되는것을 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id': 1,
        'timeline': [
            {
                'user_id': 2,
                'tweet': "I am sinbee!"
            }
        ]
    }

    # unfollow 유저 아이디 = 2
    resp = api.post(
        '/unfollow',
        data=json.dumps({'id':1, 'unfollow': 2}),
        content_type='application/json',
        headers={'Authorization': access_token}
    )
    assert resp.status_code == 200

    # 이제 유저 1의 tweet 확인 해서 유저 2의 tweet이 더 이상 리턴 되지 않는 것을 확인
    resp   = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id': 1,
        'timeline': []
    }

