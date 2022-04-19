from os import getenv

from njupass import NjuUiaAuth
from utils import log, LOG_STR

URL_JKDK_LIST = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do'
URL_JKDK_APPLY = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/saveApplyInfos.do?'

def do_nju_checkin(username: str, password: str):
    if username == '' or password == '':
        log.error('账户、密码或为空！')

    log.info('尝试登录...')
    if not auth.tryLogin(username, password):
        log.error('登录失败。可能是用户名或密码错误，或是验证码无法识别。')
    log.info('登录成功！')

    for count in range(10):
        log.info('尝试获取打卡列表信息...')
        r = auth.session.get(URL_JKDK_LIST)
        if r.status_code != 200:
            log.info(f'第 {count} 次尝试获取打卡信息失败。')
            time.sleep(5)
            continue

        content = r.json()
        if content['data'][0]['TBZT'] == '0':
            data = next(x for x in content['data'] if x.get('TJSJ') != '')
            data['WID'] = content['data'][0]['WID']
            fields = [
                "WID",
                "CURR_LOCATION",  # 位置
                "IS_TWZC",  # 体温正常
                "IS_HAS_JKQK",  # 健康情况
                "JRSKMYS",  # 今日苏康码颜色
                "JZRJRSKMYS",  # 居住人今日苏康码颜色
                "SFZJLN",  # 是否最近离宁
                "ZJHSJCSJ"  # 最近核酸检测时间
            ]
            log.info('正在打卡...')
            answer = auth.session.get(URL_JKDK_APPLY + '&'.join([key + '=' + data[key] for key in fields])).json()
            answer['location'] = data['CURR_LOCATION']
            answer['check_date'] = data['ZJHSJCSJ']
            log.info(answer)
        else:
            log.info('今日已打卡！')
        return
    log.error('打卡失败，请尝试手动打卡')


# DDDD_SERVER=http://192.168.10.80:9898
ocr_server = getenv("DDDD_SERVER")
auth = NjuUiaAuth(ocr_server)

# NJU_USERINFO=USERNAME1$PASSWORD1;USERNAME2$PASSWORD2
accounts = getenv('NJU_USERINFO')
if accounts:
    for account in accounts.split(';'):
        do_nju_checkin(*account.split('$'))
else:
    log.error('NJU_USERINFO 变量为空！')

try:
    from notify import send
    import time

    send(f'NJU checkin at {time.strftime("%m-%d %H:%M:%S", time.localtime())}', LOG_STR)
except ModuleNotFoundError:
    print(LOG_STR)
