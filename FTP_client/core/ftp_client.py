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

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from conf import setting



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
                continue

            # 分析cmd，使用反射调用相关方法
            cmd = cmd_line.split()[0]
            if hasattr(self, cmd):
                func = getattr(self, cmd)

            if len(cmd_line.split()) > 1:
                param = cmd_line.split()[1]
                func(param)
            else:
                func()

    def login(self):
        '''
        登录操作，之后要求用户输入用户名和密码，以json格式发送给服务器端
        :return: boolean 是否登陆成功
        '''
        try:
            user_name = input("Please input user name: ").strip()
            password = input("Please input password: ").strip()
            password = FTPClient.md5_secret(password)
            login_dict = {"action" : "login",
                          "username" : user_name,
                          "password" : password}
            login_json = json.dumps(login_dict)
            # 向server端发送登录信息
            login_json = bytes(login_json, encoding="utf-8")
            info_len = len(login_json)
            self.client.send(bytes(info_len.__str__(), encoding='utf-8'))
            self.client.recv(1024)
            self.client.send(login_json)

            # 接收server端返回的登录信息
            data = self.client.recv(1024)  # 第一条消息接收返回信息长度
            info_len = int(data.decode('utf-8'))
            self.client.send(b"ready")
            recv_size = 0
            data = b""
            while recv_size < info_len:
                data += self.client.recv(setting.MAX_RECV_SIZE)  # 接收返回的登录信息
                recv_size = len(data)
            login_result = json.loads(data.decode())

            if login_result.get("result") == True:
                self.user_name = user_name
                self.user_dir = os.path.join(setting.HOME_DIR, user_name)
                sys.path.append(self.user_dir)  # 用户登陆成功，将用户的路径加入环境路径
                print("%d: Welcome back %s !" % (login_result.get("code"), self.user_name))
            else:
                print("%d: Oooh, log in failur, please try again. %s" % (login_result.get("code"), login_result.get("msg")))
                self.login()
        except (EOFError, KeyboardInterrupt):
            return

    def signup(self):
        '''
        新用户注册
        :return: None, 注册成功显示用户名，注册失败提示用户重试
        '''
        try:
            user_name = input("Please input user name: ").strip()
            password = input("Please input password: ").strip()  # 由于是明文输入，就不再再次输入确认密码了
            password = FTPClient.md5_secret(password)
            signup_dict = {"action": "signup",
                           "username": user_name,
                           "password": password}
            signup_json = json.dumps(signup_dict)
            # 向server发送注册信息
            signup_json = bytes(signup_json, encoding="utf-8")
            info_len = len(signup_json)
            self.client.send(bytes(info_len.__str__(), encoding='utf-8'))
            self.client.recv(1024)
            self.client.send(signup_json)

            # 接收server端返回的注册信息
            data = self.client.recv(1024)  # 第一条消息接收返回信息长度
            info_len = int(data.decode('utf-8'))
            self.client.send(b"ready")
            recv_size = 0
            data = b""
            while recv_size < info_len:
                data += self.client.recv(setting.MAX_RECV_SIZE)  # 接收返回的注册信息
                recv_size = len(data)
            signup_result = json.loads(data.decode())

            if signup_result.get("result") == True:
                self.user_name = signup_result.get("user_name")
                self.user_dir = os.path.join(setting.HOME_DIR, user_name)
                sys.path.append(self.user_dir)  # 新用户注册成功，用户路径加入系统路径
                print("%d: Congratulations %s, you have signded up successfully!" % (signup_result.get("code"), self.user_name))
            else:
                print("%d: Oooh, signup failure, please try again." % signup_result.get("code"))
                self.signup()
        except (EOFError, KeyboardInterrupt):
            return

    def logout(self):
        '''
        退出当前用户登录状态
        :return:
        '''
        logout_info = {"action": "logout",
                       "username": self.user_name}

        logout_info = bytes(json.dumps(logout_info), encoding='utf-8')
        info_len = len(logout_info)
        self.client.send(bytes(info_len.__str__(), encoding='utf-8'))
        self.client.recv(1024)
        self.client.send(logout_info)

        # 接收信息长度和信息内容
        data = self.client.recv(1024).decode()
        info_len = int(data)
        self.client.send(b'ready')
        recv_len = 0
        data = b""
        while recv_len < info_len:
            data += self.client.recv(setting.MAX_RECV_SIZE)
            recv_len = len(data)

        logout_result = json.loads(data.decode('utf-8'))
        if logout_result.get("result") == True:
            sys.path.remove(self.user_dir)
            print("%d: logout success!" % logout_result.get("code"))
        else:
            print("%d: logout failure! %s" % (logout_result.get("code"),logout_result.get("msg")))

    def put(self):
        '''
        客户端向服务器端上传文件
        :return:
        '''
        try:
            file_name = input("Please input the file's name you want upload: ")
        except (KeyboardInterrupt, EOFError):
            return
        # 判断用户输入的文件名是否存在
        file_path = os.path.join(self.user_dir, file_name)
        if not os.path.exists(file_path):
            print("The file name you inputted doesn't exist! Please try again")
            self.put()
        file_size = os.stat(file_path).st_size
        put_info = {"action": "put",
                    "username": self.user_name,
                    "filename": file_name,
                    "filesize": file_size}
        put_json = json.dumps(put_info)
        put_info = bytes(put_json, encoding='utf-8')
        info_len = len(put_info)
        self.client.send(bytes(info_len.__str__(), encoding='utf-8'))
        self.client.recv(1024)
        self.client.send(put_info)

        # 接收服务器端文件情况反馈，是否存在该文件，是否存在同名文件等情况
        data = self.client.recv(1024).decode()
        info_len = int(data)
        self.client.send(b"ready")
        recv_len = 0
        data = b""
        while recv_len < info_len:
            data += self.client.recv(setting.MAX_RECV_SIZE)
        put_result = json.loads(data.decode('utf-8'))
        # 根据服务器端文件情况作出不同操作

        if put_result.get("existed") == False:
            # 服务器端不存在该文件，直接上传
            # 发送文件大小
            print("file size: ", file_size)
            self.client.send(bytes(file_size, encoding='utf-8'))
            self.client.recv(1024)
            # 发送文件内容
            print("File starts uploading...")
            with open(file_path, 'rb') as f:
                for line in f:
                    self.client.send(line)
            print("File send over!")
        elif put_result.get("existed") == True and put_result.get("filesize") < file_size:
            # 如果客户端已经存在该文件，但是文件大小小于本地文件大小，继续上传（断点续传）
            # 发送文件大小
            server_size = put_result.get("filesize")  # 服务器端文件大小
            print("left size: ", file_size - server_size)
            self.client.send(bytes(file_size, encoding='utf-8'))
            self.client.recv(1024)
            # 发送文件内容
            print("File is on server but not complete, start breakpoint continuation...")
            with open(file_path, 'rb') as f:
                f.seek(server_size)  # 将文件的读取指针置于断点位置处
                for line in f:
                    self.client.send(line)
            print("File send over!")
        elif put_result.get("existed") == True and put_result.get("filesize") < file_size:
            # 如果服务器端已经存在该文件，且大小相同，则比较二者的md5值是否相同
            # 计算本地文件md5值
            md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for line in f:
                    md5.update(line)  # 一行行计算，防止文件一次被读入内存，占用过多空间
                md5_value = md5.hexdigest()
            server_file_md5 = put_result.get("md5")
            print("local file MD5: %s" % md5_value)
            print("server file MD5: %s" % server_file_md5)

            if md5_value == server_file_md5:
                # 如果相同，不上传文件
                self.client.send(b"0")  # 告诉服务器端要传输的文件大小为0
                self.client.recv(1024)
                self.client.send(b"")
                print("The file already exists on the server, no need to upload!")
            else:
                # 如果不同，重新上传文件
                print("file size: ", file_size)
                self.client.send(bytes(file_size, encoding='utf-8'))
                self.client.recv(1024)
                # 发送文件内容
                print("File starts reuploading...")
                with open(file_path, 'rb') as f:
                    for line in f:
                        self.client.send(line)
                print("File send over!")




        # TODO: 之后添加进度条功能，配额判断功能，断点续传功能, md5校验功能






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


if __name__ == "__main__":
    my_client = FTPClient()
    my_client.run()