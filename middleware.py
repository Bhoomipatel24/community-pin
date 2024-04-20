from flask import request, make_response, session
from flask_jwt_extended import (
    unset_jwt_cookies,
    create_access_token,
    create_refresh_token,
)

import jwt as jwt_orig

from config import JWT_SECRET

def check_and_refresh_token():
    access_token_cookie = request.cookies.get('access_token_cookie')
    refresh_token_cookie = request.cookies.get('refresh_token_cookie')

    value = False
    if not access_token_cookie:
        return value
    try:
        jwt_orig.decode(access_token_cookie, JWT_SECRET, algorithms=["HS256"])
        value =  True
    except jwt_orig.ExpiredSignatureError:
        new_token_can_be_generated = create_new_access_token(refresh_token_cookie)
        if new_token_can_be_generated:
            value = True
    except:
        value = False
    return value

def create_new_access_token(refresh_token_key):
    try:
        decoded_token = jwt_orig.decode(refresh_token_key, JWT_SECRET, algorithms=["HS256"])
        id = decoded_token.get('id', {}).get('id')
        email = decoded_token.get('sub', {}).get('email')
        g_token = decoded_token.get('sub', {}).get('g_token')
        data = {
                'id':id,
                'email':email,
                'g_token' : g_token
            }
        resp = make_response()
        unset_jwt_cookies(resp)
        create_access_token(identity=data)
        create_refresh_token(identity=data)
        session['user'] = 'active'
        session['user_id'] = id
        return True
    except:
        session.pop('user', None)
        session.pop('user_id', None)
        return False