'''
참조한 소스 코드
https://blog.naver.com/nkj2001/222743970693

위 블로그의 채팅 기능 구현법을 참조하여 텀프로젝트의 채팅기능을 구현하였습니다.
추가로 구현한 사항은 주석으로 설명을 적어 놓았습니다.
'''


import socketserver
from threading import Thread
import random
import time

users = {}          # key: nickname_own / value: 해당 닉네임에 대한 정보 (sock, addr)(튜플)
topic = {           # 게임 시작 시, 유저들에게 분배될 단어들
    "동물": ["사자", "호랑이", "팽귄", "하마", "얼룩말", "개", "고양이", "기린", "참치", "개구리", "앵무새", "독수리"],
    "과일": ["사과", "배", "수박", "토마토", "딸기", "포도", "오랜지", "복숭아", "참외", "멜론", "키위"],
    "직업": ["의사", "교사", "엔지니어", "요리사", "예술가", "간호사", "경찰관", "소방관", "변호사", "회계사"],
    "교통수단": ["버스", "지하철", "택시", "기차", "비행기", "배", "자전거", "오토바이", "트럭"]
}


game_rule = ""          # 게임 룰 저장 변수
with open("./example_for_tech/gameRule.txt", "r") as file:
    game_rule = file.read()
    
isStarted = False       # 시작 여부 flag
change_flag = False     # setStatus의 상태를 결정하는 변수
question_turn = dict()  # 질문 턴을 구분하기 위한 변수
answer_turn = dict()    # 대답 턴을 구분하기 위한 변수
user_words = dict()     # topic 딕셔너리의 한 주제에 대한 2개의 랜덤한 변수가 들어감
start_vote = dict()     # user의 시작 투표를 위한 변수

def reset_game_state():
    """
    게임 상태를 초기화하는 함수
    """
    global isStarted, question_turn, answer_turn, change_flag, user_words
    
    isStarted = False
    change_flag = False
    question_turn.clear()
    answer_turn.clear()
    user_words.clear()

def setStatus(userList, statusChange):
    """
    게임 시작 시, 유저들의 턴을 제어하는 함수

    Args:
        userList (list): user의 nickname이 담긴 리스트
        statusChange (bool): change_flag
    """
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
    """
    유저가 퇴장 시 해당 유저의 정보를 삭제하는 함수
    
    Args:
        username (str): 퇴장한 user의 nickname
    """
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
    """
    게임 시작 투표 상태를 초기화하는 함수
    """
    global start_vote
    try:
        start_vote = {key: False for key in start_vote}
        
    except Exception as e:
        print(f"투표 초기화 중 오류 발생: {e}")

def clear_user_words():
    """
    사용자에게 전달된 단어를 삭제하는 함수
    """
    global user_words
    try:
        user_words = {key: "" for key in user_words}
        
    except Exception as e:
        print(f"사용자 단어 초기화 중 오류 발생: {e}")

def start_game():
    """
    게임을 시작하는 함수, 유저 전원이 /start를 입력하면 실행됨
    """
    global isStarted, user_words
    try:
        clear_vote_result()     # 시작 투표 결과를 초기화함으로써 게임 종료 후 재시작 투표를 원활하게 진행
        
        # 서버와 연결된 모든 클라이언트에게 전송
        for sock, _ in users.values():
            sock.send(f"곧 게임이 시작됩니다...".encode())
            time.sleep(1)
            sock.send(f"{game_rule}".encode())      # 게임 룰 설명
            

        # 한 주제에서 두 단어 선정
        random_topic = random.choice(list(topic.keys()))
        random_words = random.sample(topic[random_topic], 2)
        
        # 게임 실행 중을 알리는 flag
        isStarted = True
        
        # 게임 진행 상태를 설정
        setStatus(list(users.keys()), change_flag)

        # 선정된 단어를 전달하고 게임 시작
        for i, ((each_nickname_own, (sock, _)), word) in enumerate(zip(users.items(), random_words)):
            user_words[each_nickname_own] = word
            sock.send(f"/t {word}".encode())
            time.sleep(0.1)
            if i == 0:
                sock.send("당신의 차례입니다. 질문이나 정답을 입력해주세요.\n".encode())
            else:
                sock.send("상대방의 질문이나 정답을 기다려주세요.\n".encode())
            
    except Exception as e:
        print(f"게임 시작 중 오류 발생: {e}")

class MyHander(socketserver.BaseRequestHandler):
    """
    socketserver.TCPServer를 실행할 때 매개변수로 들어가야 할 HandlerClass\n
    =================================================================\n
    socketserver 라이브러리의 BaseRequestHandler 클래스를 상속한 후,\n 
    handle 함수를 추가하여 서버 측 소켓 작동 시 추가적으로 handle 함수가 실행
    """
    
    def handle(self):
        """
        사용자 handle 함수 (TCP 연결이 수행되면 자동으로 실행되는 함수)\n
        인원 제어, 게임 진행 제어를 수행\n
        """
        
        global isStarted, change_flag
       
        print(self.client_address)      # 어떤 호스트와 연결되었는지 확인 위함
        
        try:
            while True:
                try:
                    nickname_own = self.request.recv(1024).decode()         # TCP 연결이 완료된 이후, 클라이언트로부터 닉네임 입력을 받음
                    if not nickname_own:                                    # 닉네임 입력이 오지 않은 경우
                        print("클라이언트 연결 종료")
                        break

                    if nickname_own in users:                               # 중복된 닉네임인 경우
                        self.request.send("이미 등록된 닉네임입니다.\n".encode())
                        continue

                    if len(users) == 2:                                     # 인원이 꽉 찬 경우 (정원: 2명)
                        self.request.send("인원이 꽉 찼습니다.\n".encode())
                        continue

                    users[nickname_own] = (self.request, self.client_address)   # user 정보를 users 딕셔너리에 저장
                    print(f"현재 {len(users)} 명 참여중..")
                    
                    self.request.send(f"{nickname_own}".encode())               # 결정된 클라이언트의 닉네임 정보를 재전송
                    start_vote[nickname_own] = False                            # 시작 투표 인원 목록에 접속한 클라이언트 추가

                    for sock, _ in users.values():                              # 입장 후 안내
                        sock.send(f"{nickname_own} 님이 입장 했습니다.\n".encode())
                    self.request.send("시작을 원하시면 \"/start\" 를 입력하세요.\n".encode())
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
                    if not msg:                    # 메세지가 오지 않았을 경우 종료 진행
                        break
                        
                    msg_content = msg.decode()     # byte형식으로 온 메세지를 str로 변환

                    if msg_content == "/bye":      # 클라이언트가 접속 종료 시도를 하면, /bye 메세지를 전송하므로 이를 수신하였을 때 서버도 종료 진행
                        print("exit client")       
                        break

                    if isStarted:                   # 게임이 시작하였을 때
                        players = list(users.keys())                                                    # 현재 유저 닉네임 목록 저장
                        other_player = players[1] if nickname_own == players[0] else players[0]         # 상대방의 유저 닉네임 저장
                        
                        try:
                            # 시간 초과시
                            if msg_content == "/timeout":
                                self.handle_timeout(nickname_own, other_player)
                            # 본인의 질문 차례일 때
                            if question_turn[nickname_own]:
                                self.handle_question_turn(msg_content, nickname_own, other_player)
                            # 본인이 답변할 차례일 때
                            elif answer_turn[nickname_own]:
                                self.handle_answer_turn(msg_content, nickname_own, other_player)
                            # 본인이 질문 후, 상대방의 답변을 기다려야 할 때
                            elif question_turn[other_player]:
                                self.request.send("상대방의 답변이 끝날 때까지 기다려주세요\n".encode())
                                
                        except Exception as e:
                            print(f"게임 로직 처리 중 오류 발생: {e}") 
                    else:   # 게임이 시작하기 전, 일반적인 채팅 구현
                        try:
                            if msg_content == "/start":     # 게임 시작 투표를 하였을 때
                                self.handle_start_vote(nickname_own)
                            elif msg_content == "/bye":     # 클라이언트가 접속 종료 시도를 하면, /bye 메세지를 전송하므로 이를 수신하였을 때 서버도 종료 진행
                                print("exit client")
                                self.request.close()
                            else:                           # 일반적인 채팅을 쳤을 때
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
                players = list(users.keys())        # 유저 닉네임 목록을 저장
                if len(users) == 2:                 # 상대방이 존재할 때, 상대방의 닉네임 정보를 저장하는 변수 생성
                    other_player = players[1] if nickname_own == players[0] else players[0]
                
                if 'nickname_own' in locals() and nickname_own in users:    # 닉네임이 현재 users 딕셔너리에 존재하는지, nickname_own 변수에 있는지 재확인
                    
                    deleteUserData(nickname_own)                            # 서버 측에서 가지고 있는 유저 정보 삭제 처리
                    
                    for sock, _ in users.values():                          # 서버와 연결된 모든 클라이언트에게 전송
                        try:    
                            sock.send(f"{nickname_own}님이 퇴장 했습니다.".encode())
                        except:
                            continue
                        
                    if isStarted:                                           # 게임 중이었을 때 클라이언트가 접속을 종료하였다면
                        reset_game_state()                                  # 게임 중지, 게임관련 정보 초기화
                        users[other_player][0].send(f"플레이어 {nickname_own}님이 퇴장하여 게임이 종료되었습니다.\n".encode())
                        
                    print(f"현재 {len(users)}명 참여중")
                    
            except Exception as e:
                print(f"정리 작업 중 오류 발생: {e}")

    """
    게임 진행을 서버에서 처리하는 과정
        - user1, user2가 있다고 가정
        
    초기 상태:
        question_turn == {
            user1: True
            user2: False
        }
        
        answer_turn == {
            user1: False
            user2: True
        }
        
    user1이 질문 시:
        question_turn == {
            user1: False
            user2: False
        }
        
        answer_turn == {
            user1: False
            user2: True
        }
    
    user2가 질문에 대한 답변 시:
    
        question_turn == {
            user1: False
            user2: False
        }
        
        answer_turn == {
            user1: False
            user2: False
        }
        
    이후 setStatus가 호출하여 아래 상태를 만듦
    user1이 질문 차례일 때 정답 선언을 한 후, 그것이 오답이라고 판정되어도 아래 상태를 만듦
    
        question_turn == {
            user1: False
            user2: True
        }
        answer_turn == {
            user1: True
            user2: False
        }
    """
    
    def handle_timeout(self, nickname_own, other_player):
        """
        질문/정답 선언 시 시간 제한을 처리하는 함수
        Args:
            nickname_own (str): 본인의 닉네임
            other_player (str): 상대방의 닉네임
        """
        
        global change_flag
        
        change_flag = not change_flag   # 현재 질문 턴을 상대에게 넘기기 위해 change_flag를 변경
        setStatus(list(users.keys()), change_flag)
        
        # 본인과 상대방의 닉네임 저장
        players = list(users.keys())
        other_player = players[1] if nickname_own == players[0] else players[0]

        
        for sock, _ in users.values():      # 서버와 연결된 모든 클라이언트에게 전송
            sock.send("시간 초과로 턴이 변경됩니다.".encode())

        users[other_player][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.\n".encode())
    
    def handle_question_turn(self, msg_content, nickname_own, other_player):
        """
        질문하는 차례를 처리하는 함수
        Args:
            msg_content (str): 클라이언트측에서 전송한 메세지 내용
            nickname_own (str): 본인 닉네임
            other_player (str): 상대 닉네임
        """
        global isStarted, change_flag
            
        if msg_content.startswith("/a"):    # 정답 선언 시
            answer = msg_content[len("/a"):].strip()    # 정답 선언을 위한 /a를 제외한 나머지 내용을 추출
            
            for sock, _ in users.values():              # 서버와 연결된 모든 클라이언트에게 전송
                sock.send(f"[{nickname_own}님의 정답 선언] {answer}\n".encode())
                
            if answer == user_words[other_player]:      # 정답이라면
                for sock, _ in users.values():          # 서버와 연결된 모든 클라이언트에게 전송
                    sock.send(f"{nickname_own}님이 승리하셨습니다!!\n게임이 종료됩니다...\n모든 인원이 '/start'를 입력 시, 게임이 재시작됩니다.".encode())
                
                # 게임 상태를 초기화
                reset_game_state()
                
            else:                                       # 오답이라면
                for sock, _ in users.values():          # 서버와 연결된 모든 클라이언트에게 전송        
                    sock.send(f"오답입니다...".encode())
                
                change_flag = not change_flag           # 상대방에게 질문 기회가 넘어감
                setStatus(list(users.keys()), change_flag)
                
                users[other_player][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.\n".encode())
                users[nickname_own][0].send("상대방의 질문이나 정답을 기다려주세요.\n".encode())
            
        elif msg_content.endswith("?"):     # 질문 시
            for sock, _ in users.values():  # 서버와 연결된 모든 클라이언트에게 전송
                sock.send(f"[{nickname_own}의 질문] {msg_content}\n".encode())
            
            question_turn[nickname_own] = False     # 질문하였음을 기록
            
            users[other_player][0].send("질문에 답변해주세요 (예/아니오로 답변해주세요)\n".encode())
            users[nickname_own][0].send("상대방의 답변을 기다려주세요.\n".encode())
            
        else:       # 질문 형식이 아닐 시
            self.request.send("질문은 반드시 '?'로 끝나야 합니다. 예시: '당신은 육식동물인가요?'\n".encode())
                        
     
    def handle_answer_turn(self, msg_content, nickname_own, other_player):
        """
        대답하는 차례를 처리하는 함수
        Args:
            msg_content (str): 클라이언트측에서 전송한 메세지 내용
            nickname_own (str): 본인 닉네임
            other_player (str): 상대 닉네임
        """
        global change_flag, isStarted
        
        if question_turn[other_player]: # 상대방 질문 차례일 때
            self.request.send("상대방의 질문이나 정답을 기다려주세요.\n".encode())
        else:   # 상대방의 질문이 끝났을 떄 답변처리
            if msg_content.lower() in ["예", "아니오", "yes", "no"]:
                for sock, _ in users.values():
                    sock.send(f"[{nickname_own}의 답변] {msg_content}\n".encode())
                
                change_flag = not change_flag
                setStatus(list(users.keys()), change_flag)
                
                users[nickname_own][0].send("당신의 차례입니다. 질문이나 정답을 입력해주세요.\n".encode())
                users[other_player][0].send("상대방의 질문이나 정답을 기다려주세요.\n".encode())
            else:
                self.request.send("'예' 또는 '아니오'로만 답변해주세요.\n".encode())
                            
                        
    def handle_start_vote(self, nickname_own):
        """
        시작 투표 처리 함수

        Args:
            nickname_own (str): 본인 닉네임
        """
        
        global start_vote
        start_vote[nickname_own] = True
        count_vote = sum(1 for agree in start_vote.values() if agree)   # start_vote의 value 값들 중 True의 개수 확인
        
        for sock, _ in users.values():
                sock.send(f"{nickname_own}님이 시작 투표를 하였습니다!. ({count_vote}/2)".encode())
        if count_vote == 2:     # 모든 유저가 시작 투표를 하였을 경우, 게임 시작
            start_game()          
                        
                        
                        

# ChatServer 클래스는 socketserver 라이브러리의 TCPServer, ThreadingMixIn 클래스를 상속받음        
class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# def sendMessage():
#     """
#     서버가 클라이언트에게 직접 메세지를 전송할 수 있는 기능을 구현한 함수. 필요 시 사용
#     """
#     while True:
#         try:
#             server_message = input()
#             if server_message.startswith("/w "):
#                 message_split = server_message.split()
#                 nickname_toWhisper = message_split[1]
#                 chat_slice = message_split[2:]
#                 chat = " ".join(chat_slice)
#                 users[nickname_toWhisper][0].send(f"{chat}".encode())
#             else:
#                 for sock, _ in users.values():
#                     try:
#                         sock.send(f"{server_message}".encode())
#                     except:
#                         continue
#         except Exception as e:
#             print(f"서버 메시지 전송 중 오류 발생: {e}")

try:
    server = ChatServer(("", 8274), MyHander)
    # message_th = Thread(target=sendMessage, daemon=True)
    # message_th.start()
    server.serve_forever()
except Exception as e:
    print(f"서버 실행 중 오류 발생: {e}")
finally:
    server.shutdown()
    server.server_close()