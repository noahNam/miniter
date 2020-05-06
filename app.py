import jwt
import bcrypt

from flask import Flask, request, jsonify, current_app, Response, g
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS


'''
Default JSON encoder는 set을 JSON으로 변환할 수 없다.
그러므로 커스텀 엔코더를 작성해서 set을 list로 변환하여 JSON으로 변환가능하게 해주어야 한다.
'''


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self, obj)


def get_user(user_id):
    user = current_app.database.execute(text("""
        SELECT 
            id,
            name,
            email,
            profile
        FROM users
        WHERE id = :user_id
    """), {
        'user_id': user_id
    }).fetchone()
    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'profile': user['profile']
    } if user else None


def insert_user(user):
    return current_app.database.execute(text("""
        INSERT INTO users (
            name,
            email,
            profile,
            hashed_password
        ) VALUES (
            :name,
            :email,
            :profile,
            :password
        )
    """), user).lastrowid


def insert_tweet(user_tweet):
    return current_app.database.execute(text("""
        INSERT INTO tweets (
            user_id,
            tweet
        ) VALUES (
            :id,
            :tweet
        )
    """), user_tweet).rowcount


def insert_follow(user_follow):
    return current_app.database.execute(text("""
        INSERT INTO users_follow_list (
            user_id,
            follow_user_id
        ) VALUES (
            :id,
            :follow
        )
    """), user_follow).rowcount


def insert_unfollow(user_unfollow):
    return current_app.database.execute(text("""
        DELETE FROM users_follow_list
        WHERE user_id = :id
        AND follow_user_id = :unfollow
    """), user_unfollow).rowcount


def get_timeline(user_id):
    timeline = current_app.database.execute(text("""
        SELECT 
            t.user_id,
            t.tweet
        FROM tweets t
        LEFT JOIN users_follow_list ufl ON ufl.user_id = :user_id
        WHERE t.user_id = :user_id 
        OR t.user_id = ufl.follow_user_id
    """), {
        'user_id' : user_id
    }).fetchall()

    return [{
        'user_id' : tweet['user_id'],
        'tweet'   : tweet['tweet']
    } for tweet in timeline]


def get_user_id_and_password(email):
    row = current_app.database.execute(text("""    
        SELECT
            id,
            hashed_password
        FROM users
        WHERE email = :email
    """), {'email' : email}).fetchone()

    return {
        'id'              : row['id'],
        'hashed_password' : row['hashed_password']
    } if row else None


#########################################################
#       Decorators
#########################################################
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except jwt.InvalidTokenError:
                 payload = None

            if payload is None: return Response(status=401)

            """
            Flask에서 g 객체는 스레드와 각각의 request 내에서만 값이 유효한 스레드 로컬 변수이다 
            사용자의 요청이 동시에 들어오더라도 각각의 request 내에서만 g 객체가 유효하기 때문에 사용자 ID를 저장해도 문제가 없다.
            """
            user_id   = payload['user_id']
            g.user_id = user_id
            g.user    = get_user(user_id) if user_id else None
        else:
            return Response(status = 401)

        return f(*args, **kwargs)
    return decorated_function


# Flask가 create_app 이라는 이름의 함수를 자동으로 팩토리(Factory) 함수로 인식해서 해당 함수를 통해 Flask를 실행한다.
# test_config 파라미터를 받는 이유는 단위 테스트 할 때, 테스트용 데이터베이스 등의 테스트 설정 정보를 적용하기 위함이다.
# test_config가 None이면 config.py 파일에서 설정을 읽어 들인다. test_config 인자가 None이 아니라면 해당 설정을 적용시킨다.
# current_app은 create_app 함수에서 생성한 app 변수를 create_app 함수 외부에서도 사용할 수 있게 해준다.
def create_app(test_config=None):
    app = Flask(__name__)

    CORS(app)

    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)

    app.database = create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0)
    app.json_encoder = CustomJSONEncoder

    @app.route('/ping', methods=['GET'])
    def ping():
        return "pong"

    @app.route('/sign-up', methods=['POST'])
    def sign_up():
        new_user = request.json
        new_user['password'] = bcrypt.hashpw(
            new_user['password'].encode('UTF-8'),
            bcrypt.gensalt()
        )

        new_user_id = insert_user(new_user)
        new_user = get_user(new_user_id)

        return jsonify(new_user)


    @app.route('/login', methods=['POST'])
    def login():
        credential      = request.json
        email           = credential['email']
        password        = credential['password']
        user_credential = get_user_id_and_password(email)

        if user_credential and bcrypt.checkpw(password.encode('UTF-8'), user_credential['hashed_password'].encode('UTF-8')):
            user_id = user_credential['id']
            payload = {
                'user_id' : user_id,
                'exp'     : datetime.utcnow() + timedelta(seconds = 60 * 60 * 24)
            }

            token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], 'HS256')

            return jsonify({
                'user_id'      : user_id,
                'access_token' : token.decode('UTF-8')
            })
        else:
            return '', 401


    @app.route("/tweet", methods=['POST'])
    @login_required
    def tweet():
        user_tweet = request.json
        user_tweet['id'] = g.user_id
        tweet = user_tweet['tweet']

        if len(tweet) > 300:
            return '300자를 초과했습니다', 400

        insert_tweet(user_tweet)

        return jsonify({
            'msg': '트윗이 성공했습니다',
            'status_code': 200
        })

    @app.route('/timeline/<int:user_id>', methods=['GET'])
    def timeline(user_id):
        return jsonify({
            'user_id'  : user_id,
            'timeline' : get_timeline(user_id)
        })

    @app.route('/timeline', methods=['GET'])
    @login_required
    def user_timeline():
        user_id = g.user_id

        return jsonify({
            'user_id'  : user_id,
            'timeline' : get_timeline(user_id)
        })

    @app.route('/follow', methods=['POST'])
    @login_required
    def follow():
        payload = request.json
        insert_follow(payload)

        return '', 200

    @app.route('/unfollow', methods=['POST'])
    @login_required
    def unfollow():
        payload = request.json
        insert_unfollow(payload)

        return '', 200

    return app
