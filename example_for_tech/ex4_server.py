import socketserver
from threading import Thread
import random
import time

users = {}
topic = {
    "동물": ["사자", "호랑이", "팽귄", "하마", "얼룩말", "개", "고양이", "기린", "참치", "개구리", "앵무새", "독수리"],
    "과일": ["사과", "배", "수박", "토마토", "딸기", "포도", "오랜지", "복숭아", "참외", "멜론", "키위"],
    "직업": ["의사", "교사", "엔지니어", "요리사", "예술가", "간호사", "경찰관", "소방관", "변호사", "회계사"],
    "교통수단": ["버스", "지하철", "택시", "기차", "비행기", "배", "자전거", "오토바이", "트럭"]
}

game_rule = "상대방의 직업을 찾아라!\n 주어진 주제 내에서 상대방의 단어를 맞춰 보세요.\n 이하 게임 설명"

isStarted = False
question_turn = dict()
answer_turn = dict()
change_flag = False
user_words = dict()
start_vote = dict()

def reset_game_state():
    global isStarted, question_turn, answer_turn, change_flag, user_words
    isStarted = False
    question_turn.clear()
    answer_turn.clear()
    change_flag = False
    user_words.clear()

def setStatus(userList, statusChange):
    global question_turn, answer_turn
    try:
        if not statusChange:
            question_turn = {userList[0]: True, userList[1]: False}
            answer_turn = {userList[0]: False, userList[1]: True}
        else:
            question_turn = {userList[0]: False, userList[1]: True}
            answer_turn = {userList[0]: True, userList[1]: False}
            
    except Exception as e:
        print(f"턴 설정 중 오류 발생: {e}")

def deleteUserData(username):
    try:
        if username in start_vote:
            del start_vote[username]
        if username in user_words:
            del user_words[username]
        if username in users:
            del users[username]
            
    except Exception as e:
        print(f"사용자 데이터 삭제 중 오류 발생: {e}")

def clear_vote_result():
    global start_vote
    try:
        start_vote = {key: False for key in start_vote}
        
    except Exception as e:
        print(f"투표 초기화 중 오류 발생: {e}")

def clear_user_words():
    global user_words
    try:
        user_words = {key: "" for key in user_words}
        
    except Exception as e:
        print(f"사용자 단어 초기화 중 오류 발생: {e}")

def start_game():
    global isStarted, user_words
    try:
        clear_vote_result()
        for sock, _ in users.values():
            sock.send(f"곧 게임이 시작됩니다...".encode())
            time.sleep(1)
            sock.send(f"{game_rule}".encode())
            

        random_topic = random.choice(list(topic.keys()))
        random_words = random.sample(topic[random_topic], 2)
        
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
            
    except Exception as e:
        print(f"게임 시작 중 오류 발생: {e}")

class MyHander(socketserver.BaseRequestHandler):
    def handle(self):
        global isStarted, change_flag
        print(self.client_address)
        
        try:
            while True:
                try:
                    nickname_own = self.request.recv(1024).decode()
                    if not nickname_own:
                        print("클라이언트 연결 종료")
                        break

                    if nickname_own in users:
                        self.request.send("이미 등록된 닉네임입니다.\n".encode())
                        continue

                    if len(users) == 2:
                        self.request.send("인원이 꽉 찼습니다.\n".encode())
                        continue

                    users[nickname_own] = (self.request, self.client_address)
                    print(f"현재 {len(users)} 명 참여중..")
                    
                    self.request.send(f"{nickname_own}".encode())
                    start_vote[nickname_own] = False

                    for sock, _ in users.values():
                        sock.send(f"{nickname_own} 님이 입장 했습니다.".encode())
                    self.request.send("시작을 원하시면 \"/start\" 를 입력하세요.".encode())
                    break

                except ConnectionError:
                    print(f"클라이언트 {self.client_address} 연결 종료")
                    break
                
                except Exception as e:
                    print(f"닉네임 처리 중 오류 발생: {e}")
                    break

            while True:
                try:
                    msg = self.request.recv(1024)
                    if not msg:
                        break
                        
                    msg_content = msg.decode()

                    if msg_content == "/bye":
                        print("exit client")
                        break

                    if isStarted:
                        players = list(users.keys())
                        other_player = players[1] if nickname_own == players[0] else players[0]
                        
                        try:
                            # 시간 초과
                            if msg_content == "/timeout":
                                self.handle_timeout(nickname_own, other_player)

                            if question_turn[nickname_own]:
                                self.handle_question_turn(msg_content, nickname_own, other_player)

                            elif answer_turn[nickname_own]:
                                self.handle_answer_turn(msg_content, nickname_own, other_player)
                                
                            elif question_turn[other_player]:
                                self.request.send("상대방의 답변이 끝날 때까지 기다려주세요".encode())
                                
                        except Exception as e:
                            print(f"게임 로직 처리 중 오류 발생: {e}") 
                    else:
                        # 일반 채팅 처리
                        try:
                            if msg_content == "/start":
                                self.handle_start_vote(nickname_own)
                            elif msg_content == "/bye":
                                print("exit client")
                                self.request.close()
                            else:
                                for sock, _ in users.values():
                                    sock.send(f"[{nickname_own}] {msg_content}".encode())
                        except Exception as e:
                            print(f"채팅 처리 중 오류 발생: {e}")      
                                          
                
                except ConnectionError:
                    print(f"클라이언트 {nickname_own} 연결 종료")
                    break
                except Exception as e:
                    print(f"메시지 처리 중 오류 발생: {e}")
                    continue
        finally:
            try:
                players = list(users.keys())
                other_player = players[1] if nickname_own == players[0] else players[0]
                
                if 'nickname_own' in locals() and nickname_own in users:
                    
                        
                    deleteUserData(nickname_own)
                    for sock, _ in users.values():
                        try:
                            sock.send(f"{nickname_own}님이 퇴장 했습니다.".encode())
                        except:
                            continue
                        
                    if isStarted:
                        reset_game_state()
                        users[other_player][0].send(f"플레이어 {nickname_own}님이 퇴장하여 게임이 종료되었습니다.".encode())
                        
                    print(f"현재 {len(users)}명 참여중")
                    
            except Exception as e:
                print(f"정리 작업 중 오류 발생: {e}")

                
                

            
            
    def handle_timeout(self, nickname_own, other_player):
        global change_flag
        change_flag = not change_flag
        setStatus(list(users.keys()), change_flag)
        players = list(users.keys())
        other_player = players[1] if nickname_own == players[0] else players[0]

        for sock, _ in users.values():
            sock.send("시간 초과로 턴이 변경됩니다.".encode())

        users[other_player][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.".encode())
        users[nickname_own][0].send("상대방의 질문이나 정답을 기다려주세요.".encode())
    
    def handle_question_turn(self, msg_content, nickname_own, other_player):
        global isStarted, change_flag
            
        if msg_content.startswith("/a"):
            answer = msg_content[len("/a"):].strip()
            for sock, _ in users.values():
                sock.send(f"{nickname_own}의 정답 선언: {answer}".encode())
                
            if answer == user_words[other_player]:
                for sock, _ in users.values():
                    sock.send(f"{nickname_own}님이 승리하셨습니다!!".encode())
                    sock.send(f"게임이 종료됩니다...".encode())
                    sock.send(f"모든 인원이 '/start'를 입력 시, 게임이 재시작됩니다.".encode())
                    
                clear_vote_result()
                clear_user_words()
                change_flag = False
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
                        
     
    def handle_answer_turn(self, msg_content, nickname_own, other_player):
        global change_flag, isStarted
        
        
        
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
                            
                        
    def handle_start_vote(self, nickname_own):
        global start_vote
        start_vote[nickname_own] = True
        count_vote = sum(1 for agree in start_vote.values() if agree)
        
        for sock, _ in users.values():
                sock.send(f"{nickname_own}님이 시작 투표를 하였습니다!.\n({count_vote}/2)".encode())
        if count_vote == 2:
            start_game()          
                        
                        
                        
                        
class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def sendMessage():
    while True:
        try:
            server_message = input()
            if server_message.startswith("/w "):
                message_split = server_message.split()
                nickname_toWhisper = message_split[1]
                chat_slice = message_split[2:]
                chat = " ".join(chat_slice)
                users[nickname_toWhisper][0].send(f"{chat}".encode())
            else:
                for sock, _ in users.values():
                    try:
                        sock.send(f"{server_message}".encode())
                    except:
                        continue
        except Exception as e:
            print(f"서버 메시지 전송 중 오류 발생: {e}")

try:
    server = ChatServer(("", 8274), MyHander)
    message_th = Thread(target=sendMessage, daemon=True)
    message_th.start()
    server.serve_forever()
except Exception as e:
    print(f"서버 실행 중 오류 발생: {e}")
finally:
    server.shutdown()
    server.server_close()