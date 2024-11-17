from socket import *

def send(sock):
    sendData = input('>>>')
    sock.send(sendData.encode('utf-8'))
    
def receive(sock):
    recvData = sock.recv(1024)
    print('상대방 :', recvData.decode('utf-8'))
    

port = 8080

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', port))
serverSocket.listen(1)

print(f'{port}번 포트로 접속 대기중')

connectSocket, addr = serverSocket.accept()

print(f'{addr}에서 접속되었습니다.')

while True:
    send(connectSocket)
    
    receive(connectSocket)
    