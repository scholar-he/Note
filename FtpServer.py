#! /usr/bin/python
# -*-coding:utf-8-*-

"""
本模块实现ftp的基本功能：实现FTP的登录/登出、判断远端文件是否存在、创建远端文件夹、上传单个文件、下载单个文件。
后续有业务需求可在本模块上继续扩展。
"""

import ftplib
import logging
import os
import socket

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d/%b/%Y %H:%M:%S')


class FtpClient(object):
    """
        实现FTP文件传输的相关操作
    """

    def __init__(self, host, port=21):
        self.host = host
        self.port = port
        self.ftp = ftplib.FTP()
        self.ftp.encoding = "gbk"
        self.logger = logging

    def login(self,username, password):
        try:
            timeout = 30
            socket.setdefaulttimeout(timeout)
            # 0 主动模式 1 #被动模式
            self.ftp.set_pasv(True)
            # 打开调试级别2，显示详细信息
            # self.ftp.set_debuglevel(2)
            self.logger.info("开始连接：< ftp://%s >" % self.host)
            self.ftp.connect(self.host, self.port)
            self.ftp.login(username, password)
            self.logger.info("连接成功：< ftp://%s >" % self.host)
            self.logger.info(self.ftp.welcome)
        except Exception as err:
            self.logger.error("FTP连接或登录失败，错误描述为：%s" % err)
            raise

    def close(self):
        self.ftp.quit()
        self.logger.info("FTP已断开连接")

    def isSameSize(self, localFile, remoteFile):
        """
            校验本地文件与远端文件大小是否一致
        Args:
            localFile：本地文件路径
            remoteFile: 远端文件路径
        Return:
            None
        Raises:
            None
        Example:
            res = self.ftp.isSameSize(localFile="D:/testftp.txt", remoteFile="/testftp.txt")
        """
        try:
            remoteFileSize = self.ftp.size(remoteFile)
        except Exception as err:
            # self.logger.error("isSameSize() 错误描述为：%s" % err)
            remoteFileSize = -1

        try:
            localFileSize = os.path.getsize(localFile)
        except Exception as err:
            # self.logger.error("isSameSize() 错误描述为：%s" % err)
            localFileSize = -1

        self.logger.info('localFileSize:%d  , localFileSize:%d' % (localFileSize, remoteFileSize))
        return True if localFileSize == localFileSize else False

    def doesFileExist(self, filePath):
        """
            判断文件路径是否存在
        Args:
            filePath：要校验的文件绝对路径
        Return:
            bool: True/False
        Raises:
            None
        Example:
            res = self.ftp.doesFilePathExist(filePath="/testdir/testfpt.txt")
        """
        if filePath.endswith("/"):
            filePath = filePath[:-1]
        dirname = os.path.dirname(filePath)
        try:
            self.ftp.cwd(dirname)
        except Exception as err:
            self.logger.warning("查找的文件或文件夹路径不存在：%s" % filePath)
            return False
        fileList = self.ftp.nlst(dirname)
        self.logger.info("路径<'%s'>下存在的文件列表：\n%s" % (self.ftp.pwd(), fileList))
        # 返回根目录
        self.ftp.cwd("/")
        return True if filePath in fileList else False

    def mkdir(self, dirPath):
        """
            创建文件夹，支持创建多层级文件夹
        Args:
            dirPath: 待创建文件夹绝对路径
        Return:
            bool：True/False
        Raises:
            None
        Example:
            self.mkdir("/testA/tetsB")
        """
        if self.doesFileExist(dirPath):
            self.logger.info("该路径已存在：%s" % dirPath)
            return True
        if not dirPath.startswith("/"):
            self.logger.error("待创建文件夹路径必须以根路径‘/’开始")
            return False
        self.ftp.cwd("/")
        self.logger.info("开始创建文件路径：%s" % dirPath)
        dirname = dirPath.split("/")
        for _ in dirname:
            if _ != "":
                try:
                    self.ftp.cwd(_)
                except Exception as err:
                    self.ftp.mkd(_)
                    self.ftp.cwd(_)
        self.logger.info("创建文件夹成功！")
        self.logger.info("当前工作路径：%s" % self.ftp.pwd())
        return True

    def downloadFile(self, localFile, remoteFile):
        """
            从FTP服务端下载单个文件
        Args:
            localFile: 指定下载到本地的文件路径
            remoteFile: 待下载的远端文件路径
        Return:
            None
        Raises:
            None
        Example:
            self.ftp.downloadFile(localFile="D:/testftp.txt", remoteFile="/testftp.txt")
        """
        if not self.doesFileExist(remoteFile):
            self.logger.error('%s 不存在' % remoteFile)
            return
        try:
            self.logger.info('>>>>>>>>>>>>下载文件 %s ... ...' % localFile)
            buf_size = 1024
            file_handler = open(localFile, 'wb')
            self.ftp.retrbinary('RETR %s' % remoteFile, file_handler.write, buf_size)
            file_handler.close()
            self.logger.info("下载文件成功")
        except Exception as err:
            self.logger.error('下载文件出错，出现异常：%s ' % err)
            return


    def putFile(self, localFile, remoteFile):
        """
            从本地上传单个文件到FTP服务端
        Args:
            localFile: 待上传的本地文件路径
            remoteFile: 指定将保存到的远端文件路径
        Return:
            None
        Raises:
            None
        Example:
            self.ftp.downloadFile(localFile="D:/testftp.txt", remoteFile="/testftp.txt")
        """
        if not os.path.isfile(localFile):
            self.logger.error('%s 不存在' % localFile)
            return
        try:
            buf_size = 1024
            file_handler = open(localFile, 'rb')
            self.ftp.storbinary('STOR %s' % remoteFile, file_handler, buf_size)
            file_handler.close()
            self.logger.info('上传: %s' % localFile + "成功!")
        except Exception as err:
            self.logger.error('下载文件出错，出现异常：%s ' % err)
            return


if __name__ == '__main__':
    ftp = FtpClient("10.10.10.101") # 此处修改FTP服务端的IP
    ftp.login(username="ftp_user", password="Admin@9000")

    # 创建文件夹
    # ftp.mkdir("/root/hecheng")

    # 下载文件
    ftp.downloadFile(localFile="myapp.log", remoteFile="/root/myapp.log")

    # 上传文件
    # ftp.putFile(localFile="myapp.log", remoteFile="/root/myapp.log")

    ftp.close()
