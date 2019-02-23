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
    user_cur_dir = None

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
                self.user_cur_dir = self.user_dir
                sys.path.append(self.user_dir)  # 用户登陆成功，将用户的路径加入环境路径
                os.chdir(self.user_dir)
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

            print(signup_result)
            if signup_result.get("result") == True:
                self.user_name = signup_result.get("username")
                self.user_dir = os.path.join(setting.HOME_DIR, user_name)
                self.user_cur_dir = self.user_dir
                sys.path.append(self.user_dir)  # 新用户注册成功，用户路径加入系统路径
                print(self.user_dir)
                os.makedirs(self.user_dir)  # 为用户创建目录
                os.chdir(self.user_dir)
                print("%d: Congratulations %s, you have signded up successfully!" % (signup_result.get("code"), self.user_name))
            else:
                print("%d: Oooh, signup failure. %s" % (signup_result.get("code"), signup_result.get("msg")))
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
            print("%d: logout failure! %s" % (logout_result.get("code"), logout_result.get("msg")))

    def put(self):
        '''
        客户端向服务器端上传文件
        :return:
        '''
        if self.user_name == None:
            print("Please login first: login")
            return
        try:
            file_name = input("Please input the file's name you want upload: ")
        except (KeyboardInterrupt, EOFError):
            return
        # 判断用户输入的文件名是否存在
        file_path = os.path.join(self.user_cur_dir, file_name)
        # file_name = file_path.split(self.user_name)[1]
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
        print(info_len)
        self.client.send(b"ready")
        recv_len = 0
        data = b""
        while recv_len < info_len:
            data += self.client.recv(setting.MAX_RECV_SIZE)
            recv_len = len(data)
        put_result = json.loads(data.decode('utf-8'))
        # 根据服务器端文件情况作出不同操作
        print(put_result)
        if put_result.get("existed") == False:
            # 服务器端不存在该文件，直接上传
            # 发送文件大小
            print("file size: ", file_size)
            self.client.send(bytes(file_size.__str__(), encoding='utf-8'))
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
            self.client.send(bytes(file_size.__str__(), encoding='utf-8'))
            self.client.recv(1024)
            # 发送文件内容
            print("File is on server but not complete, start breakpoint continuation...")
            with open(file_path, 'rb') as f:
                f.seek(server_size)  # 将文件的读取指针置于断点位置处
                print("cursor location: ", f.tell())
                for line in f:
                    self.client.send(line)
            print("File send over!")
        elif put_result.get("existed") == True and put_result.get("filesize") >= file_size:
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
                print("The file already existed on the server, no need to upload!")
            else:
                # 如果不同，重新上传文件
                print("file size: ", file_size)
                self.client.send(bytes(file_size.__str__(), encoding='utf-8'))
                self.client.recv(1024)
                # 发送文件内容
                print("File starts reuploading...")
                with open(file_path, 'rb') as f:
                    for line in f:
                        self.client.send(line)
                print("File send over!")




        # TODO: 之后添加进度条功能，配额判断功能

    def get(self):
        """
        从服务器获取文件，发送到客户端，文件传输情况与put类似
        :return:  None
        """
        pass

    def ls(self):
        """
        列出用户本地目录下的文件
        :return:
        """
        list_result = os.listdir(self.user_cur_dir)
        print(list_result)

    def ls_remote(self):
        """
        列出用户服务器端的目录下的文件
        :return:
        """
        # if self.user_cur_dir.endswith(self.user_name):
        #     path = ""
        # else:
        #     path = self.user_cur_dir.split(self.user_name)[1]

        ls_info = {"action": "ls",
                   "username": self.user_name}
        ls_info_json = json.dumps(ls_info)
        ls_info_bytes = bytes(ls_info_json, encoding='utf-8')
        info_len = len(ls_info_bytes)
        self.client.send(bytes(info_len.__str__(), encoding='utf-8'))
        self.client.recv(1024)
        self.client.send(ls_info_bytes)
        # 接收返回
        result_len = int(self.client.recv(setting.MAX_RECV_SIZE).decode())
        self.client.send(b"ready")
        recv_len = 0
        data = b""
        while recv_len < result_len:
            data += self.client.recv(setting.MAX_RECV_SIZE)
            recv_len = len(data)
        print(json.loads(data.decode()).get("ls"))

    def cd(self):
        """
        打开用户本地下的某一文件夹
        :param floder:
        :return:
        """
        print("current location: ", self.user_cur_dir)
        try:
            folder = input("input the folder name: ")
            os.chdir(os.path.join(self.user_cur_dir, folder))
        except FileNotFoundError as e:
            print("当前目录下未找到%s文件夹！" % folder)
        except NotADirectoryError as e:
            print("%s 不是文件夹" % folder)
        else:
            self.user_cur_dir = os.getcwd()
            print("current location: ", self.user_cur_dir)

    def cd_remote(self):
        """
        打开用户服务器端的某一文件夹
        :return:
        """
        folder = input("input the folder name: ")
        cd_info = {"action": "cd",
                   "username": self.user_name,
                   "path": folder}
        cd_json = json.dumps(cd_info)
        cd_bytes = bytes(cd_json, encoding='utf-8')
        info_len = len(cd_bytes)
        self.client.send(bytes(info_len.__str__(), encoding='utf-8'))
        self.client.recv(1024)
        self.client.send(cd_bytes)
        # 接收返回
        result_len = int(self.client.recv(setting.MAX_RECV_SIZE).decode())
        self.client.send(b"ready")
        data = b""
        recv_len = 0
        while recv_len < result_len:
            data += self.client.recv(setting.MAX_RECV_SIZE)
            recv_len = len(data)
        result = json.loads(data)

        print("%d: %s" %(result.get("code"), result.get("msg")))

    def pwd(self):
        """
        获取当前位置
        :return:
        """
        print("current location: ", os.getcwd())

    def pwd_remote(self):
        """
        获取服务器上的额当前位置
        :return:
        """
        pwd_dict = {"action": "pwd",
                    "username": self.user_name}
        pwd_json = json.dumps(pwd_dict)
        pwd_bytes = bytes(pwd_json, encoding='utf-8')
        pwd_len = len(pwd_bytes)
        self.client.send(bytes(pwd_len.__str__(), encoding='utf-8'))
        self.client.recv(1024)
        self.client.send(pwd_bytes)
        # 接收返回
        result_len = int(self.client.recv(setting.MAX_RECV_SIZE).decode())
        self.client.send(b"ready")
        data = b""
        recv_len = 0
        while recv_len < result_len:
            data += self.client.recv(setting.MAX_RECV_SIZE)
            recv_len = len(data)
        result = data.decode()
        result_json = json.loads(result)
        print("%s: %s" % (result_json.get("code"), result_json.get("pwd")))

    def mkdir(self):
        """
        本地创建文件夹
        :return:
        """
        folder_name = input("input folder name: ")
        try:
            os.makedirs(folder_name)
        except FileExistsError:
            print("the folder name already existed! ")
        except:
            print("make dir error")
        else:
            print("make dir %s success" % folder_name)

    def mkdir_remote(self):
        """
        在服务器端创建文件夹
        :return:
        """
        folder_name = input("input folder name: ")
        mkdir_dict = {"action": "mkdir",
                      "usernaem": self.user_name,
                      "path": folder_name}
        mkdir_json = json.dumps(mkdir_dict)
        mkdir_bytes = bytes(mkdir_json, encoding='utf-8')
        mkdir_len = len(mkdir_bytes)
        self.client.send(bytes(mkdir_len.__str__(), encoding='utf-8'))
        self.client.recv(1024)
        self.client.send(mkdir_bytes)
        # 接受返回
        result_len = int(self.client.recv(setting.MAX_RECV_SIZE).decode())
        self.client.send(b"ready")
        data = b""
        recv_len = 0
        while recv_len < result_len:
            data += self.client.recv(setting.MAX_RECV_SIZE)
            recv_len = len(data)
        result = data.decode()
        result_json = json.loads(result)
        print("%s: %s" %(result_json.get("code")), result_json("msg"))



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