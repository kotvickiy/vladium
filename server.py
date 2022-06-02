# FastAPI Server

import base64
import uvicorn
import hmac
import hashlib
import json
from typing import Optional
from fastapi import FastAPI, Form, Cookie
from fastapi.responses import Response


app = FastAPI()

SECRET_KEY = "2c99ab5e72c451945edeed38b252e37d09edfc21ab9f03448c4fd8a0d1c5d3cd"
PASSWORD_SALT = "bb5942203066438b468d9c0905033226576589f53a09ac429775287604994326"


def sign_data(data: str) -> str:
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    username_base64, sign = username_signed.split('.')
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username


def verify_password(username: str, password: str) -> bool:
    password_hash = hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest().lower()
    stored_password_hash = users[username]["password"].lower()
    return password_hash == stored_password_hash


users = {
    'vladkotvickiy@gmail.com': {
        'name': 'Владислав',
        'password': '2e13e09da37a9772f37bf68e236e9321f0abf9524d58b3f93a7b363a98124143', # hashlib.sha256( ("hsvk9oqw" + PASSWORD_SALT).encode()  ).hexdigest()
        'balance': 1_000_000
    },
    'alexey@user.com': {
        'name': 'Алексей',
        # 'password': 'some_password_1',
        'password': 'fa8ed0ac90d0fa9593b73b1914b07c5eab01f405ed971e951a9aae459fd440b1',
        'balance': 100_000
    },
    'petr@user.com': {
        'name': 'Пётр',
        # 'password': 'some_password_2',
        'password': '9c80199a600b5c7db167c9bdbed785be562ad2ece14ea71ca86fc756325edd16',
        'balance': 555_555
    }
}


@app.get('/')
def index_page(username: Optional[str] = Cookie(default=None)):
    with open('templates/login.html', 'r', encoding='utf-8') as f:
        login_page = f.read()
    if not username:
        return Response(login_page, media_type='text/html')
    valid_username = get_username_from_signed_string(username)
    if not valid_username:
        response = Response(login_page, media_type='text/html')
        response.delete_cookie(key='username')
        return response
    # try:
    #     user = users[valid_username]
    # except KeyError:
    #     response = Response(login_page, media_type='text/html')
    #     response.delete_cookie(key='username')
    #     return response
    return Response(
        f'Привет, {users[valid_username]["name"]}!<br />'
        f'Баланс: {users[valid_username]["balance"]}',
        media_type='text/html')


@app.post("/login")
def process_login_page(username : str = Form(...), password : str = Form(...)):
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "success": False,
                "message": "Я Вас не знаю!"
            }),
            media_type='application/json')
    response = Response(
        json.dumps({
            "success": True,
            "message": f'Привет, {user["name"]}!<br />  Баланс {user["balance"]}'
        }),
        media_type='application/json')

    username_signed = base64.b64encode(username.encode()).decode() + "." + sign_data(username)
    response.set_cookie(key='username', value=username_signed, max_age=12000000000)
    return response


if __name__ == '__main__':
    uvicorn.run('server:app', port=8000)
