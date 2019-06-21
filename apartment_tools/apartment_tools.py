#!/usr/bin/env python
# coding: utf-8
# author: shengwu

import json
import time
import urllib2
import urllib
import cookielib
import logging
import smtplib
from email.mime.text import MIMEText

logging.basicConfig(level=logging.NOTSET,
                    filename='apartment_tools_' + time.strftime('%Y%m%d', time.localtime(time.time())) + '.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s')

# 平台登录账号
accountCode = '************'
# 平台登录密码
accountPass = '************'

# 邮件发送方
_user = "xxxxxxxxxx@qq.com"
# 邮箱授权码
_pwd = "**************"
# 邮件接收方
_to = "xxxxxxxxxx@qq.com"

# 编号
card_no = ''

# 发送邮件请求次数
mail_send_num = int(10)
# 刷新时间 60s
time_sleep = 15
room_number = None
# url
opener = None
# 房间数量映射
apartment_dict = {}


# 一分钟更新一次
def start():
    # 用户登录
    load_user_login()
    # 加载请求地址
    url_list = get_url_list()
    get_message_number = 1
    # 邮箱验证
    send_mail("server start, check email running....................")
    while mail_send_num > 0:
        try:
            logging.info('第' + str(get_message_number) + '次获取房源信息.................')
            # 请求房源信息
            get_room_message_info(url_list)
        except urllib2.HTTPError, e:
            logging.error('server error:%s', e)
            send_mail("server error...................")
        get_message_number = get_message_number + 1
        time.sleep(float(time_sleep))


# 平台账号密码登录，获取cookies，默认只登录一次
def load_user_login():
    global opener
    #
    login_page = "http://117.71.57.99:9080/online/gzflogin.jtml?action=login"
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
    data = urllib.urlencode({"accountCode": accountCode, "accountPass": accountPass})
    opener.open(login_page, data)


# 预配置请求地址
def get_url_list():
    url_list = [{'name': '1#',
                 'building_code': '0011449816806945psc',
                 'url': 'http://117.71.57.99:9080/online/apply.do?action=formList1&code=01'
                        '&buildingCode=0011449816806945psc'},
                {'name': '2#',
                 'building_code': '0011449816830250MuI',
                 'url': 'http://117.71.57.99:9080/online/apply.do?action=formList1&code=01'
                        '&buildingCode=0011449816830250MuI'},
                # {'name': '综合楼东',
                #  'building_code': '0011449816876736sfx',
                #  'url': 'http://117.71.57.99:9080/online/apply.do?action=formList1&code=01'
                #         '&buildingCode=0011449816876736sfx'},
                {'name': '综合楼西',
                 'building_code': '0011449816949458BXk',
                 'url': 'http://117.71.57.99:9080/online/apply.do?action=formList1&code=01'
                        '&buildingCode=0011449816949458BXk'}
                ]
    return url_list


# 请求房源信息
def get_room_message_info(url_list):
    global room_number
    room_number = 1
    for url_info in url_list:
        op = opener.open(url_info['url'])
        data_list = op.read()
        data_analysis(json.loads(data_list, encoding="UTF-8")['list'], url_info['building_code'])
    logging.info('------------------------------')


# 数据解析
def data_analysis(data, building_code):
    room_list = []
    global room_number
    for key in data:
        floor_room_list = data[key]
        for room in floor_room_list:
            building_name = room['buildingName']
            room_floor = room['roomFloor']
            room_name = room['roomName']
            room_sex_name = room['roomSexName']
            room_type_name = room['roomTypeName']
            status = room['status']
            qty = int(room['qty'])
            how_person = int(room['howPerson'])
            room_code = room['roomCode']
            room_message = {'room_type_name': room_type_name, 'building_name': building_name, 'room_name': room_name}
            room_info = {'room_floor': room_floor, 'room_name': room_name, 'room_sex_name': room_sex_name,
                         'how_person': how_person, 'room_type_name': room_type_name, 'status': status,
                         'qty': qty, 'building_name': building_name, 'room_code': room_code}
            logging.info(str(room_number) + '.' + json.dumps(room_info, encoding="UTF-8", ensure_ascii=False))
            if qty > how_person:
                if room_type_name == u'男生单人间':
                    print (json.dumps(room_message, encoding="UTF-8", ensure_ascii=False))
                    logging.info(json.dumps(room_message, encoding="UTF-8", ensure_ascii=False))
                    add_account(building_code, room_code)
                    # 默认目前为无房状态，若qty > how_person时，表示新增了房源信息，发送e-mail请求
                    send_mail("皖水公寓房间已更新v1")
            room_list.append(room_type_name)
            room_number += 1
    # 当房源数量超过初始值时，表示新增了房源信息，发送e-mail请求
    if building_code not in apartment_dict:
        apartment_dict[building_code] = len(room_list)
    elif len(room_list) > apartment_dict[building_code]:
        send_mail("皖水公寓房间已更新V2")
        apartment_dict[building_code] = len(room_list)
    elif len(room_list) < apartment_dict[building_code]:
        apartment_dict[building_code] = len(room_list)


# 自动请求添加账号
def add_account(building_code, room_code):
    try:
        json_str = {'type': '01', 'cardNo': card_no, 'code': '01', 'buildingCode': building_code,
                    'roomCode': room_code}
        add_url = 'http://117.71.57.99:9080/online/apply.do?action=roomReserve'
        opener.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
        data = urllib.urlencode({"jsonStr": json.dumps(json_str, encoding="UTF-8", ensure_ascii=False)})
        op = opener.open(add_url, data)
        add_result = op.read()
        print 'add_result:' + add_result
        logging.info('add_result:' + add_result)
    except Exception as e:
        print ("error message:,%s" % e.message)


# 邮件通知
def send_mail(mail_title):
    mail_content = 'http://117.71.57.99:9080/online/gzflogin.jtml?action=login&accountCode=baoying18297984004&accountPass=baoying18297984004'
    msg = MIMEText(mail_content)
    # e-mail标题，注明是服务异常还是房源已更新
    msg["Subject"] = str(mail_title)
    msg["From"] = _user
    msg["To"] = _to
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(_user, _pwd)
        s.sendmail(_user, _to, msg.as_string())
        s.quit()
        print("send email Success!")
        global mail_send_num
        mail_send_num = mail_send_num - 1
        # send_mail_my(mail_title)
    except smtplib.SMTPException, e:
        logging.error("Falied,%s" % e)


# 邮件通知
def send_mail_my(mail_title):
    mail_content = 'http://117.71.57.99:9080/online/gzflogin.jtml?action=login&accountCode=baoying18297984004&accountPass=baoying18297984004'
    msg = MIMEText(mail_content)
    # e-mail标题，注明是服务异常还是房源已更新
    msg["Subject"] = str(mail_title)
    msg["From"] = _user
    msg["To"] = _my
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(_user, _pwd)
        s.sendmail(_user, _my, msg.as_string())
        s.quit()
        print("send email Success!")
    except smtplib.SMTPException, e:
        print ("Falied,%s" % e.message)


if __name__ == '__main__':
    start()
