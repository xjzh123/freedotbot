import json
import os
import random
import time
from multiprocessing import Process, Queue
import threading
import websocket
import pywebio as ui
import simpchess
import nest_asyncio  # https://www.markhneedham.com/blog/2019/05/10/jupyter-runtimeerror-this-event-loop-is-already-running/


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
        self.logpath = self.main.logpath
        self.is_playing = False
        self.colordict = {
            '404r': 'ff5722',
            'r': 'ff5722',
            '404b': 'c0ffee',
            'b': 'c0ffee',
            'g': '99c21d',
            'wikidot': 'f02727',
            'vscode': '007acc'
        }

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

    def wsendchat(self, msg, nick=None):
        '''
        用私聊命令发送聊天消息
        '''
        if nick == None:
            nick = self.nick
        self.sendchat("/whisper {} {}".format(nick, msg))

    def get_data(self, key, json_data=None):
        '''
        从json数据获取信息，没有这条信息则返回空值
        '''
        if json_data == None:
            json_data = self.ms_data
        key = str(key)
        if key in json_data:
            result = json_data[key]
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
        self.trip = self.get_data("trip")
        self.nicks = self.get_data("nicks")
        self.users = self.get_data("users")
        # 根据不同消息类型，调用对应方法
        if not self.cmdtype == None:
            if self.cmdtype == "chat":
                self.chat()
            elif self.cmdtype == "info":
                self.info()
            elif self.cmdtype == "emote":
                self.emote()
            elif self.cmdtype == "onlineAdd":
                self.onlineAdd()
            elif self.cmdtype == "onlineSet":
                self.onlineSet()
            elif self.cmdtype == "onlineRemove":
                self.onlineRemove()
            else:
                pass
        self.get_user_info()

    def get_user_info(self):
        if not self.color == None and not self.color == False:
            if not self.nick in self.colordict.keys():
                self.colordict[self.nick] = self.color
            elif self.colordict[self.nick] != self.color:
                self.colordict[self.nick] = self.color

    def chat(self):
        '''
        当有人说话时调用
        '''
        self.main.show("{}: {}".format(self.nick, self.text))
        if self.text[0:1] == '.':
            self.chatcommand(self.text)
        if self.trip == 'p4AXF2' or self.trip == 'xmv2c1':
            # against a spammer with this trip. ignore or delete this function if it is no longer necessary. 
            self.sendchat('@{} 狗叫呢？'.format(self.nick))
            self.wsendchat('''# 狗再叫\n$$\Huge\color{red}{狗再叫}$$\n>>>>>>>>>>>>>>>>>>>># ==再来给你爹叫一个啊狗儿子狗儿子狗儿子狗儿子狗儿子狗儿子狗儿子狗儿子狗儿子狗儿子狗儿子狗狗儿子==''')

    def info(self):
        '''
        当有信息显示（私信）时调用
        '''
        self.main.show("*{}".format(self.text))

    def emote(self):
        '''
        当有旁白显示（/me）时调用
        '''
        self.main.show("*{}".format(self.text))

    def onlineAdd(self):
        '''
        当有人加入时调用
        '''
        self.onlineusers.append(self.nick)
        #self.sendchat("Hello {}. I am a bot. ".format(self.nick))
        self.wsendchat(
            "To Chinese users: 在your-channel，可以试试说中文哦。建议新人点击链接看看[我写的wiki](https://hcwiki.github.io)。\nTo Other users: if it occurs that everybody is speaking Chinese, you can go to ?programming. There most users speak English. Or, staying here is welcome too! ")
        self.main.show("*{} join".format(self.nick))

    def onlineSet(self):
        '''
        当返回在线名单时（加入新房间时）调用
        '''
        for user_data in self.users:
            self.nick = self.get_data("nick", user_data)
            self.color = self.get_data("color", user_data)
            self.get_user_info()
        self.onlineusers = self.nicks
        self.sendchat("/color #ffffff")
        # self.sendchat(
        #    "I am free-dotbot. Maybe one day I can be used to battle foolishbird! ")

    def onlineRemove(self):
        '''
        当有人离开时调用
        '''
        self.onlineusers.remove(self.nick)
        self.main.show("*{} left".format(self.nick))

    def chatcommand(self, text):
        '''
                处理聊天命令
        '''
        ccmdtxt = text.replace('.', '', 1)
        ccmdlist = ccmdtxt.split(' ', 1)
        ccmd = ccmdlist[0]
        if len(ccmdlist) > 1:
            cobj = ccmdlist[1]
        else:
            cobj = ''
        if ccmd == '':  # 防止“.”触发命令
            pass
        elif '.' in ccmd:  # 防止“...”触发命令
            pass
        elif ccmd == 'help':  # 命令帮助
            help_text = '\n'.join([
                '## [.] + command name + command obj = command',
                '|command name<other names>|command obj|command effect|',
                '|----|----|----|',
                '|color<c>|[the nickname of a user whose nickname has special color]|Gives you a command to change the color of your name. |',
                '|history<h>|[a number from 1 to how many messages dotbot can show]|Shows you messages which are sent before you use this command. |',
                '|r|[1 or 2 int for the minimal and maximal result]|Random int. |',
                '|chess|[no object]|Play Chinese Chess in chat room!|',
                '|2player|[no object]|Join the Chess game!|',
                '|p|[x]&[y]of piece [x]&[y] of destination|Move your piece on the Chess board!|',
                '|end_game|[no object]|End the game!|',
                '|help|[no object]|Shows this doc. |',
                '|[more]|[to be developed]|[in the future.]|'
            ])
            self.wsendchat(help_text)

        elif ccmd == 'c' or ccmd == 'color':  # 快速获取颜色代码
            cobj = cobj.lstrip('@').rstrip()
            if cobj in self.colordict.keys():
                getcolor = self.colordict[cobj]
                self.wsendchat("`/color #{}`".format(getcolor))
            else:
                self.wsendchat("Please give correct parameter.")

        elif ccmd == 'history' or ccmd == 'h':  # 聊天记录查询功能
            if cobj.isdigit() == True and len(cobj) > 0:
                cobj = int(cobj)
                # 如果聊天记录小于1mb
                if os.path.getsize(self.logpath) < 1024576:
                    with open(self.logpath, 'r') as chatHistory:
                        historyList = chatHistory.readlines()
                        if cobj >= 1 and cobj <= len(historyList):
                            chstr = ''.join(historyList[-cobj-1:-1])
                            self.wsendchat("Showing {} messages: \n".format(str(cobj))+chstr)
                        else:
                            self.wsendchat(
                                "Only {} messages logged. Can't show {}. ".format(str(len(historyList)), str(cobj)))
                else:
                    self.wsendchat("Log file is too big! Refuse to read or write log. ")
            else:
                self.wsendchat("Please give leagal parameter. ")
        elif ccmd == 'online' or ccmd == 'o':
            self.wsendchat('Online user: '+','.join(self.onlineuser))
        elif ccmd == 'chess':
            if self.is_playing == False:
                self.p1 = self.nick
                self.is_playing = -1
                self.player = 1
                simpchess.set_callback(self)
                simpchess.generate_pieces()
                simpchess.main.getMap()
                self.sendchat('发送“.2player”加入游戏')
            else:
                self.sendchat('当前游戏已经在进行')
        elif ccmd == '2player':
            if self.is_playing == -1:
                self.p2 = self.nick
                self.sendchat('成功加入游戏')
                self.is_playing = 1
            else:
                self.sendchat('当前没有开始游戏或游戏已经在进行')
        elif ccmd == 'p':
            if self.is_playing == 1:
                if self.player == 1:
                    if self.nick == self.p1:
                        move_success = simpchess.consolePlay(cobj,1)
                        if move_success:
                            self.player = -1
                else:
                    if self.nick == self.p2:
                        move_success = simpchess.consolePlay(cobj,-1)
                        if move_success:
                            self.player = 1
        elif ccmd == 'end_game':
            self.is_playing = False
            self.sendchat('已结束游戏')
        elif ccmd == 'chess_board':
            if self.is_playing == 1:
                simpchess.main.getMap()

        elif ccmd == 'r':
            if cobj == '':
                self.sendchat(random.randint(0,1024))
            else:
                cobj_list = cobj.split()
                if len(cobj_list) == 1 and cobj.isdigit():
                    cobj = int(cobj)
                    self.sendchat(random.randint(min(0,cobj),max(0,cobj)))
                elif len(cobj_list) == 2 and cobj_list[0].isdigit() and cobj_list[1].isdigit():
                    int1 = int(cobj_list[0])
                    int2 = int(cobj_list[1])
                    self.sendchat(random.randint(min(int1,int2),max(int1,int2)))
        elif ccmd == 'getobj':
            self.sendchat('obj:[{}]'.format(cobj))
        else:
            self.wsendchat(
                'Unknown dotbot command. Use ".help" to get help for dotbot commands. ')  # 未知命令


class BotMain:  # 提供各种功能，接收websocket服务器的信息
    def __init__(self, chatroom, botname, show_msg_queue, send_msg_queue, bot_ctrl_queue, cloud_mode):
        self.chatroom = chatroom
        self.botname = botname
        self.show_msg_queue = show_msg_queue
        self.send_msg_queue = send_msg_queue
        self.bot_ctrl_queue = bot_ctrl_queue
        self.cloud_mode = cloud_mode
        self.init_time = time.strftime("%Y-%m-%d %H_%M_%S", time.localtime())
        self.logpath = './log/{} {}.txt'.format(self.chatroom, self.init_time)
        with open(self.logpath, 'w') as log:  # 创建日志文件
            pass
        self.msghandler = MsgHandler(chatroom, botname, self)

    def send_input_msg(self):
        while True:
            if not self.send_msg_queue.empty():
                self.msghandler.sendchat(self.send_msg_queue.get())

    def exec_bot_ctrl(self):
        while True:
            if not self.bot_ctrl_queue.empty():
                self.ctrl_cmd = self.send_input_msg.get()
                pass

    def on_open(self, ws):
        '''
        成功与服务器建立连接时调用
        '''
        self.send_input_msg_t = threading.Thread(target=self.send_input_msg)
        #self.exec_bot_ctrl_t = threading.Thread(target=self.exec_bot_ctrl)
        self.send_input_msg_t.start()
        # self.exec_bot_ctrl_t.start()
        ws.send(json.dumps({"cmd": "join", "channel": str(
            self.chatroom), "nick": str(self.botname)}))
        self.msghandler.set_ws(ws)

    def on_close(self, ws, arg1=None, arg2=None):
        '''
        被服务器踢出时调用
        '''
        try:
            closearg = "arg1:[{}]arg2:[{}]".format(str(arg1), str(arg2))
        except:
            closearg = ""
        self.show("###closed "+str(closearg))

    def on_error(self, ws, error):
        '''
        发生错误时调用
        '''
        self.show("###error: {}".format(error))

    def on_message(self, ws, message):
        '''
        服务器发送来数据时调用
        '''
        ms_data = json.loads(message)
        self.msghandler.handle(ms_data)

    def show(self, text):
        '''
        显示信息。
        '''
        text = str(text)
        self.show_msg_queue.put(text)
        with open(self.logpath, 'a') as chatHistory:  # 记录日志
            if os.path.getsize(self.logpath) < 1024576:
                chatHistory.write(text + "\n")


class BotProc(Process):  # bot运行进程
    def __init__(self, chatroom, botname, show_msg_queue, send_msg_queue, bot_ctrl_queue, cloud_mode):
        Process.__init__(self)  # 初始化进程
        self.cloud_mode = cloud_mode
        self.main = BotMain(chatroom=chatroom, botname=botname, show_msg_queue=show_msg_queue,
                            send_msg_queue=send_msg_queue, bot_ctrl_queue=bot_ctrl_queue, cloud_mode=cloud_mode)  # 设置main模块

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
    def __init__(self, show_msg_queue, send_msg_queue, bot_ctrl_queue, cloud_mode):
        Process.__init__(self)
        self.show_msg_queue = show_msg_queue
        self.send_msg_queue = send_msg_queue
        self.bot_ctrl_queue = bot_ctrl_queue
        self.cloud_mode = cloud_mode

    def runUI(self):
        self.get_input_t = threading.Thread(target=self.get_input_msg)
        self.read_chat_t = threading.Thread(target=self.get_chat_msg)
        ui.session.register_thread(self.get_input_t)  # 在子线程中使用PyWebIO必须进行这一步
        # https://pywebio.readthedocs.io/zh_CN/latest/guide.html#thread-in-server-mode
        ui.session.register_thread(self.read_chat_t)
        self.get_input_t.start()
        self.read_chat_t.start()
        ui.output.put_scrollable(ui.output.put_scope(
            'chatscope'), height=600, keep_bottom=True)

    def get_input_msg(self):
        '''
        将界面输入框里的内容发送到队列
        '''
        while True:
            msg = ui.input.input(type='text')
            if not msg == "":
                self.send_msg_queue.put(msg)

    def get_chat_msg(self):
        '''
        获取队列中的消息
        '''
        while True:
            if not self.show_msg_queue.empty():
                ui.output.put_text(self.show_msg_queue.get(),
                                   scope='chatscope')  # get()函数会自动删除队列的最后一项。

    def run(self):
        '''
        定义进程活动：显示界面
        '''
        print('Starting UI...')
        ui.start_server(self.runUI, port=8080, debug=True,
                        remote_access=False)  # PyWebIO支持script模式与server模式，此处为server模式。


if __name__ == '__main__':  # 使用多进程时必须使用。见https://www.cnblogs.com/wFrancow/p/8511711.html\
    # notebook模式开关。notebook模式下，禁用UI，启用notebook优化
    nest_asyncio.apply()
    print("----DotBot Running----")
    print("Current path: {}".format(os.path.abspath('.')))
    with open("cloud_config.json") as config_json:
        cloud_config = json.loads(config_json.read())
        cloud_mode = cloud_config["is_heroku"]
    if cloud_mode == True:
        hcroom = cloud_config["room"]
    else:
        roomdict = {"yc":"your-channel","ts":"test","cn":"chinese","purg":"purgatory"}
        hcroom = input("Please input room name (or abbreviation) here: ")
        if hcroom in roomdict:
            hcroom = roomdict[hcroom]
    send_msg_queue = Queue()
    show_msg_queue = Queue()
    #bot_ctrl_queue = Queue()
    botproc = BotProc(chatroom=hcroom, botname="dotbot", show_msg_queue=show_msg_queue,
                      send_msg_queue=send_msg_queue, bot_ctrl_queue=None, cloud_mode=cloud_mode)
    uiproc = UIProc(show_msg_queue=show_msg_queue,
                    send_msg_queue=send_msg_queue, bot_ctrl_queue=None, cloud_mode=cloud_mode)
    while True:
        try:
            botproc.start()
            uiproc.start()
            botproc.join()
            uiproc.join()
        except Exception:
            botproc.kill()
            uiproc.kill()
