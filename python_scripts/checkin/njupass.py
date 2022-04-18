"""
DESCRIPTION:
    Tools for getting Authorization websites of Nanjing University
PACKAGES:
    NjuUiaAuth
    NjuEliteAuth
"""
import os
import re
import time

import ddddocr
import execjs
import requests

from utils import log

URL_NJU_UIA_AUTH = 'https://authserver.nju.edu.cn/authserver/login'
USER_AGENT = "Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Zoom Edition Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.88 Mobile Safari/537.36 okhttp/3.12.4 cpdaily/9.0.15 wisedu/9.0.15"


class NjuUiaAuth:
    """
    DESCRIPTION:
        Designed for passing Unified Identity Authentication(UIA) of Nanjing University.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})

        r = self.session.get(URL_NJU_UIA_AUTH)
        self.lt = re.search(
            r'<input type="hidden" name="lt" value="(.*)"/>', r.text).group(1)
        self.execution = re.search(
            r'<input type="hidden" name="execution" value="(.*)"/>', r.text).group(1)
        self._eventId = re.search(
            r'<input type="hidden" name="_eventId" value="(.*)"/>', r.text).group(1)
        self.rmShown = re.search(
            r'<input type="hidden" name="rmShown" value="(.*)"', r.text).group(1)
        self.pwdDefaultEncryptSalt = re.search(
            r'var pwdDefaultEncryptSalt = "(.*)"', r.text).group(1)

    def getCaptchaCode(self, try_times: int = 3) -> str:
        """
        DESCRIPTION:
            Getting captcha code binded with IP
        RETURN_VALUE:
            captcha code image(ByteIO). Recommended using Image.show() in PIL.
        """
        url = 'https://authserver.nju.edu.cn/authserver/captcha.html'
        for _ in range(try_times):
            res = self.session.get(url, stream=True)
            ocr = ddddocr.DdddOcr(show_ad=0)
            # with BytesIO(res.content) as f:
            res = ocr.classification(res.content)
            if res:
                return res
            log.warning(f"The {try_times} try to login failed!")
            time.sleep(1)
        return ""

    def parsePassword(self, password: str):
        """
        DESCRIPTION:
            Parsing password to encrypted form which can be identified by the backend sersver of UIA.
        ATTRIBUTES:
            password(str): Original password
        """
        with open(os.path.join(os.path.dirname(__file__), './encrypt.js')) as f:
            ctx = execjs.compile(f.read())
        return ctx.call('encryptAES', password, self.pwdDefaultEncryptSalt)

    def needCaptcha(self, username: str) -> bool:
        url = 'https://authserver.nju.edu.cn/authserver/needCaptcha.html?username={}'.format(
            username)
        r = self.session.post(url)
        if 'true' in r.text:
            log.info("统一认证平台需要输入验证码才能继续，尝试识别验证码...")
            return True
        else:
            return False

    def tryLogin(self, username: str, password: str, try_times: int = 3):
        """
        DESCRIPTION:
            Try to login using OCR to bypass captcha.
            Return true if login success, false otherwise
        """
        for _ in range(try_times):
            captchaText = ""
            if self.needCaptcha(username):
                captchaText = self.getCaptchaCode()
            ok = self.login(username, password, captchaResponse=captchaText)
            if ok:
                return True
            log.warning(f"The {try_times} try to get captcha failed!")
            time.sleep(2)
        return False

    def login(self, username: str, password: str, captchaResponse: str = ""):
        """
        DESCRIPTION:
            Post a request for logging in.
            Return true if login success, false otherwise
        ATTRIBUTES:
            username(str)
            password(str)
        """
        data = {
            'username': username,
            'password': self.parsePassword(password),
            'lt': self.lt,
            'dllt': 'userNamePasswordLogin',
            'execution': self.execution,
            '_eventId': self._eventId,
            'rmShown': self.rmShown,
            'captchaResponse': captchaResponse,
            "User-Agent": USER_AGENT
        }
        r = self.session.post(URL_NJU_UIA_AUTH,
                              data=data,
                              allow_redirects=False)
        return r.status_code == 302
