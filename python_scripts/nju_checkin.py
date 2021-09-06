# NJU Health Checkin Script
# Copyright (C) 2021 Maxwell Lyu https://github.com/Maxwell-Lyu

import base64
import json
import os
import random
from http.cookiejar import MozillaCookieJar

import requests
from Crypto.Cipher import AES
from Crypto.Util import Padding
from bs4 import BeautifulSoup

LOG = ''


def encryptAES(_p0: str, _p1: str) -> str:
    _chars = list('ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678')

    def _rds(len: int) -> str:
        return ''.join(random.choices(_chars, k=len))

    def _gas(data: str, key0: str, iv0: str) -> bytes:
        encrypt = AES.new(key0.strip().encode('utf-8'),
                          AES.MODE_CBC, iv0.encode('utf-8'))
        return base64.b64encode(encrypt.encrypt(Padding.pad(data.encode('utf-8'), 16)))

    return _gas(_rds(64) + _p0, _p1, _rds(16)).decode('utf-8')


def do_login(session, cookie_path, response) -> bool:
    global LOG

    username = os.getenv('NJU_USER')
    password = os.getenv('NJU_PASS')
    if not username or not password:
        LOG += "No username or pwd found.\n"
        return False

    url_login = r'https://authserver.nju.edu.cn/authserver/login'

    soup = BeautifulSoup(response.text, 'html.parser')
    data_login = {
        'username': username,
        'password': encryptAES(password, soup.select_one("#pwdDefaultEncryptSalt").attrs['value']),
        'lt': soup.select_one('[name="lt"]').attrs['value'],
        'dllt': "userNamePasswordLogin",
        'execution': soup.select_one('[name="execution"]').attrs['value'],
        '_eventId': soup.select_one('[name="_eventId"]').attrs['value'],
        'rmShown': soup.select_one('[name="rmShown"]').attrs['value'],
    }
    # 'https://authserver.nju.edu.cn/authserver/index.do'
    response = session.post(url_login, data_login)

    if response.url.find(f"authserver/login") != -1:
        LOG += f"Login error, check your username = {username} and pwd = *** !\n"
        return False
    session.cookies.save(cookie_path, ignore_discard=True)
    LOG += f"use = {username} login success!\n"
    return True


def do_nju_checkin():
    global LOG
    cookie_path = os.getenv('NJU_CK') or "./ck.txt"

    url_no_login = r'https://authserver.nju.edu.cn/authserver/index.do'
    url_list = r'https://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do'
    url_apply = r'https://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/saveApplyInfos.do?'

    has_ck = os.path.isfile(cookie_path)
    s = MozillaCookieJar(cookie_path)
    has_ck and s.load(cookie_path, ignore_discard=True, ignore_expires=True)

    session = requests.Session()
    session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/93.0.4577.63'}
    session.cookies = s

    response = session.get(url_no_login)
    if response.url.find(f"authserver/login") != -1:
        if not do_login(session, cookie_path, response):
            return
    else:
        LOG += "use ck instead of login\n"

    # list
    content = session.get(url_list).json()

    # apply
    data = next(x for x in content['data'] if x.get('TJSJ') != '')
    data['WID'] = content['data'][0]['WID']
    fields = [
        'WID',
        'CURR_LOCATION',
        'IS_TWZC',
        'IS_HAS_JKQK',
        'JRSKMYS',
        'JZRJRSKMYS'
    ]
    result = session.get(url_apply + '&'.join([key + '=' + data[key] for key in fields]))

    answer = json.loads(result.text)
    answer['location'] = data['CURR_LOCATION']
    LOG += answer

    if result.status_code != 200:
        LOG += f"checkin error: {result.text}"


do_nju_checkin()

try:
    from notify import send
    import time

    send(f"NJU checkin at {time.strftime('%m-%d %H:%M:%S', time.localtime())}", LOG)
except ModuleNotFoundError:
    print(LOG)
