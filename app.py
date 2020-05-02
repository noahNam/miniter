from flask import Flask, request, jsonify, current_app
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text

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
        'user_id': user_id
    }).fetchall()

    return [{
        'user_id': tweet['user_id'],
        'tweet': tweet['tweet']
    } for tweet in timeline]


# Flask가 create_app 이라는 이름의 함수를 자동으로 팩토리(Factory) 함수로 인식해서 해당 함수를 통해 Flask를 실행한다.
# test_config 파라미터를 받는 이유는 단위 테스트 할 때, 테스트용 데이터베이스 등의 테스트 설정 정보를 적용하기 위함이다.
# test_config가 None이면 config.py 파일에서 설정을 읽어 들인다. test_config 인자가 None이 아니라면 해당 설정을 적용시킨다.
# current_app은 create_app 함수에서 생성한 app 변수를 create_app 함수 외부에서도 사용할 수 있게 해준다.
def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)

    app.database = create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0)

    app.users = {}
    app.tweets = []
    app.id_count = 1
    app.json_encoder = CustomJSONEncoder

    @app.route('/ping', methods=['GET'])
    def ping():
        return "pong"

    @app.route('/sign-up', methods=['POST'])
    def sign_up():
        new_user = request.json
        new_user_id = insert_user(new_user)
        new_user = get_user(new_user_id)

        return jsonify(new_user)

    @app.route("/tweet", methods=['POST'])
    def tweet():
        user_tweet = request.json
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

    @app.route('/follow', methods=['POST'])
    def follow():
        payload = request.json
        insert_follow(payload)

        return '', 200

    @app.route('/unfollow', methods=['POST'])
    def unfollow():
        payload = request.json
        insert_unfollow(payload)

        return '', 200

    return app
