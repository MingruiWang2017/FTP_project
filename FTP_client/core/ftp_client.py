# encoding: utf-8

"""
@ author: wangmingrui
@ time: 2019/1/30 16:38
@ desc: ftp客户端
"""

import os
import sys
import socket
import hashlib
import json
from ..conf import setting


class FTPClient(object):
    '''
    FTP 客户端主程序
    '''
    user_name = None
    user_dir = None

    def __init__(self):
        self.client = socket.socket()
        self.client.connect(setting.ip_port)

    def run(self):
        '''
        客户端运行函数
        :return:
        '''
        while True:
            # 接收入户输入，作为命令
            cmd_line = input(">>:").strip()
            if len(cmd_line) == 0:
                break

            # 分析cmd，使用反射调用相关方法
            cmd = cmd_line.split()[0]
            if len(cmd_line.split()) > 1 :
                param = cmd_line.split()[1]

            if hasattr(self, cmd):
                func = getattr(cmd)
                func(param)

    def login(self):
        '''
        登录操作，之后要求用户输入用户名和密码，以json格式发送给服务器端
        :return: boolean 是否登陆成功
        '''
        user_name = input("Please input user name: ").strip()
        password = input("Please input password: ").strip()
        password = FTPClient.md5_secret(password)
        login_dict = {"action" : "login",
                      "username" : user_name,
                      "password" : password}
        login_json = json.dumps(login_dict)
        # 向server端发送登录信息
        login_json = bytes(login_json, encoding="utf-8")
        self.client.send(login_json)

        # 接收server端返回的登录信息
        data = self.client.recv(1024)  # 第一条消息接收返回信息长度
        info_len = int(data.decode('utf-8'))
        self.client.send(b"ready")
        recv_size = 0
        while recv_size < info_len:
            data += self.client.recv(setting.MAX_RECV_SZIE)  # 接收返回的登录信息
            recv_size = len(data)
        login_result = json.loads(data.decode())

        if login_result.get("result") == True:
            self.user_name = login_result.get("user_name")
            self.user_dir = os.path.join(setting.HOME_DIR, user_name)
            sys.path.append(self.user_dir)
            print("Welcome back %s !" %self.user_name)
        else:
            print("Oooh, log in failur, please try again.")
            self.login()

    def singup(self):
        '''
        新用户注册
        :return: None, 注册成功显示用户名，注册失败提示用户重试
        '''
        user_name = input("Please input user name: ").strip()
        password = input("Please input password: ").strip()  # 由于是明文输入，就不再再次输入确认密码了
        password = FTPClient.md5_secret(password)
        signup_dict = {"action" : "signup",
                       "user_name" : user_name,
                       "password" : password}
        signup_json = json.dumps(signup_dict)
        # 向server发送注册信息
        signup_json = bytes(signup_json, encoding="utf-8")
        self.client.send(signup_json)

        # 接收server端返回的注册信息
        data = self.client.recv(1024)  # 第一条消息接收返回信息长度
        info_len = int(data.decode('utf-8'))
        self.client.send(b"ready")
        recv_size = 0
        while recv_size < info_len:
            data += self.client.recv(setting.MAX_RECV_SZIE)  # 接收返回的注册信息
            recv_size = len(data)
        signup_result = json.loads(data.decode())

        if signup_result.get("result") == True:
            self.user_name = signup_result.get("user_name")
            self.user_dir = os.path.join(setting.HOME_DIR, user_name)
            sys.path.append(self.user_dir)
            print("Congratulations %s, you have signded up successfully!" % self.user_name)
        else:
            print("Oooh, signup failure, please try again.")
            self.singup()




    @staticmethod
    def md5_secret(content):
        '''
        对内容进行md5加密，返回content的md5值
        :param content: 要进行加密的内容
        :return: 加密结果
        '''
        md5 = hashlib.md5()
        bytes_content = bytes(content, encoding='utf-8')
        md5.update(bytes_content)
        return md5.hexdigest()