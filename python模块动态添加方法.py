# Description: 给对象动态加载方法

# Server.py
import os
import sys

class Server(object):

    def __init__(self):
        self.__initMethods()

    def __initMethods(self):
        filePath = os.path.dirname(os.path.realpath(__file__))
        files = os.listdir(filePath)
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                importPath = ".".join(["Demo", file[:-3]])
                __import__(importPath)
                methods = dir(sys.modules[importPath])
                for method in methods:
                    if not method.startswith("__"):
                        m = getattr(sys.modules[importPath], method)
                        setattr(Server, method, m)

if __name__ == '__main__':
    s = Server()
    s.MyPrint()
    
    
  
# Methods.py
def MyPrint(self):
    print("动态绑定方法成功")
