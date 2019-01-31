# encoding: utf-8

"""
@ author: wangmingrui
@ time: 2019/1/30 16:32
@ desc: 配置文件
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
HOME_DIR = os.path.join(BASE_DIR, "/user_data/HOME")

MAX_RECV_SIZE = 1024 * 8
USER_QUATO = 1024 * 1024 * 1024 * 10  # 初始用户配额为10G

HOST = "localhost"
PORT = 8086
ip_port = (HOST, PORT)