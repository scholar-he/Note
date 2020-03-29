#! /usr/bin/python
# -*-coding:utf-8-*-
"""
@Author: Tony 2513141027
@Date: 2019/9/30 22:31 
@Description: ssh登录
"""
import re
import time
import socket
import logging
import traceback
import threading

from paramiko import Transport, SFTPClient, SSHException, BadAuthenticationType
from paramiko.ssh_exception import  AuthenticationException

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

class SSHConnection(object):
    def __init__(self, hostip, username, password, port=22):
        self.hostip = hostip
        self.username = username
        self.password = password
        self.port = port
        self.logger = logging
        self.linesep = "\n"
        self.waitstr = "{}@#>".format(self.username)
        self.ansi_escape = re.compile(r'\x1B\[0-?]*[ -/]*[@_~]]')
        self.transport = None
        self.channel = None
        self.localParam = threading.local()

    def __del__(self):
        """
        垃圾回收时清理资源
        """
        self.close()

    def createSFTPClient(self):
        """
        创建SFTP通道
        """
        if self.transport is None or not self.transport.is_active():
            self.transport = self.createClient()
            self.authentication(self.transport)
        sftp = SFTPClient.from_transport(self.transport)
        return sftp

    def send(self, cmd, timeout=10):
        """
        下发命令到设备上
        """
        _result = False
        if not self.isActive():
            self.logger.warning("reconnecting...")
            self.reconnect()
            time.sleep(1)
        channel = self.channel
        for i in range(timeout):
            try:
                channel.send(cmd + self.linesep)
                self.logger.info("send cmd: {}".format(cmd))
            except socket.timeout as e:
                self.logger.warning("{} execute cmd: {} timeout".format(self.hostip, cmd))
                self.logger.exception(e)
                time.sleep(1)
            else:
                _result = True
                break
        return _result

    def recv(self, waitstr="[>$#]", nbytes=1024, timeout=30):
        """
        接收命令下发执行后的回显信息
        """
        isMatch = False
        recv = ""
        channel = self.channel
        startTm = time.time()
        warnMsg = ""
        while time.time() - startTm < timeout:
            try:
                strGet = channel.recv(nbytes) or b""
            except socket.timeout:
                if not warnMsg:
                    warnMsg = "{} echo is not received timeout".format(self.hostip)
                    self.logger.warning(warnMsg)
            except Exception as e:
                self.logger.exception(e)
                raise
            else:
                if strGet is not "":
                    recv += strGet.decode("utf-8")
                if re.search(waitstr, recv):
                    isMatch = True
                    break
            time.sleep(0.5)
        else:
            self.logger.warning("Did not receive '{}' until timeout({}s):\n{}".format(waitstr, timeout, recv))
        recv = self.ansi_escape.sub("", recv)
        return recv, isMatch

    def createClient(self):
        """
        创建SSH连接
        """
        event = threading.Event()
        for i in range(3):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.hostip, self.port))
                transport = Transport(sock)
                transport.start_client(event)
                event.wait(10)
                if not event.is_set():
                    self.logger.warning("{} start client timeout".format(self.hostip))
                    time.sleep(10)
                    continue
                if not transport.is_active():
                    self.logger.exception(socket.error)
                    raise socket.error
            except (socket.error, EOFError, SSHException) as e:
                if i != 2:
                    self.logger.warning("create connect to {}:{} failed".format(self.hostip, self.port))
                    sock.close()
                    time.sleep(3)
                else:
                    self.logger.error("create connect to {}:{} failed".format(self.hostip, self.port))
                    self.logger.exception(e)
                    raise
            else:
                return transport

    def authentication(self, transport):
        """
        身份验证
        """
        if not transport.is_authenticated():
            try:
                self.auth_password(transport)
            except BadAuthenticationType as e:
                self.logger.exception(e)
                raise
            self.logger.debug("{} login success".format(self.hostip))

    def auth_password(self, tranport):
        """
        密码验证
        """
        my_event = threading.Event()
        self.logger.info("logging ip: {}; username: {}; password: {}".format(self.hostip, self.username, self.password))
        tranport.auth_password(self.username, self.password, my_event)
        my_event.wait(120)
        if not my_event.is_set():
            self.logger.warning("authenticate timeout")
        if not tranport.is_authenticated():
            error = tranport.get_exception()
            if error is None:
                error = AuthenticationException("Authentication failed")
            self.logger.exception(error)
            raise error
    def login(self):
        """
        登录设备
        """
        if self.transport is None or not self.transport.is_active():
            self.transport = self.createClient()
        if self.transport is None:
            self.logger.error("create client error")
            return
        self.authentication(self.transport)
        channel = self.transport.open_session()
        channel.get_pty(width=200, height=200)
        channel.invoke_shell()
        channel.settimeout(10)
        self.channel = channel
        result, isMatch = self.recv(waitstr=r"[>$#]", timeout=5)
        if isMatch:
            self.logger.info("{} authenticate (password) successfully".format(self.hostip))
        else:
            self.logger.warning("Has not get the command promote yet at this connection")
        self.execCommand(r"PS1='\u@#>'", waitstr=self.waitstr, timeout=5)

    def isActive(self):
        """
        判断当前连接是否断开
        """
        return not self.channel.closed if self.channel else False

    def close(self):
        """
        断开连接
        """
        if self.transport:
            self.transport.close()
            self.transport = None
            self.channel = None

    def execCommand(self, cmd, waitstr=".*@#>", timeout=60, nbytes = 32768):
        return self.recv(waitstr, nbytes, timeout) if self.send(cmd, timeout=10) else (None, False)

    def reconnect(self):
        """
        重连
        """
        self.close()
        self.login()

    def run(self, command, waitstr=None, inPut=None, timeout=60):
        stdout = ""
        if waitstr is None:
            waitstr = self.waitstr
        if inPut is None:
            cmdList = [(command, waitstr)]
        else:
            inPut.insert(0, command)
            inPut.append(waitstr)
            cmdList = [(inPut[i], "{}|{}".format(inPut[i+1], waitstr)) for i in range(0, len(inPut), 2)]
        for cmd, waitstr in cmdList:
            tmpres, isMatch = self.execCommand(cmd, waitstr=waitstr, timeout=timeout)
            if not timeout:
                break
            if tmpres:
                stdout += tmpres
            else:
                self.logger.error("{} cmd: <{}> recv nothing".format(self.hostip, cmd))
        self.logger.debug(re.sub(r"\r", "", stdout))
        return re.sub(r"\s*\r|{}".format(waitstr), "", stdout).replace(command, "").strip()

    def getFile(self, src, dst):
        """
        下载文件
        """
        sftp = self.createSFTPClient()
        self.localParam.rate = 0
        try:
            sftp.get(src, dst, self.callback)
        except Exception:
            self.logger.error("file transfer failed.\n{}".format(traceback.format_exc()))
            return False
        finally:
            sftp.close()
        return True

    def putFile(self, src, dst):
        """
        上传文件
        """
        sftp = self.createSFTPClient()
        self.localParam.rate = 0
        try:
            sftp.put(src, dst, self.callback)
        except Exception:
            self.logger.error("file transfer failed.\n{}".format(traceback.format_exc()))
            return False
        finally:
            sftp.close()
        return True


    def callback(self, sended, total):
        """
        文件传输回调函数
        """
        if total ==0:
            return
        if sended == total:
            self.logger.info("file transfer success.")
            return
        i = (round(sended) / round(total)) * 100
        if i - self.localParam.rate < 1:
            return
        self.localParam.rate = i
        self.logger.info("file size: %dB, sended: %dB, rate: %dB" % (total, sended, i))


if __name__ == '__main__':
    hostip = "192.168.1.102"
    username = "hecheng"
    password = "Hc232017."
    ssh = SSHConnection(hostip, username, password)
    ssh.login()
    print(ssh.run("ifconfig -a"))
