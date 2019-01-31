# encoding: utf-8

"""
@ author: wangmingrui
@ time: 2019/1/26 17:24
@ desc: ftp 服务器的处理逻辑
"""

import socketserver
import os
import json
import hashlib
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from conf import setting


class ServerRequestHandler(socketserver.BaseRequestHandler):
    '''
    服务器请求处理类
    '''
    # def __init__(self,user):
    #     super()
    #     self.user = user
    #     self.user_dir = os.path.join(setting.HOME_DIR, user)  # 用户目录
    #     self.user_current_dir = self.user_dir.substring[self.user_dir.find("HOME"):]


    def handle(self):
        '''
        接收请求，并分析命令，之后调用相关方法
        :user: 当前用户
        :return: None
        '''
        while True:
            try:
                data = self.request.recv(setting.MAX_RECV_DATA).decode()
                print(data)
                info_len = int(data)
                recv_len = 0
                data = b""
                self.request.send(b"ready")
                while recv_len < info_len:
                    data += self.request.recv(setting.MAX_RECV_DATA)
                    recv_len = len(data)

                if not data:
                    print("\033[31;1m--------user break connection--------\033[0m")
                    break


                # 解析json数据
                data = data.decode()
                command_json = json.loads(data)

                print("user command >>: ", command_json.get("action"))

                cmd = command_json.get("action")
                # 使用反射定位cmd调用的方法
                if hasattr(self, cmd):
                    func = getattr(self, cmd)
                    func(command_json)
                else:
                    print("\033[31;1m-------command not found-------\033[0m")
            except ConnectionResetError as err:
                print("\033[31;1m-----------user break connection---------\033[0m")
                break

    def login(self, info):
        '''
        接收用户登陆请求
        :param info:
        :return:
        '''
        print(info)
        username = info.get("username")
        password = info.get("password")
        # 读取用户信息文件确认用户是否存在
        with open("..conf.userinfo.ini") as f:
            if len(f.read()) > 0:
                all_user_info = json.load(f)
                print(all_user_info)





    # def ls(self, *args):
    #     '''
    #     列出当前目录下文件列表功能
    #     :param args: 文件路径，默认为当前文件目录
    #     :return: 文件目录下的文件列表
    #     '''
    #     user_cur_dir = os.path.join(self.user_dir, args[0])
    #     result = os.listdir(user_cur_dir)
    #
    #     for _dir in result:
    #         print("\t-", _dir)
    #
    # def cd(self, *args):
    #     '''
    #     打开指定的文件夹
    #     :param args: 文件夹名
    #     :return:
    #     '''
    #     user_dir = os.path.join(self.user_dir, args[0])
    #     self.user_current_dir = user_dir
    #
    #     os.chdir(user_dir)
    #     now_dir = user_dir.split(os.sep)[-1]
    #     current_absdir = self.user_current_dir.join(now_dir)
    #     print("\033[33;1m current path: {}\033;0m".format(current_absdir))
    #
    # def mkdir(self, *args):
    #     '''
    #     新建文件夹
    #     :param args: 文件夹名
    #     :return: None
    #     '''
    #     new_dir_name = args[0]
    #
    #     if len(new_dir_name) > 0:
    #         pass




# class FTPServer(object):
#     '''
#     ftp 服务器处理程序，负责文件的收发，命令的处理
#     '''
#     def __init__(self, address, user):
#         pass


server = socketserver.ThreadingTCPServer(setting.ip_port, ServerRequestHandler, True)
server.serve_forever()