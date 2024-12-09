import socketserver
from threading import Thread
import random
import time

users = {}  # key: nickname_own / value: 해당 닉네임에 대한 정보 (sock, addr, word)(튜플)

topic = {"동물": ["사자", "호랑이", "팽귄", "하마", "얼룩말", "개", "고양이", "기린", "참치", "개구리", "앵무새", "독수리"],
       "과일": ["사과", "배", "수박", "토마토", "딸기", "포도", "오랜지", "복숭아", "참외", "멜론", "키위"],
       "직업": ["의사", "교사", "엔지니어", "요리사", "예술가", "간호사", "경찰관", "소방관", "변호사", "회계사"],
       "교통수단": ["버스", "지하철", "택시", "기차", "비행기", "배", "자전거", "오토바이", "트럭"]
       }

start_game = "상대방의 직업을 찾아라!\n 주어진 주제 내에서 상대방의 단어를 맞춰 보세요.\n 이하 게임 설명"

isStarted = False
question_turn = dict()
answer_turn = dict()
change_flag = False
random_words = list()

def setStatus(userList, statusChange):
    global question_turn, answer_turn
    
    if not statusChange: 
        question_turn = {
            userList[0]: True,
            userList[1]: False
        }
        
        answer_turn = {
            userList[0]: False,
            userList[1]: True
        }
        
    else:
        question_turn = {
            userList[0]: False,
            userList[1]: True
        }
        
        answer_turn = {
            userList[0]: True,
            userList[1]: False
        }
        
# HandlerClass 제작
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
                # 서버에 접속하는 모든 클라이언트에 대한 정보 저장
                users[nickname_own] = (self.request, self.client_address)
                print(f"현재 {len(users)} 명 참여중..")
                # 클라이언트에게 정해진 닉네임 알려줌
                self.request.send(f"{nickname_own}".encode())
                
                # 모든 클라이언트에게 전송
                for sock, _ in users.values():
                    sock.send(f"{nickname_own} 님이 입장 했습니다.".encode())
                
                # 2명의 인원이 모였을 때 게임 시작
                if len(users) == 2:
                    for sock, _ in users.values():
                        sock.send(f"곧 게임이 시작됩니다...".encode())
                        time.sleep(1)
                        # 게임 설명
                        sock.send(f"{start_game}".encode())
                        
                    
                    random_topic = random.choice(list(topic.keys()))
                    random_words = random.sample(topic[random_topic], 2)
                    
                    # 게임 시작을 알리는 flag
                    isStarted = True
                    
                    setStatus(list(users.keys()), change_flag)
                    
                    # user 정보에 word 추가 후 클라이언트에게 본인의 단어를 전달
                    for i, ((each_nickname_own, (sock, addr)), word) in enumerate(zip(users.items(), random_words)):
                        users[each_nickname_own] = (sock, addr, word)
                        sock.send(f"/t {word}".encode())
                        time.sleep(0.3)

                        if i == 0:
                            sock.send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                        else:
                            sock.send("상대방의 질문이나 정답을 기다려주세요.".encode())
                    
                break
            
        """
        질문자
        
        답변자
        
        """ 
        while True:
            
            # 메세지 받기까지 대기
            msg = self.request.recv(1024)
            if msg.decode() == "/bye":
                print("exit client")
                self.request.close()
                break  
            
            # 정답 입력: /a 정답
            if isStarted:
                msg_content = msg.decode()
                players = list(users.keys())
                # 파이썬에선 함수 내부이면 반복문 내에서 선언된 변수가 반복문 밖에서 사용될 수 있음 (nickname_own)
                other_player = players[1] if nickname_own == players[0] else players[0]
                
                # 질문자의 턴일 때
                if question_turn[nickname_own]:
                    #정답 판정
                    if msg_content.startswith("/a"):
                        answer = msg_content[len("/a"):].strip()
                        for sock, _, _ in users.values():
                            sock.send(f"{nickname_own}의 정답 선언: {answer}".encode())
                            
                        if answer == users[other_player][2]:
                            for sock, _, _ in users.values():
                                sock.send(f"{nickname_own}님이 승리하셨습니다!!".encode())
                                sock.send(f"게임이 종료됩니다...".encode())
                                isStarted = False
                                
                                
                        else:
                            for sock, _, _ in users.values():
                                sock.send(f"오답입니다...".encode())
                                
                            # 턴 변경
                            change_flag = not change_flag
                            setStatus(list(users.keys()), change_flag)
                            
                            users[other_player][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                            users[nickname_own][0].send("상대방의 질문이나 정답을 기다려주세요.".encode())
                    
                    
                    
                    # 질문자의 턴일 때
                    elif msg_content.endswith("?"):
                        for sock, _, _ in users.values():
                            sock.send(f"[{nickname_own}의 질문] {msg_content}".encode())
                        
                        # 턴 변경 (자신의 질문권 없애기)
                        question_turn[nickname_own] = False
                        
                        # 턴 변경 알림
                        users[other_player][0].send("질문에 답변해주세요 (예/아니오로 답변해주세요)".encode())
                        users[nickname_own][0].send("상대방의 답변을 기다려주세요.".encode())
                    else:
                        # 질문이 아닌 경우 알림
                        self.request.send("질문은 반드시 '?'로 끝나야 합니다. 예시: '당신은 육식동물인가요?'".encode())
                
                
                
                
                elif answer_turn[nickname_own]:  # 답변자의 턴
                    # 답변자는 현재 질문자가 질문하는 중이면 메시지를 보낼 수 없음
                    if question_turn[other_player]:
                        self.request.send("상대방의 질문이 끝날 때까지 기다려주세요".encode())
                    
                    
                    else:
                        # 답변 처리 (예/아니오 답변만 허용)
                        if msg_content.lower() in ["예", "아니오", "yes", "no"]:
                            for sock, _, _ in users.values():
                                sock.send(f"[{nickname_own}의 답변] {msg_content}".encode())
                            
                            # 턴 변경
                            change_flag = not change_flag
                            setStatus(list(users.keys()), change_flag)
                            
                            # 턴 변경 알림
                            users[nickname_own][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                            users[other_player][0].send("상대방의 질문이나 정답을 기다려주세요.".encode())
                        else:
                            self.request.send("'예' 또는 '아니오'로만 답변해주세요.".encode())
                     
                     
                     
                            
                # 질문자도 답변자도 아닐 때 (질문하고 난 이후)            
                else:
                    if question_turn[other_player]:
                        self.request.send("상대방의 답변이 끝날 때까지 기다려주세요".encode())
               
               
                 
            else:        
                # 게임 시작 전에는 자유롭게 채팅 가능
                for sock, _, _ in users.values():
                    sock.send(f"[{nickname_own}] {msg.decode()}".encode())
       
                
                
        if nickname_own in users:
            del users[nickname_own]
            for sock, _, _ in users.values():
                sock.send(f"{nickname_own}님이 퇴장 했습니다.".encode())
            print(f"현재 {len(users)}명 참여중")

# chatServer를 멀티 쓰레드 환경으로 구성            
class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def sendMessage():
    while True:
        # 서버 귓속말 형식: /w nickname_own chat
        server_message = input()
        # 귓속말일 경우
        if server_message.startswith("/w "):
            message_split = server_message.split()
            nickname_toWhisper = message_split[1]
            chat_slice = message_split[2:]
            chat = " ".join(chat_slice)
            
            users[nickname_toWhisper][0].send(f"{chat}".encode())
        # 전체 보내기일 경우
        else:  
            for sock, _, _ in users.values():
                sock.send(f"{server_message}".encode())
    


# TCPServer클래스는 server_address와 HandlerClass를 매개변수로 필요로 함
server = ChatServer(("", 8274), MyHander)

# 서버가 메세지를 보내기 위한 쓰레드 설정
message_th = Thread(target = sendMessage, daemon=True)
message_th.start()

server.serve_forever()
server.shutdown()
server.server_close()