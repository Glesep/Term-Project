import socketserver
from threading import Thread
import random
import time

users = {}  # key: nickname / value: 해당 닉네임에 대한 정보 (튜플)

topic = {"동물": ["사자", "호랑이", "팽귄", "하마", "얼룩말", "개", "고양이", "기린", "참치", "개구리", "앵무새", "독수리"],
       "과일": ["사과", "배", "수박", "토마토", "딸기", "포도", "오랜지", "복숭아", "참외", "멜론", "키위"],
       "직업": ["의사", "교사", "엔지니어", "요리사", "예술가", "간호사", "경찰관", "소방관", "변호사", "회계사"],
       "교통수단": ["버스", "지하철", "택시", "기차", "비행기", "배", "자전거", "오토바이", "트럭"]
       }

start_game = "상대방의 직업을 찾아라!\n 주어진 주제 내에서 상대방의 단어를 맞춰 보세요.\n 이하 게임 설명"

isStarted = False
current_turn = ""
# HandlerClass 제작
class MyHander(socketserver.BaseRequestHandler):
    
    def handle(self):
        global isStarted, current_turn
        
        print(self.client_address)

        while True:
            nickname = self.request.recv(1024).decode()
            
            if nickname in users:
                self.request.send("이미 등록된 닉네임입니다.\n".encode())
                
            if len(users) == 2:
                self.request.send("인원이 꽉 찼습니다.\n".encode())
                
            else:
                # 서버에 접속하는 모든 클라이언트에 대한 정보 저장
                users[nickname] = (self.request, self.client_address)
                print(f"현재 {len(users)} 명 참여중..")
                # 클라이언트에게 정해진 닉네임 알려줌
                self.request.send(f"{nickname}".encode())
                
                # 모든 클라이언트에게 전송
                for sock, _ in users.values():
                    sock.send(f"{nickname} 님이 입장 했습니다.".encode())
                
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
                    current_turn = list(users.keys())[0]
                    
                    # 단어 분배
                    for i, ((sock, _), word) in enumerate(zip(users.values(), random_words)):
                        sock.send(f"/t {word}".encode()) 
                        time.sleep(0.5)
                        
                        if i == 0:
                            sock.send("당신의 차례입니다! 자신의 단어를 표현해주세요!".encode())
                        else:
                            sock.send("상대방의 차례입니다.".encode())
                    
                    
                break
            
            
        while True:
            
            msg = self.request.recv(1024)
            if msg.decode() == "/bye":
                print("exit client")
                self.request.close()
                break  
            
            if isStarted:
                # 게임 중일 때는 턴 체크
                if nickname == current_turn:
                    # 메시지 전송 후 턴 변경
                    for sock, _ in users.values():
                        sock.send(f"[{nickname}] {msg.decode()}".encode())
                    
                    # 다음 턴으로 변경
                    players = list(users.keys())
                    current_turn = players[1] if current_turn == players[0] else players[0]
                    
                    # 턴 변경 알림
                    for nick, (sock, _) in users.items():
                        if nick == current_turn:
                            sock.send("당신의 차례입니다! 자신의 단어를 표현해주세요!".encode())
                        else:
                            sock.send("상대방의 차례입니다.".encode())
                else:
                    # 자신의 턴이 아닐 때는 메시지를 보낸 클라이언트에게만 알림
                    self.request.send("지금은 당신의 차례가 아닙니다.".encode())
                 
            else:        
                # 게임 시작 전에는 자유롭게 채팅 가능
                for sock, _ in users.values():
                    sock.send(f"[{nickname}] {msg.decode()}".encode())
       
                
                
        if nickname in users:
            del users[nickname]
            for sock, _ in users.values():
                sock.send(f"{nickname}님이 퇴장 했습니다.".encode())
            print(f"현재 {len(users)}명 참여중")

# chatServer를 멀티 쓰레드 환경으로 구성            
class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def sendMessage():
    while True:
        # 서버 귓속말 형식: /w nickname chat
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
            for sock, _ in users.values():
                sock.send(f"{server_message}".encode())
    


# TCPServer클래스는 server_address와 HandlerClass를 매개변수로 필요로 함
server = ChatServer(("", 8274), MyHander)

# 서버가 메세지를 보내기 위한 쓰레드 설정
message_th = Thread(target = sendMessage, daemon=True)
message_th.start()

server.serve_forever()
server.shutdown()
server.server_close()