import socket
from threading import Thread

def recv_message(sock):
    while True:
        msg = sock.recv(1024)
        print(msg.decode())

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 8274))

# Thread - 서버의 메세지를 지속적으로 수신할 수 있게 코드 작성 (2개의 무한 루프 로직을 동시에 실행 불가능 - 쓰레드로 분리)
th = Thread(target = recv_message, args=(sock, ), daemon=True)
th.start()

while True:
    msg = input("입력: ")
    sock.send(msg.encode())
    if msg == "/bye":
        break
sock.close()