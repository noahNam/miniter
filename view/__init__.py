import jwt

from flask import Flask, request, jsonify, current_app, Response, g
from flask.json import JSONEncoder
from functools import wraps

'''
Default JSON encoder는 set을 JSON으로 변환할 수 없다.
그러므로 커스텀 엔코더를 작성해서 set을 list로 변환하여 JSON으로 변환가능하게 해주어야 한다.
'''


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self, obj)


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
            user_id = payload['user_id']
            g.user_id = user_id
        else:
            return Response(status=401)

        return f(*args, **kwargs)

    return decorated_function


def create_endpoints(app, services):
    app.json_encoder = CustomJSONEncoder

    user_service = services.user_service
    tweet_service = services.tweet_service

    @app.route('/ping', methods=['GET'])
    def ping():
        return "pong"

    @app.route('/sign-up', methods=['POST'])
    def sign_up():
        new_user = request.json
        new_user = user_service.create_new_user(new_user)

        return jsonify(new_user)

    @app.route('/login', methods=['POST'])
    def login():
        credential = request.json
        autorized = user_service.login(credential)

        if autorized:
            user_credential = user_service.get_user_id_and_password(credential['email'])
            user_id = user_credential['id']
            token = user_service.generate_access_token(user_id)

            return jsonify({
                'user_id': user_id,
                'access_token': token
            })
        else:
            return '', 401

    @app.route("/tweet", methods=['POST'])
    @login_required
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']
        user_id = g.user_id

        result = tweet_service.tweet(user_id, tweet)

        if result is None:
            return '300자를 초과했습니다', 400

        return jsonify({
            'msg': '트윗이 성공했습니다',
            'status_code': 200
        })


    @app.route('/follow', methods=['POST'])
    @login_required
    def follow():
        payload = request.json
        user_id = g.user_id
        follow_id = payload['follow']

        user_service.follow(user_id, follow_id)

        return jsonify({
            'msg': 'follow 되었습니다.',
            'status_code': 200
        })

    @app.route('/unfollow', methods=['POST'])
    @login_required
    def unfollow():
        payload = request.json
        user_id = g.user_id
        unfollow_id = payload['unfollow']

        user_service.unfollow(user_id, unfollow_id)

        return jsonify({
            'msg': 'unfollow 되었습니다.',
            'status_code': 200
        })

    @app.route('/timeline/<int:user_id>', methods=['GET'])
    def timeline(user_id):
        timeline = tweet_service.get_timeline(user_id)

        return jsonify({
            'user_id': user_id,
            'timeline': timeline
        })

    @app.route('/timeline', methods=['GET'])
    @login_required
    def user_timeline():
        timeline = tweet_service.get_timeline(g.user_id)

        return jsonify({
            'user_id': g.user_id,
            'timeline': timeline
        })