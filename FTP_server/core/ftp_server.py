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
                data = self.request.recv(setting.MAX_RECV_SIZE).decode()
                print(data)
                info_len = int(data)
                recv_len = 0
                data = b""
                self.request.send(b"ready")
                while recv_len < info_len:
                    data += self.request.recv(setting.MAX_RECV_SIZE)
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
                print(err)
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
        with open("../conf/user_info.ini", "r", encoding="utf-8") as f:
            if len(f.read()) > 0:
                f.seek(0)
                all_user_info = json.load(f)
                print(all_user_info)
                if username in all_user_info:
                    user_info = all_user_info.get(username)
                    if user_info.get("password") == password:
                        result = {"result": True,
                                  "code": 200,
                                  "msg": "Login success!"}
                        print("\033[32;1m----- login success -----\033[0m")
                        sys.path.append(os.path.join(setting.HOME_DIR, username))  # 将用户路径添加到sys路径
                    else:
                        result = {"result": False,
                                  "code": 401,
                                  "msg": "Passwod error!"}
                        print("\033[31;1m----- login fail: wrong password -----\033[0m")
                else:
                    result = {"result": False,
                              "code": 400,
                              "msg": "No this user!"}
                    print("\033[31;1m----- login fail: no such user -----\033[0m")
        # 返回登录结果
        result_info = bytes(json.dumps(result), encoding='utf-8')
        self.request.send(bytes(len(result_info).__str__(), encoding='utf-8'))
        self.request.recv(setting.MAX_RECV_SIZE)
        self.request.send(result_info)

    def signup(self, info):
        '''
        创建新用户，将新用户信息加入配置文件
        :param info:
        :return:
        '''
        print(info)
        username = info.get("username")
        # 读取用户信息文件确认用户是否存在
        with open("../conf/user_info.ini", "r+", encoding="utf-8") as f:
            if len(f.read()) > 0:
                f.seek(0)
                all_user_info = json.load(f)
                print(all_user_info)
                if username in all_user_info:
                    result = {"result": False,
                              "code": 400,
                              "msg": "User has already existed!"}
                    print("\033[31;1m----- signup fail: user name already existed -----\033[0m")
                else:
                    info.pop("action")
                    new_user_info = {username: info}
                    all_user_info.update(new_user_info)
                    f.seek(0)  # 将文件指针移动到文件开始，覆盖原本的文件内容
                    json.dump(all_user_info, f)
                    result = {"result": True,
                              "code": 200,
                              "msg": "Congratulations, signup success!"}
                    print("\033[32;1m----- signup success -----\033[0m")
                    sys.path.append(os.path.join(setting.HOME_DIR, username))  # 将用户路径添加到sys路径

        # 返回登录结果
        result_info = bytes(json.dumps(result), encoding='utf-8')
        self.request.send(bytes(len(result_info).__str__(), encoding='utf-8'))
        self.request.recv(setting.MAX_RECV_SIZE)
        self.request.send(result_info)

    def logout(self, info):
        '''
        用户退出登录，服务器端从sys路径中移除用户的路径，结束当前连接
        :return:
        '''
        print(info)
        user_dir = os.path.join(setting.HOME_DIR, info.get("username"))
        print(user_dir)
        try:
            sys.path.remove(user_dir)
        except ValueError:
            result = {"result": False,
                      "code": 400,
                      "msg": "%s user not login!" % info.get("username")}
        else:
            result = {"result": True,
                      "code": 200}
        print("\033[31;1m----- logout success -----\033[0m")
        result_info = bytes(json.dumps(result), encoding='utf-8')
        info_len = len(result_info)
        self.request.send(bytes(info_len.__str__(), encoding='utf-8'))
        self.request.recv(1024)
        self.request.send(result_info)
        raise ConnectionResetError("user logout")





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