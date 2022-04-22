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
from http.cookiejar import MozillaCookieJar
from random import choice

import execjs
import requests

from utils import log

URL_NJU_UIA_AUTH = "https://authserver.nju.edu.cn/authserver/login"
URL_NJU_UIA_INFO = "https://authserver.nju.edu.cn/authserver/index.do"
USER_AGENT = "Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Zoom Edition Build/SKQ1.211006.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.88 Mobile Safari/537.36 okhttp/3.12.4 cpdaily/9.0.15 wisedu/9.0.15"


class NjuUiaAuth:
    """
    DESCRIPTION:
        Designed for passing Unified Identity Authentication(UIA) of Nanjing University.
    """

    def __init__(self, dddd_server: str):
        self.session = requests.Session()
        self.session.cookies = MozillaCookieJar()
        self.session.headers.update({"User-Agent": USER_AGENT})
        if not dddd_server:
            log.info("No dddd server configured, use `ddddocr` package!")
            self.dddd_server = ""
        else:
            self.dddd_server = dddd_server


    def getCaptchaCode(self, try_times: int = 3) -> str:
        """
        DESCRIPTION:
            Getting captcha code binded with IP
        RETURN_VALUE:
            captcha code image(ByteIO). Recommended using Image.show() in PIL.
        """
        url = "https://authserver.nju.edu.cn/authserver/captcha.html"
        for _ in range(try_times):
            try:
                pic_byte = self.session.get(url, stream=True).content
            except ConnectionError:
                log.warning(f"Can't connect to auth servet to get captcha. {_}/{try_times}")
                time.sleep(choice(range(5)))
                continue

            if self.dddd_server:
                ocr_res = requests.post(f"{self.dddd_server.rstrip('/')}/ocr/file", files={"image": pic_byte}).text
            else:
                import ddddocr
                ocr_res = ddddocr.DdddOcr(show_ad=0).classification(pic_byte)
            if ocr_res:
                log.info(f"Captcha code is {ocr_res}.")
                return ocr_res
            log.warning(f"The {_} try to get captcha failed!")
            time.sleep(choice(range(5)))
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
        return ctx.call("encryptAES", password, self.pwdDefaultEncryptSalt)

    def needCaptcha(self, username: str) -> bool:
        url = f"https://authserver.nju.edu.cn/authserver/needCaptcha.html?username={username}"
        try:
            r = self.session.post(url)
        except ConnectionError:
            r = {"text": ""}

        if 'true' in r.text:
            log.info("统一认证平台需要输入验证码才能继续，尝试识别验证码...")
            return True
        else:
            return False

    def tryCookie(self, username):
        cookie_path = f"./{username}.ck"
        if os.path.isfile(cookie_path):
            self.session.cookies.load(cookie_path, ignore_discard=True, ignore_expires=True)
            for _ in range(3):
                try:
                    self.session.get(f"{URL_NJU_UIA_AUTH}?service={URL_NJU_UIA_INFO}")
                    if self.session.get(URL_NJU_UIA_INFO).url != URL_NJU_UIA_INFO:
                        log.warning("Cookie expired! Reset cookie.")
                        os.remove(cookie_path)
                        self.session = requests.Session()
                        self.session.cookies = MozillaCookieJar()
                        self.session.headers.update({"User-Agent": USER_AGENT})
                        return False
                    log.info(f"Use cookie to login. {_}/3")
                    return True
                except ConnectionError:
                    continue
            log.warning("Can't connect to auth server to get account info!")
            return False
        else:
            log.info("No cookie file find.")
            return False

    def tryLogin(self, username: str, password: str, try_times: int = 3):
        """
        DESCRIPTION:
            Try to login using OCR to bypass captcha.
            Return true if login success, false otherwise
        """
        if self.tryCookie(username):
            return True

        for _ in range(try_times):
            captchaText = ""
            if self.needCaptcha(username):
                captchaText = self.getCaptchaCode()
            try:
                ok = self.login(username, password, captchaResponse=captchaText)
            except ConnectionError:
                log.warning(f"Can't connect to auth server to login! {_}/{try_times}")
                time.sleep(choice(range(5)))
                continue
            if ok:
                self.session.cookies.clear(domain="authserver.nju.edu.cn", path="/", name="JSESSIONID")
                self.session.cookies.clear(domain="authserver.nju.edu.cn", path="/authserver", name="route")
                self.session.cookies.save(f"./{username}.ck", ignore_discard=True)
                log.info("Cookie saved.")
                return True
            log.warning(f"The {_} try to login failed!")
            time.sleep(choice(range(5)))
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
