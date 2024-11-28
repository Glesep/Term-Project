import socketserver

# HandlerClass 제작
class MyHander(socketserver.BaseRequestHandler):
    def handle(self):
        print(self.client_address)

        # 클라이언트에게 수신한 데이터를 다시 클라이언트로 전송해주는 방식
        while True:
            msg = self.request.recv(1024)   # 현재 접속된 클라이언트의 소켓은 self.request로 접근할 수 있음
            if msg.decode() == "/bye":
                print("exit client")
                self.request.close()
                break
            self.requset.send(msg)          # 현재 클라이언트에게 데이터를 전송 가능

class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# TCPServer클래스는 server_address와 HandlerClass를 매개변수로 필요로 함

server = ChatServer(("", 8274), MyHander)

server.serve_forever()
server.shutdown()
server.server_close()