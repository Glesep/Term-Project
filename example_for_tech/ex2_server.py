import socketserver

# HandlerClass 제작
class MyHander(socketserver.BaseRequestHandler):
    users = {}  # value는 튜플
    
    def handle(self):
        print(self.client_address)

        while True:
            self.request.send("채팅 닉네임을 입력하세요 ".encode())
            nickname = self.request.recv(1024).decode()
            
            if nickname in self.users:
                self.request.send("이미 등록된 닉네임입니다.\n".encode())
            else:
                # 서버에 접속하는 모든 클라이언트에 대한 정보 저장
                self.users[nickname] = (self.request, self.client_address)
                print(f"현재 {len(self.users)} 명 참여중..")
                
                for sock, _ in self.users.values():
                    sock.send(f"{nickname} 님이 입장 했습니다.".encode())
                break
        
        while True:
            msg = self.request.recv(1024)
            if msg.decode() == "/bye":
                print("exit client")
                self.request.close()
                break
            # 전체 유저에게 채팅 보내주기
            for sock, _ in self.users.values():
                sock.send(f"[{nickname}] {msg.decode()}".encode())
                
        if nickname in self.users:
            del self.users[nickname]
            for sock, _ in self.users.values():
                sock.send(f"{nickname}님이 퇴장 했습니다.".encode())
            print(f"현재 {len(self.users)}명 참여중")
            
    

class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# TCPServer클래스는 server_address와 HandlerClass를 매개변수로 필요로 함

server = ChatServer(("", 8274), MyHander)

server.serve_forever()
server.shutdown()
server.server_close()