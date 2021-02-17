from mcdreforged.api.all import *
import requests
import json
import websocket
import os

"""
将指定的QQ群聊信息自动转发到MC服务器中, 让正在服务器的玩家能在不跳出服务器的情况下与QQ群聊中的各位一起划水
此插件基于MCDReforged开发
同时使用到了mirai(QQ机器人框架)
以及mirai-api-http(机器人HTTP通讯插件)
@author 正义桑
"""

PLUGIN_METADATA = {
    'id': 'qbot',
    'version': '1.0.0',
    'name': 'A QQ Bot Develop By ZhengYi'
}


SESSION = ''
QQ_BOT_SERVER = ''
AUTH_KEY = ''
QQ = 0
ADMIN_QQ = 0
MAIN_GROUP = 0
SERVER = None
STATUS_RECI_MAP = ['未启动', '未启动', '启动']
STATUS_SESSION_MAP = ['未获取', '获取', '获取']

ws = None
"""
0:SESSION: [未获取]
1:SESSION: [获取到], 接收QQ群信息: [未启动] 
2:SESSION: [获取到], 接收QQ群信息: [启动] 
"""
bot_status = 0
bot_version = 'UNKNOWN'


CONFIG_FILE_CONTENT = '''{
  "qq_bot_server": "",
  "auth_key": "",
  "bot_qq": 0,
  "admin_qq": 0,
  "group_id": 0
}'''


# 初始化配置文件
def init_config():
    with open("./config/qbot.json", 'w') as file_obj:
        file_obj.write(CONFIG_FILE_CONTENT)
        file_obj.close()


# 读取配置文件
def load_config():
    global QQ_BOT_SERVER, AUTH_KEY, QQ, ADMIN_QQ, MAIN_GROUP
    if not os.path.isfile('./config/qbot.json'):
        SERVER.logger.warn("配置文件不存在，正在创建...")
        init_config()
        SERVER.unload_plugin('qbot')
    config_file = open("./config/qbot.json")
    config_json = json.load(config_file)
    QQ_BOT_SERVER = config_json['qq_bot_server']
    AUTH_KEY = config_json['auth_key']
    QQ = config_json['bot_qq']
    ADMIN_QQ = config_json['admin_qq']
    MAIN_GROUP = config_json['group_id']



def get_help_message():
    return RTextList(
        RText('========= QQ Bot通讯插件 ==========\n', RColor.yellow),
        RText('!!qq send <msg>: ', RColor.red), RText('向QQ群中发送消息\n'),
        RText('!!qq off: ', RColor.red), RText('关闭消息接收\n'),
        RText('!!qq on: ', RColor.red), RText('启用消息接收\n'),
        RText('!!qq status: ', RColor.red), RText('查看状态\n'),
        RText('================================', RColor.yellow)
    )


def get_status():
    return RTextList(
        RText('========= QQ Bot 状态 ==========\n', RColor.yellow),
        RText('BOT 版本: '), RText('[{}]\n'.format(bot_version), RColor.yellow),
        RText('BOT 认证: '), RText('[{}]\n'.format(STATUS_SESSION_MAP[bot_status]), RColor.yellow),
        RText('BOT 接收器: '), RText('[{}]\n'.format(STATUS_RECI_MAP[bot_status]), RColor.yellow),
        RText('================================', RColor.yellow)
    )


# 向QQ群中发送信息
def send_msg(msg):
    msg_obj = {
        'sessionKey': SESSION,
        'target': MAIN_GROUP,
        'messageChain': [
            {'type': 'Plain', 'text': '[MC服务器消息]: {}'.format(msg)}
        ]
    }
    send_resp = json.loads(requests.post('http://{}/sendGroupMessage'.format(QQ_BOT_SERVER), json=msg_obj).content)
    if send_resp['code'] == 0:
        return RText('发送成功', RColor.green)
    else:
        SERVER.logger.warn('发送信息失败->{}'.format(msg))
        return RText('发送失败', RColor.red)


def init_session():
    auth_user()
    if SESSION != '':
        verify_key()


# 获取WebSocket验证
def auth_user():
    global SERVER
    global SESSION
    global bot_version
    bot_info = json.loads(requests.get('http://{}/about'.format(QQ_BOT_SERVER)).content)
    if bot_info['code'] == 0:
        SERVER.logger.info("QQ机器人服务端版本: {}".format(bot_info["data"]["version"]))
        bot_version = bot_info["data"]["version"]
        auth_info = json.loads(
            requests.post('http://{}/auth'.format(QQ_BOT_SERVER), json={'authKey': AUTH_KEY}).content)
        if auth_info['code'] == 0:
            SESSION = auth_info['session']
            SERVER.logger.info("获取到SESSION: {}".format(auth_info['session']))
        elif auth_info['code'] == 1:
            SERVER.logger.error('错误的AUTH_KEY')
        else:
            SERVER.logger.error('未知错误')
    else:
        SERVER.logger.error('未知错误，可能是服务端未启动')


# 激活SESSION
def verify_key():
    global bot_status
    verify_resp = json.loads(requests.post('http://{}/verify'.format(QQ_BOT_SERVER),
                                           json={
                                               'sessionKey': SESSION,
                                               'qq': QQ
                                           }).content)
    if verify_resp['code'] == 0:
        SERVER.logger.info('SESSION已经激活')
        bot_status = 1
    else:
        SERVER.logger.error('SESSION激活失败')


# 释放SESSION
def release_session():
    pass


# 接收进程
@new_thread("QQ Bot Client")
def start_bot():
    global ws
    ws = websocket.WebSocketApp('ws://{}/message?sessionKey={}'.format(QQ_BOT_SERVER, SESSION),
                                on_message=on_message,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()


def on_message(ws, message):
    format_msg = json.loads(message)
    if format_msg['type'] == 'GroupMessage':
        group_msg(format_msg)


def on_open(ws):
    global bot_status
    bot_status = 2


def on_close(ws):
    global bot_status
    SERVER.logger.warn('接收进程将关闭')
    SERVER.say(RText('[QBOT]: 接收进程关闭', RColor.yellow))
    bot_status = 1


def group_msg(message):
    # 判断是否为公共群发出信息
    if message['sender']['group']['id'] == MAIN_GROUP:
        sender = message['sender']['memberName']
        msg = parse_msg(message['messageChain'])
        SERVER.logger.info('接收到来自{}的消息: {}'.format(sender, msg))
        SERVER.say(RTextList(
            RText('[QQ群消息][{}]:'.format(sender), RColor.yellow),
            RText(msg)
        ))


def parse_msg(msg_chain):
    msg_txt = ''
    for msg in msg_chain:
        if msg['type'] == 'Source':
            pass
        elif msg['type'] == 'Plain':
            msg_txt += msg['text']
        elif msg['type'] == 'Image':
            msg_txt += '[图片]'
        elif msg['type'] == 'Face':
            msg_txt += '[{}]'.format(msg['name'])
    return msg_txt


# BOT 启动
def bot_on():
    if ws is None:
        start_bot()
        return RText('机器人启动成功', RColor.green)


# BOT 关闭
def bot_off():
    global ws
    if ws is not None:
        ws.close()
        ws = None
        return RText('机器人已关闭', RColor.red)


def on_load(server, old):
    global SERVER
    SERVER = server
    load_config()
    # 配置文件出错会导致无法启动
    try:
        init_session()
        bot_on()
    except:
        SERVER.logger.error('无法正常启动插件,请检查配置文件')
        SERVER.unload_plugin('qbot')
        return
    server.register_help_message('!!qq', 'QQ群通信插件')
    server.register_command(
        Literal('!!qq').runs(lambda src: src.reply(get_help_message())).then(
            Literal('send').then(
                GreedyText('message').runs(lambda src, ctx: src.reply(send_msg(ctx['message'])))
            )
        ).then(
            Literal('help').runs(lambda src: src.reply(get_help_message()))
        ).then(
            Literal('status').runs(lambda src: src.reply(get_status()))
        ).then(
            Literal('on').runs(lambda src: src.reply(bot_on()))
        ).then(
            Literal('off').runs(lambda src: src.reply(bot_off()))
        )
    )


def on_unload(server):
    global ws
    server.logger.info('正在释放WS链接')
    if ws is not None:
        ws.close()
        ws = None
