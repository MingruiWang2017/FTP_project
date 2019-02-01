# encoding: utf-8

"""
@ author: wangmingrui
@ time: 2019/1/26 17:17
@ desc: 服务器端配置文件
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # server的根目录
HOME_DIR = os.path.join(BASE_DIR, 'user_data','HOME')

BIND_HOST = 'localhost'
BIND_PORT = 8086
ip_port = (BIND_HOST, BIND_PORT)

MAX_RECV_SIZE = 1024 * 8

