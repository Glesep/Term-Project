import socketserver

class MyHandler(socketserver.BaseRequestHandler):
    users = {}

    def handle(self):
        print(self.client_address)
        while True:
            self.request.send("채팅 닉네임을 입력하세요: ".encode())
            nickname = self.request.recv(1024).decode()
            if nickname in self.users:
                self.request.send("이미 등록된 닉네임 입니다.\n".encode())
            else:
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
            for sock, _ in self.users.values():
                sock.send(f"[{nickname}] {msg.decode()}".encode())

        if nickname in self.users:
            del self.users[nickname]
            for sock, _ in self.users.values():
                sock.send(f"{nickname} 님이 퇴장 했습니다.".encode())
            print("현재 {} 명 참여중".format(len(self.users)))

class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

server = ChatServer(("", 8274), MyHandler)
server.serve_forever()
server.shutdown()
server.server_close()