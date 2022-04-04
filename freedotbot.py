import json
import os
import random
import time
from multiprocessing import Process, Queue
import threading
import websocket
from pywebio import start_server
from pywebio.output import *
from pywebio.input import *
from pywebio.session import register_thread


def chat_json(text):
    '''
    将发送到消息组装成数据
    '''
    return json.dumps({"cmd": "chat", "text": str(text)})


class MsgHandler:
    def __init__(self, chatroom, botname, main):
        self.chatroom = chatroom
        self.botname = botname
        self.main = main

    def set_ws(self, ws):
        '''
        设置自身websocket对象
        '''
        self.ws = ws

    def sendchat(self, msg):
        '''
        发送聊天消息
        '''
        self.ws.send(chat_json(msg))

    def wsendchat(self, msg):
        '''
        用私聊命令发送聊天消息
        '''
        self.sendchat("/whisper {} {}".format(self.nick, msg))

    def get_data(self, key):
        '''
        从json数据获取信息，没有这条信息则返回空值
        '''
        key = str(key)
        if key in self.ms_data:
            result = self.ms_data[key]
        else:
            result = None
        return result

    def handle(self, ms_data):
        '''
        处理服务器返回数据
        '''
        # 获取各条所需数据
        self.ms_data = ms_data
        self.cmdtype = self.get_data("cmd")
        self.nick = self.get_data("nick")
        self.text = self.get_data("text")
        self.color = self.get_data("color")
        self.color = self.get_data("color")
        self.trip = self.get_data("trip")
        self.nicks = self.get_data("nicks")
        # 根据不同消息类型，调用对应方法
        if not self.cmdtype == None:
            if self.cmdtype == "chat":
                self.chat()
            elif self.cmdtype == "onlineAdd":
                self.onlineAdd()
            elif self.cmdtype == "onlineSet":
                self.onlineSet()
            elif self.cmdtype == "onlineRemove":
                self.onlineRemove()
            else:
                pass

    def chat(self):
        '''
        当有人说话时调用
        '''
        self.main.emote("{}: {}".format(self.nick, self.text))

    def onlineAdd(self):
        '''
        当有人加入时调用
        '''
        self.onlineusers.append(self.nick)
        self.main.emote("*{} join".format(self.nick))

    def onlineSet(self):
        '''
        当返回在线名单时（加入新房间时）调用
        '''
        self.onlineusers = self.nicks
        self.sendchat("/color #ffffff")
        #self.sendchat(
        #    "I am free-dotbot. Maybe one day I can be used to battle foolishbird! ")

    def onlineRemove(self):
        '''
        当有人离开时调用
        '''
        self.onlineusers.remove(self.nick)
        self.main.emote("*{} left".format(self.nick))


class BotMain:  # 提供各种功能，接收websocket服务器的信息
    def __init__(self, chatroom, botname,show_msg_queue,send_msg_queue,bot_ctrl_queue):
        self.chatroom = chatroom
        self.botname = botname
        self.show_msg_queue=show_msg_queue
        self.send_msg_queue=send_msg_queue
        self.bot_ctrl_queue=bot_ctrl_queue
        self.init_time = time.strftime("%Y-%m-%d %H_%M_%S", time.localtime())
        self.logpath = './log/'+self.chatroom+' '+self.init_time+'.txt'
        with open(self.logpath, 'x') as log:  # 创建日志文件
            pass
        self.msghandler = MsgHandler(chatroom, botname, self)
    
    def send_input_msg(self):
        while True:
            if not self.send_msg_queue.empty():
                self.msghandler.sendchat(self.send_msg_queue.get())
    
    def exec_bot_ctrl(self):
        while True:
            if not self.bot_ctrl_queue.empty():
                self.ctrl_cmd=self.send_input_msg.get()
                pass

    def on_open(self, ws):
        '''
        成功与服务器建立连接时调用
        '''
        self.send_input_msg_t=threading.Thread(target=self.send_input_msg)
        self.exec_bot_ctrl_t=threading.Thread(target=self.exec_bot_ctrl)
        self.send_input_msg_t.start()
        self.exec_bot_ctrl_t.start()
        ws.send(json.dumps({"cmd": "join", "channel": str(
            self.chatroom), "nick": str(self.botname)}))
        self.msghandler.set_ws(ws)

    def on_close(self, ws):
        '''
        被服务器踢出时调用
        '''
        self.emote("###closed")

    def on_error(self, ws, error):
        '''
        发生错误时调用
        '''
        self.emote("###error: {}".format(error))

    def on_message(self, ws, message):
        '''
        服务器发送来数据时调用
        '''
        ms_data = json.loads(message)
        self.msghandler.handle(ms_data)

    def emote(self, text):
        '''
        显示信息。如果有条件，可以自行更改显示的方式。
        '''
        text = str(text)
        self.show_msg_queue.put(text)
        with open(self.logpath, 'a') as chatHistory:
            if os.path.getsize(self.logpath) < 1024576:
                chatHistory.write(text + "\n")


class BotProc(Process):  # bot运行进程
    def __init__(self, chatroom, botname,show_msg_queue,send_msg_queue,bot_ctrl_queue):
        Process.__init__(self)  # 初始化进程
        self.show_msg_queue=show_msg_queue
        self.send_msg_queue=send_msg_queue
        self.bot_ctrl_queue=bot_ctrl_queue
        self.main = BotMain(chatroom=chatroom, botname=botname,show_msg_queue=show_msg_queue,send_msg_queue=send_msg_queue,bot_ctrl_queue=bot_ctrl_queue)  # 设置main模块

    def run(self):
        '''
        定义进程活动：连接hack.chat服务器
        '''
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp("wss://hack.chat/chat-ws", on_message=self.main.on_message,
                                    on_error=self.main.on_error, on_close=self.main.on_close)  # 会自动调用BotMain中的方法
        ws.on_open = self.main.on_open
        ws.run_forever()

class UIProc(Process):
    def __init__(self,show_msg_queue,send_msg_queue,bot_ctrl_queue):
        Process.__init__(self)
        self.show_msg_queue=show_msg_queue
        self.send_msg_queue=send_msg_queue
        self.bot_ctrl_queue=bot_ctrl_queue

    def runUI(self):
        self.get_input_t=threading.Thread(target=self.get_input_msg)
        self.read_chat_t=threading.Thread(target=self.get_chat_msg)
        register_thread(self.get_input_t)#在子线程中使用PyWebIO必须进行这一步
        register_thread(self.read_chat_t)#https://pywebio.readthedocs.io/zh_CN/latest/guide.html#thread-in-server-mode
        self.get_input_t.start()
        self.read_chat_t.start()
        put_scrollable(put_scope('chatscope'), height=600, keep_bottom=True)

    def get_input_msg(self):
        '''
        将界面输入框里的内容发送到队列
        '''
        while True:
            msg=input(type=TEXT)
            if not msg == "":
                self.send_msg_queue.put(msg)
    
    def get_chat_msg(self):
        '''
        获取队列中的消息
        '''
        while True:
            if not self.show_msg_queue.empty():
                put_text(self.show_msg_queue.get(), scope='chatscope')#get()函数会自动删除队列的最后一项。

    def run(self):
        '''
        定义进程活动：显示界面
        '''
        start_server(self.runUI, port=8080, debug=True)#PyWebIO支持script模式与server模式，此处为server模式。


if __name__ == '__main__':
    hcroom = 'yc'
    if hcroom == 'yc':
        hcroom = 'your-channel'
    elif hcroom == 'ts':
        hcroom = 'test'
    elif hcroom.lower() == 'cn':
        hcroom = 'chinese'
    send_msg_queue = Queue()
    show_msg_queue = Queue()
    bot_ctrl_queue = Queue()
    botproc = BotProc(chatroom=hcroom, botname="dotbot",show_msg_queue=show_msg_queue,send_msg_queue=send_msg_queue,bot_ctrl_queue=bot_ctrl_queue)
    uiproc=UIProc(show_msg_queue=show_msg_queue,send_msg_queue=send_msg_queue,bot_ctrl_queue=bot_ctrl_queue)
    botproc.start()
    uiproc.start()
    botproc.join()
    uiproc.join()
