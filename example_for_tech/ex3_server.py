import socketserver
from threading import Thread
import random
import time

users = {}  # key: nickname_own / value: 해당 닉네임에 대한 정보 (sock, addr, word)(튜플)

topic = {"동물": ["사자", "호랑이", "팽귄", "하마", "얼룩말", "개", "고양이", "기린", "참치", "개구리", "앵무새", "독수리"],
       "과일": ["사과", "배", "수박", "토마토", "딸기", "포도", "오랜지", "복숭아", "참외", "멜론", "키위"],
       "직업": ["의사", "교사", "엔지니어", "요리사", "예술가", "간호사", "경찰관", "소방관", "변호사", "회계사"],
       "교통수단": ["버스", "지하철", "택시", "기차", "비행기", "배", "자전거", "오토바이", "트럭"]}

start_game = "상대방의 직업을 찾아라!\n 주어진 주제 내에서 상대방의 단어를 맞춰 보세요.\n 이하 게임 설명"
isStarted = False
question_turn = dict()
answer_turn = dict()
change_flag = False
random_words = list()

def setStatus(userList, statusChange):
    global question_turn, answer_turn
    if not statusChange:
        question_turn = {userList[0]: True, userList[1]: False}
        answer_turn = {userList[0]: False, userList[1]: True}
    else:
        question_turn = {userList[0]: False, userList[1]: True}
        answer_turn = {userList[0]: True, userList[1]: False}

class MyHander(socketserver.BaseRequestHandler):
    def handle(self):
        global isStarted, change_flag, random_words
        print(self.client_address)

        while True:
            nickname_own = self.request.recv(1024).decode()
            if nickname_own in users:
                self.request.send("이미 등록된 닉네임입니다.\n".encode())
            if len(users) == 2:
                self.request.send("인원이 꽉 찼습니다.\n".encode())
            else:
                users[nickname_own] = (self.request, self.client_address)
                print(f"현재 {len(users)} 명 참여중..")
                self.request.send(f"{nickname_own}".encode())
                
                for sock, _ in users.values():
                    sock.send(f"{nickname_own} 님이 입장 했습니다.".encode())
                
                if len(users) == 2:
                    for sock, _ in users.values():
                        sock.send(f"곧 게임이 시작됩니다...".encode())
                        time.sleep(1)
                        sock.send(f"{start_game}".encode())
                    
                    random_topic = random.choice(list(topic.keys()))
                    random_words = random.sample(topic[random_topic], 2)
                    isStarted = True
                    setStatus(list(users.keys()), change_flag)
                    
                    for i, ((each_nickname_own, (sock, addr)), word) in enumerate(zip(users.items(), random_words)):
                        users[each_nickname_own] = (sock, addr, word)
                        sock.send(f"/t {word}".encode())
                        time.sleep(0.3)
                        if i == 0:
                            sock.send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                        else:
                            sock.send("상대방의 질문이나 정답을 기다려주세요.".encode())
                break

        while True:
            msg = self.request.recv(1024)
            if msg.decode() == "/bye":
                print("exit client")
                self.request.close()
                break
           

            if isStarted:
                msg_content = msg.decode()
                players = list(users.keys())
                other_player = players[1] if nickname_own == players[0] else players[0]
                
                 
                # 시간 초과
                if msg_content == "/timeout":
                    change_flag = not change_flag
                    setStatus(list(users.keys()), change_flag)
                    players = list(users.keys())
                    other_player = players[1] if nickname_own == players[0] else players[0]

                    for sock, _, _ in users.values():
                        sock.send("시간 초과로 턴이 변경됩니다.".encode())

                    users[other_player][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                    users[nickname_own][0].send("상대방의 질문이나 정답을 기다려주세요.".encode())
                    continue
                

                if question_turn[nickname_own]:
                    if msg_content.startswith("/a"):
                        answer = msg_content[len("/a"):].strip()
                        for sock, _, _ in users.values():
                            sock.send(f"{nickname_own}의 정답 선언: {answer}".encode())
                            
                        if answer == users[other_player][2]:
                            for sock, _, _ in users.values():
                                sock.send(f"{nickname_own}님이 승리하셨습니다!!".encode())
                                sock.send(f"게임이 종료됩니다...".encode())
                            isStarted = False
                            # 타이머 정지
                        else:
                            for sock, _, _ in users.values():
                                sock.send(f"오답입니다...".encode())
                            
                            change_flag = not change_flag
                            setStatus(list(users.keys()), change_flag)
                            
                            users[other_player][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                            users[nickname_own][0].send("상대방의 질문이나 정답을 기다려주세요.".encode())
                    
                    elif msg_content.endswith("?"):
                        for sock, _, _ in users.values():
                            sock.send(f"[{nickname_own}의 질문] {msg_content}".encode())
                        
                        question_turn[nickname_own] = False
                        
                        users[other_player][0].send("질문에 답변해주세요 (예/아니오로 답변해주세요)".encode())
                        users[nickname_own][0].send("상대방의 답변을 기다려주세요.".encode())
                    else:
                        self.request.send("질문은 반드시 '?'로 끝나야 합니다. 예시: '당신은 육식동물인가요?'".encode())
                
                elif answer_turn[nickname_own]:
                    if question_turn[other_player]:
                        self.request.send("상대방의 질문이 끝날 때까지 기다려주세요".encode())
                    else:
                        if msg_content.lower() in ["예", "아니오", "yes", "no"]:
                            for sock, _, _ in users.values():
                                sock.send(f"[{nickname_own}의 답변] {msg_content}".encode())
                            
                            change_flag = not change_flag
                            setStatus(list(users.keys()), change_flag)
                            
                            users[nickname_own][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                            users[other_player][0].send("상대방의 질문이나 정답을 기다려주세요.".encode())
                        else:
                            self.request.send("'예' 또는 '아니오'로만 답변해주세요.".encode())
                            
                else:
                    if question_turn[other_player]:
                        self.request.send("상대방의 답변이 끝날 때까지 기다려주세요".encode())
            else:
                for sock, _, _ in users.values():
                    sock.send(f"[{nickname_own}] {msg.decode()}".encode())
                
        if nickname_own in users:
            del users[nickname_own]
            for sock, _, _ in users.values():
                sock.send(f"{nickname_own}님이 퇴장 했습니다.".encode())
            print(f"현재 {len(users)}명 참여중")

class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def sendMessage():
    while True:
        server_message = input()
        if server_message.startswith("/w "):
            message_split = server_message.split()
            nickname_toWhisper = message_split[1]
            chat_slice = message_split[2:]
            chat = " ".join(chat_slice)
            users[nickname_toWhisper][0].send(f"{chat}".encode())
        else:
            for sock, _, _ in users.values():
                sock.send(f"{server_message}".encode())

server = ChatServer(("", 8274), MyHander)
message_th = Thread(target=sendMessage, daemon=True)
message_th.start()

server.serve_forever()
server.shutdown()
server.server_close()