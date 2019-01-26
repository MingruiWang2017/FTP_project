# encoding: utf-8

"""
@ author: wangmingrui
@ time: 2019/1/26 17:09
@ desc: 服务器端主程序，实现管理功能
"""

import socketserver, json, os, hashlib
from ..conf import setting
from ..core.ftp_server import FTPServer


class Manager(object):
    '''
    主程序，包括启动FTPServer， 创建用户，登录，退出
    '''

    def start_ftp(self):
        '''
        启动server
        :return:
        '''
        server = FTPServer(setting.ip_port)
