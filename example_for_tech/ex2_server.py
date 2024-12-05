import socketserver
from threading import Thread

users = {}  # value는 튜플

# HandlerClass 제작
class MyHander(socketserver.BaseRequestHandler):
    
    def handle(self):
        print(self.client_address)

        while True:
            # self.request.send("채팅 닉네임을 입력하세요 ".encode())
            nickname = self.request.recv(1024).decode()
            
            if nickname in users:
                self.request.send("이미 등록된 닉네임입니다.\n".encode())
            else:
                # 서버에 접속하는 모든 클라이언트에 대한 정보 저장
                users[nickname] = (self.request, self.client_address)
                print(f"현재 {len(users)} 명 참여중..")
                # 클라이언트에게 정해진 닉네임 알려줌
                self.request.send(f"{nickname}".encode())
                
                for sock, _ in users.values():
                    sock.send(f"{nickname} 님이 입장 했습니다.".encode())
                break
        
        while True:
            msg = self.request.recv(1024)
            if msg.decode() == "/bye":
                print("exit client")
                self.request.close()
                break          
            # 전체 유저에게 채팅 보내주기
            for sock, _ in users.values():
                sock.send(f"[{nickname}] {msg.decode()}".encode())
                
        if nickname in users:
            del users[nickname]
            for sock, _ in users.values():
                sock.send(f"{nickname}님이 퇴장 했습니다.".encode())
            print(f"현재 {len(users)}명 참여중")
            
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