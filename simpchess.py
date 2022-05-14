
background = '''┏┯┯┳┳┳┯┯┓
┠┼┼╊╋╉┼┼┨
┠╋┼╄╇╃┼╋┨
┣┼╋┼╋┼╋┼┫
┠┴┴┴┴┴┴┴┨
┠┬┬┬┬┬┬┬┨
┣┼╋┼╋┼╋┼┫
┠╋┼╆╈╅┼╋┨
┠┼┼╊╋╉┼┼┨
┗┷┷┻┻┻┷┷┛'''  # 棋盘，横着是x轴，纵的是y轴

cmiAllMap = [[1]*9]*10

cmiPalace = [[0]*3+[1]*3+[0]*3]*3+[[0]*9]*4+[[0]*3+[1]*3+[0]*3]*3

pieceList = []

initGroupMap = [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0]]

groupMap = initGroupMap

def print_out(strout):
    print(strout)
    if not callback == None:
        callback.sendchat(strout)


def generateRookMove():
    result = []
    for x in range(-8, 9):
        if x != 0:
            result.append([x, 0])
    for y in range(-9, 10):
        if y != 0:
            result.append([0, y])
    return result


def generateKingMove():
    result = []
    for x in range(-1, 2):
        for y in range(-1, 2):
            if x != 0 or y != 0:
                result.append([x, y])
    return result


class piece:
    # 阵营，横坐标，纵坐标，移动目的地，移动范围（比如不能过河）。马腿象眼炮架，预计通过重构父类方法实现。
    def __init__(self, group, x, y, canMoveTo, canMoveIn, chara):
        self.group = group
        self.x = x
        self.spawnX = x
        self.y = y
        self.spawnY = y
        self.canMoveTo = canMoveTo
        self.canMoveIn = canMoveIn
        self.existence = True
        self.chara = chara
        self.is_king = False
        pieceList.append(self)
        global groupMap

    def needCheck(self):
        return True

    def canMove(self, destX, destY):
        result = False  # 是否移动成功
        try:  # 防止canMoveIn里没有目的地，也就是走到棋盘外面
            self.destX = destX
            self.destY = destY
            self.deltaX = destX-self.x
            self.deltaY = destY-self.y
            if (
                self.existence == True and
                self.canMoveIn[destY][destX] == 1 and
                not groupMap[destY][destX] == self.group and
                [self.deltaX, self.deltaY] in self.canMoveTo
            ):
                if self.needCheck() == True:
                    self.move(destX, destY)
                    result = True
                else:
                    result = 'need error'
            else:
                result = 'move error'
        finally:
            return result

    def move(self, destX, destY):
        for destPiece in pieceList:
            if (
                destPiece.x == destX and
                destPiece.y == destY and
                not destPiece == self
            ):
                destPiece.x = -1
                destPiece.y = -1
                destPiece.existence = False
        groupMap[self.y][self.x] = 0
        self.x = destX
        self.y = destY


class Rook(piece):  # 车
    def __init__(self, group, x, y, chara):
        self.canMoveTo = generateRookMove()
        self.canMoveIn = cmiAllMap
        piece.__init__(self, group, x, y, self.canMoveTo,
                       self.canMoveIn, chara)

    def needCheck(self):
        # 阻挡（不能越子）
        result = True
        if self.deltaX == 0:
            for i in range(min(self.y, self.destY)+1, max(self.y, self.destY)):
                if not groupMap[i][self.x] == 0:
                    result = False
        else:
            for i in range(min(self.x, self.destX)+1, max(self.x, self.destX)):
                if not groupMap[self.y][i] == 0:
                    result = False
        return result


class PAO(piece):  # 炮
    def __init__(self, group, x, y, chara):
        self.canMoveTo = generateRookMove()
        self.canMoveIn = cmiAllMap
        piece.__init__(self, group, x, y, self.canMoveTo,
                       self.canMoveIn, chara)

    def needCheck(self):
        # 阻挡（不能越子）
        if groupMap[self.destY][self.destX] == 0:
            result = True
            if self.deltaX == 0:
                for i in range(min(self.y, self.destY)+1, max(self.y, self.destY)):
                    if not groupMap[i][self.x] == 0:
                        result = False
            else:
                for i in range(min(self.x, self.destX)+1, max(self.x, self.destX)):
                    if not groupMap[self.y][i] == 0:
                        result = False
            return result
        else:
            result = 0
            if self.deltaX == 0:
                for i in range(min(self.y, self.destY)+1, max(self.y, self.destY)):
                    if not groupMap[i][self.x] == 0:
                        result = result + 1
            else:
                for i in range(min(self.x, self.destX)+1, max(self.x, self.destX)):
                    if not groupMap[self.y][i] == 0:
                        result = result + 1
            if result == 1:
                return True
            else:
                return False


class Knight(piece):  # 马
    def __init__(self, group, x, y, chara):
        self.canMoveTo = [[-2, 1], [-2, -1], [-1, 2],
                          [-1, -2], [1, 2], [1, -2], [2, 1], [2, -1]]
        self.need = [[-1, 0], [-1, 0], [0, 1],
                     [0, -1], [0, 1], [0, -1], [1, 0], [1, 0]]
        self.canMoveIn = cmiAllMap
        piece.__init__(self, group, x, y, self.canMoveTo,
                       self.canMoveIn, chara)

    def needCheck(self):
        # 马腿
        result = False
        if [self.deltaX, self.deltaY] in self.canMoveTo:
            i = self.canMoveTo.index([self.deltaX, self.deltaY])
            if groupMap[self.y+self.need[i][1]][self.x+self.need[i][0]] == 0:
                result = True
        return result


class Bishop(piece):  # 相
    def __init__(self, group, x, y, chara):
        self.canMoveTo = [[-2, 2], [-2, -2], [2, 2], [2, -2]]
        self.need = [[-1, 1], [-1, -1], [1, 1], [1, -1]]
        # 不能过河
        if group == 1:
            self.canMoveIn = [[1]*9]*5+[[0]*9]*5
        else:
            self.canMoveIn = [[0]*9]*5+[[1]*9]*5
        piece.__init__(self, group, x, y, self.canMoveTo,
                       self.canMoveIn, chara)

    def needCheck(self):
        # 象眼
        result = False
        if [self.deltaX, self.deltaY] in self.canMoveTo:
            i = self.canMoveTo.index([self.deltaX, self.deltaY])
            if groupMap[self.y+self.need[i][1]][self.x+self.need[i][0]] == 0:
                result = True
        return result


class SHI(piece):  # 士
    def __init__(self, group, x, y, chara):
        self.canMoveTo = [[-1, 1], [-1, -1], [1, 1], [1, -1]]
        self.canMoveIn = cmiPalace
        piece.__init__(self, group, x, y, self.canMoveTo,
                       self.canMoveIn, chara)


class Pawns(piece):  # 卒
    def __init__(self, group, x, y, chara):
        if group == 1:
            self.canMoveTo = [[0, 1], [-1, 0], [1, 0]]
        else:
            self.canMoveTo = [[0, -1], [-1, 0], [1, 0]]
        self.canMoveIn = cmiAllMap
        piece.__init__(self, group, x, y, self.canMoveTo,
                       self.canMoveIn, chara)

    def needCheck(self):
        result = True
        if self.group == 1:
            if self.y < 5:
                if self.deltaY == 0:
                    result = False
        else:
            if self.y > 4:
                if self.deltaY == 0:
                    result = False
        return result


class King(piece):  # 将帅
    def __init__(self, group, x, y, chara):
        self.canMoveTo = generateKingMove()
        self.canMoveIn = cmiPalace
        piece.__init__(self, group, x, y, self.canMoveTo,
                       self.canMoveIn, chara)
        self.is_king = True

# 现版本以测试为主，只实现了少数棋子。


class Main():
    def __init__(self):
        global groupMap

    def scanMap(self):
        self.mapCharaList = []
        groupMap = initGroupMap
        for line in background.splitlines(True):
            for chara in list(line):
                self.mapCharaList.append(chara)
        for piece in pieceList:
            if piece.existence == 1:
                self.mapCharaList[10*piece.y+piece.x] = piece.chara
                groupMap[piece.y][piece.x] = piece.group
        self.mapstr = ''.join(self.mapCharaList)

    def showMap(self):
        self.showList = ['\\ 0-1-2-3-4-5-6-7-8[x][上方为1方，下方为-1方]\n']
        self.mapLineList = self.mapstr.splitlines(True)
        for a in range(len(self.mapLineList)):
            self.showList.append(str(a)+self.mapLineList[a])
            # 给字符串加上纵坐标标识
        self.showstr = ''.join(self.showList)
        print_out(self.showstr)
    
    def getMap(self):
        self.scanMap()
        self.showMap()

def play(x,y,x1,y1,group=None):
    result = False
    if group == None:
        group = 0
    for piece in pieceList:
        if piece.x==x and piece.y==y:
            print('piece found')
            if piece.existence==True and not piece.group == -group:
                cm = piece.canMove(x1,y1)
                if cm == True:
                    piece.move(x1,y1)
                    main.getMap()
                    result = True
                else:
                    print_out('canMove:{}'.format(cm))
            else:
                print_out('group error or dead piece error')
    return result

def consolePlay(strin=None,group=None):
    result = False
    if strin == None:
        strin = input('move:')
    listin = strin.split()
    if len(listin)==4:
        result = play(int(listin[0]),int(listin[1]),int(listin[2]),int(listin[3]),group=group)
    else:
        print_out('input error')
    return result


def generate_pieces():
    # 生成所有棋子
    pieceList.clear()
    global r01,r02,k01,k02,b01,b02,s01,s02,king01,pao01,pao02,p01,p02,p03,p04,p05,r11,r12,k11,k12,b11,b12,s11,s12,king11,pao11,pao12,p11,p12,p13,p14,p15

    r01 = Rook(group=1, x=0, y=0, chara='车')
    r02 = Rook(group=1, x=8, y=0, chara='车')
    k01 = Knight(group=1,x=1,y=0,chara='马')
    k02 = Knight(group=1,x=7,y=0,chara='马')
    b01 = Bishop(group=1,x=2,y=0,chara='相')
    b02 = Bishop(group=1,x=6,y=0,chara='相')
    s01 = SHI(group=1,x=3,y=0,chara='士')
    s02 = SHI(group=1,x=5,y=0,chara='士')
    king01 = King(group=1,x=4,y=0,chara='将')
    pao01 = PAO(group=1,x=1,y=2,chara='炮')
    pao02 = PAO(group=1,x=7,y=2,chara='炮')
    p01 = Pawns(group=1,x=0,y=3,chara='兵')
    p02 = Pawns(group=1,x=2,y=3,chara='兵')
    p03 = Pawns(group=1,x=4,y=3,chara='兵')
    p04 = Pawns(group=1,x=6,y=3,chara='兵')
    p05 = Pawns(group=1,x=8,y=3,chara='兵')

    r11 = Rook(group=-1, x=0, y=9, chara='車')
    r12 = Rook(group=-1, x=8, y=9, chara='車')
    k11 = Knight(group=-1,x=1,y=9,chara='馬')
    k12 = Knight(group=-1,x=7,y=9,chara='馬')
    b11 = Bishop(group=-1,x=2,y=9,chara='象')
    b12 = Bishop(group=-1,x=6,y=9,chara='象')
    s11 = SHI(group=-1,x=3,y=9,chara='仕')
    s12 = SHI(group=-1,x=5,y=9,chara='仕')
    king11 = King(group=-1,x=4,y=9,chara='帥')
    pao11 = PAO(group=-1,x=1,y=7,chara='砲')
    pao12 = PAO(group=-1,x=7,y=7,chara='砲')
    p11 = Pawns(group=-1,x=0,y=6,chara='卒')
    p12 = Pawns(group=-1,x=2,y=6,chara='卒')
    p13 = Pawns(group=-1,x=4,y=6,chara='卒')
    p14 = Pawns(group=-1,x=6,y=6,chara='卒')
    p15 = Pawns(group=-1,x=8,y=6,chara='卒')

def set_callback(bot):
    global callback
    callback = bot

main = Main()
callback = None