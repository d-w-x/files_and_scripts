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

import execjs
import requests

from utils import log

URL_NJU_UIA_AUTH = 'https://authserver.nju.edu.cn/authserver/login'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"


class NjuUiaAuth:
    """
    DESCRIPTION:
        Designed for passing Unified Identity Authentication(UIA) of Nanjing University.
    """

    def __init__(self, dddd_server: str):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        if not dddd_server:
            log.info("No dddd server configured, use `ddddocr` package!")
        else:
            self.dddd_server = dddd_server

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
            pic_byte = self.session.get(url, stream=True).content
            if self.dddd_server:
                ocr_res = requests.post(f"{self.dddd_server.rstrip('/')}/ocr/file", files={'image': pic_byte}).text
            else:
                import ddddocr
                ocr_res = ddddocr.DdddOcr(show_ad=0).classification(pic_byte)
            if ocr_res:
                log.info(f"Captcha code is {ocr_res}.")
                return ocr_res
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
