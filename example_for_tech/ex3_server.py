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

isStarted = False       # 시작 여부 flag
question_turn = dict()  # 질문 턴을 구분하기 위한 변수
answer_turn = dict()    # 대답 턴을 구분하기 위한 변수
change_flag = False     # setStatus의 상태를 결정하는 변수
user_words = dict()     # topic 딕셔너리의 한 주제에 대한 2개의 랜덤한 변수가 들어감
start_vote = dict()     # user의 시작 투표를 위한 변수
# nickname_color = ""      # 클라이언트의 닉네임 표기 색상

def setStatus(userList, statusChange):
    """
    게임 시작 시, 유저들의 턴을 제어하는 함수

    Args:
        userList (list): user의 nickname이 담긴 리스트
        statusChange (bool): change_flag
    """
    global question_turn, answer_turn
    if not statusChange:
        question_turn = {userList[0]: True, userList[1]: False}
        answer_turn = {userList[0]: False, userList[1]: True}
    else:
        question_turn = {userList[0]: False, userList[1]: True}
        answer_turn = {userList[0]: True, userList[1]: False}

def clear_vote_result():
    """
    게임 시작 투표 상태를 초기화하는 함수
    """
    global start_vote
    
    start_vote = {key: False for key in start_vote}

def clear_user_words():
    global user_words
    user_words = {key: "" for key in user_words}
    
def start_game():
    """
    게임 시작 함수
    """
    global isStarted, user_words
    clear_vote_result(list(users.keys()))
    
    for sock, _ in users.values():
        sock.send(f"곧 게임이 시작됩니다...".encode())
        time.sleep(1)
        sock.send(f"{start_game}".encode())

        random_topic = random.choice(list(topic.keys()))
        random_words = random.sample(topic[random_topic], 2)
        
        # for user_nickname, word in zip(users.items(), random_words):
        #     user_words[user_nickname] = word
            
        
        isStarted = True
        
        setStatus(list(users.keys()), change_flag)

        for i, ((each_nickname_own, (sock, _)), word) in enumerate(zip(users.items(), random_words)):
            user_words[each_nickname_own] = word
            sock.send(f"/t {word}".encode())
            time.sleep(0.1)
            if i == 0:
                sock.send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
            else:
                sock.send("상대방의 질문이나 정답을 기다려주세요.".encode())

def deleteUserData(username):
    if username in start_vote:
        del start_vote[username]
    if username in user_words:
        del user_words[username]
    del users[username]
   

class MyHander(socketserver.BaseRequestHandler):
    """
    socketserver.TCPServer를 실행할 때 매개변수로 들어가야 할 HandlerClass\n
    ==================================================================\n
    socketserver 라이브러리의 BaseRequestHandler 클래스를 상속한 후,\n 
    handle 함수를 추가하여 서버 측 소켓 작동 시 추가적으로 handle 함수가 실행
    """
    def handle(self):
        """
        사용자 handle 함수 \n
        인원 제어, 게임 진행 제어를 수행
        """
        global isStarted, change_flag
        print(self.client_address)

        
        while True:
            # user가 정한 닉네임을 수신받음
            nickname_own = self.request.recv(1024).decode()
            
            # 닉네임 중복 확인
            if nickname_own in users:
                self.request.send("이미 등록된 닉네임입니다.\n".encode())
            # 인원 수 제한
            if len(users) == 2:
                self.request.send("인원이 꽉 찼습니다.\n".encode())
            
            else:
                # users 딕셔너리에 user 정보 저장
                users[nickname_own] = (self.request, self.client_address)
                print(f"현재 {len(users)} 명 참여중..")
                # 본인의 닉네임 정보 클라이언트 측에 알려줌
                self.request.send(f"{nickname_own}".encode())
                start_vote[nickname_own] = False
                
                # 입장 알림
                for sock, _ in users.values():
                    sock.send(f"{nickname_own} 님이 입장 했습니다.".encode())
                    time.sleep(0.1)
                self.request.send("시작을 원하시면 '/start' 를 입력하세요.".encode())
                
                # # 게임 진행을 할 수 있는 인원 수가 되었을 때
                # if len(users) == 2:
                #     # vote
                #     clear_vote_result(list(users.keys()))
                #     for sock, _ in users.values():
                #         sock.send(f"인원이 충족되었습니다.\n 게임 시작을 원하시면 /start를 입력해주세요.".encode())
                        
                        
                    
                    
                    
                break
            
        while True:
            msg = self.request.recv(1024)
            msg_content = msg.decode()
            
            if isStarted:
                players = list(users.keys())
                other_player = players[1] if nickname_own == players[0] else players[0]
                
                 
                # 시간 초과
                if msg_content == "/timeout":
                    change_flag = not change_flag
                    setStatus(list(users.keys()), change_flag)
                    players = list(users.keys())
                    other_player = players[1] if nickname_own == players[0] else players[0]

                    for sock, _ in users.values():
                        sock.send("시간 초과로 턴이 변경됩니다.".encode())

                    users[other_player][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                    users[nickname_own][0].send("상대방의 질문이나 정답을 기다려주세요.".encode())
                    continue
                
                
                
                
                
                if question_turn[nickname_own]:
                    if msg_content.startswith("/a"):
                        answer = msg_content[len("/a"):].strip()
                        for sock, _ in users.values():
                            sock.send(f"{nickname_own}의 정답 선언: {answer}".encode())
                            
                        if answer == users[other_player][2]:
                            for sock, _ in users.values():
                                sock.send(f"{nickname_own}님이 승리하셨습니다!!".encode())
                                sock.send(f"게임이 종료됩니다...".encode())
                                sock.send(f"모든 인원이 '/start'를 입력 시, 게임이 재시작됩니다.")
                                
                            clear_vote_result()
                            clear_user_words()
                            isStarted = False
                            

                        else:
                            for sock, _ in users.values():
                                sock.send(f"오답입니다...".encode())
                            
                            change_flag = not change_flag
                            setStatus(list(users.keys()), change_flag)
                            
                            users[other_player][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
                            users[nickname_own][0].send("상대방의 질문이나 정답을 기다려주세요.".encode())
                    
                    elif msg_content.endswith("?"):
                        for sock, _ in users.values():
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
                            for sock, _ in users.values():
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
                
                        
            # start_vote의 value값이 True인 개수를 셈
            elif msg_content == "/start":
                start_vote[nickname_own] = True
                count_vote = sum(1 for agree in start_vote.values() if agree)
                
                for sock, _ in users.values():
                        sock.send(f"{nickname_own}님이 시작 투표를 하였습니다!.\n({count_vote}/2)".encode())
                if count_vote == 2:
                    start_game()       

            elif msg_content == "/bye":
                print("exit client")
                self.request.close()
                break
            
            # 일반 대화
            else:  
                for sock, _ in users.values():
                    sock.send(f"[{nickname_own}] {msg.decode()}".encode())
                
        if nickname_own in users.keys():
            deleteUserData(nickname_own)

            for sock, _ in users.values():
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
            for sock, _ in users.values():
                sock.send(f"{server_message}".encode())

server = ChatServer(("", 8274), MyHander)
message_th = Thread(target=sendMessage, daemon=True)
message_th.start()

server.serve_forever()
server.shutdown()
server.server_close()