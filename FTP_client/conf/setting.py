# encoding: utf-8

"""
@ author: wangmingrui
@ time: 2019/1/30 16:32
@ desc: 配置文件
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
HOME_DIR = os.path.join(BASE_DIR, "/user_data/HOME")

# sys.path.append(BASE_DIR)  # 将根目录加入到环境路径中

MAX_RECV_SIZE = 1024 * 8
USER_QUATO = 1024 * 1024 * 1024 * 10  # 初始用户配额为10G

HOST = "localhost"
PORT = "8086"
ip_port = (HOST, PORT)