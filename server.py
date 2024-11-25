# server.py
import socketserver
import signal
import logging
import time
import random
import threading

class GameHandler(socketserver.BaseRequestHandler):
    """게임 핸들러 클래스
    클라이언트의 연결과 게임 진행을 관리하는 메인 클래스
    socketserver.BaseRequestHandler를 상속받아 구현
    """
    
    # 클래스 변수들 - 모든 인스턴스가 공유하는 게임 상태 정보
    users = {}  # {닉네임: (소켓, 주소)} 형태로 연결된 유저 정보 저장
    game_started = False  # 게임 시작 여부
    current_topic = ""  # 현재 게임의 주제
    answer_words = {}  # {닉네임: 할당된 단어} 형태로 각 유저의 단어 저장
    current_turn = None  # 현재 턴을 가진 유저의 닉네임
    waiting_for_restart = False  # 게임 재시작 대기 상태
    restart_votes = {}  # {닉네임: 투표} 형태로 재시작 투표 현황 저장
    
    # 게임에서 사용할 주제와 단어들
    topics = {
        "동물": ["사자", "호랑이", "코끼리", "기린", "팬더", "원숭이", "캥거루", "코알라"],
        "음식": ["피자", "햄버거", "스파게티", "초밥", "김치", "라면", "떡볶이", "비빔밥"],
        "나라": ["한국", "일본", "중국", "미국", "프랑스", "영국", "독일", "이탈리아"],
        "과일": ["사과", "바나나", "오렌지", "포도", "딸기", "키위", "망고", "파인애플"],
        "직업": ["의사", "교사", "요리사", "경찰", "소방관", "변호사", "프로그래머", "디자이너"]
    }
    
    def broadcast(self, message, exclude=None):
        """모든 클라이언트에게 메시지를 전송하는 함수
        
        Args:
            message (str): 전송할 메시지
            exclude (socket, optional): 제외할 클라이언트 소켓
            
        클라이언트의 recv_message 메소드에서 이 메시지를 받아 처리함
        """
        logging.info(f"Broadcasting: {message}")
        for nickname, (sock, _) in self.users.items():
            if exclude and sock == exclude:
                continue
            try:
                sock.send(message.encode())
            except Exception as e:
                logging.error(f"Broadcasting error to {nickname}: {e}")

    def initialize_game(self):
        """게임 초기화 및 설정
        
        게임 상태를 초기화하고 각 플레이어에게 단어를 할당
        클라이언트의 game_started 상태와 연동됨
        
        Returns:
            bool: 초기화 성공 여부
        """
        self.game_started = True
        self.waiting_for_restart = False
        self.restart_votes.clear()
        self.current_topic = random.choice(list(self.topics.keys()))
        self.answer_words.clear()
        
        available_words = self.topics[self.current_topic].copy()
        for nickname in self.users.keys():
            word = random.choice(available_words)
            available_words.remove(word)
            self.answer_words[nickname] = word
            logging.info(f"Assigned word '{word}' to player {nickname}")
        
        return True

    def start_game(self):
        """게임 시작 처리
        
        게임 시작 메시지를 전송하고 게임을 초기화
        클라이언트의 recv_message에서 이 메시지들을 받아 UI를 업데이트
        
        Returns:
            bool: 게임 시작 성공 여부
        """
        if len(self.users) != 2:
            return False
            
        self.broadcast("\n게임이 곧 시작됩니다!")
        time.sleep(1)
        
        self.broadcast("\n상대방의 단어를 맞춰라!")
        time.sleep(0.5)
        
        game_instructions = """
=== 게임 방법 ===
1. 자유롭게 서로 질문하고 답변하며 상대방의 단어를 추측하세요.
2. 상대방의 단어를 맞추려면 '[정답] 단어' 형식으로 입력하세요.
3. 서로 대화를 나누며 상대방의 단어를 알아내세요.
"""
        self.broadcast(game_instructions)
        time.sleep(0.5)
        
        if self.initialize_game():
            self.broadcast(f"\n=== 게임 시작 ===\n주제: {self.current_topic}")
            time.sleep(0.1)
            
            for nickname, (sock, _) in self.users.items():
                personal_info = f"\n당신의 단어: {self.answer_words[nickname]}"
                try:
                    sock.send(personal_info.encode())
                except Exception as e:
                    logging.error(f"Error sending game info to {nickname}: {e}")
            
            return True
        return False

    def handle_nickname_setup(self):
        """클라이언트의 닉네임 설정을 처리
        
        클라이언트의 handle_nickname_setup 메소드와 상호작용
        닉네임 중복 체크 및 승인 처리
        
        Returns:
            str: 설정된 닉네임
        """
        while True:
            try:
                self.request.send("NICKNAME_REQ".encode())
                nickname = self.request.recv(1024).decode().strip()
                
                if not nickname:
                    continue
                    
                if nickname in self.users:
                    self.request.send("NICKNAME_DUP".encode())
                    continue
                    
                self.request.send(f"NICKNAME_ACK:{nickname}".encode())
                return nickname
                
            except Exception as e:
                logging.error(f"Error in nickname setup: {e}")
                raise

    def handle(self):
        """클라이언트 연결 처리 메인 함수
        
        클라이언트의 연결부터 게임 진행, 종료까지 모든 과정을 관리
        클라이언트의 모든 메시지를 처리하고 적절한 응답을 전송
        """
        try:
            # 게임방 인원 체크
            if len(self.users) >= 2:
                self.request.send("FULL".encode())
                return
                
            # 닉네임 설정
            nickname = self.handle_nickname_setup()
            self.users[nickname] = (self.request, self.client_address)
            logging.info(f"Player {nickname} connected. Current players: {len(self.users)}")
            
            # 입장 메시지 전송
            welcome_msg = f"{nickname}님이 입장했습니다."
            self.broadcast(welcome_msg)
            
            # 2명이 모이면 게임 시작
            if len(self.users) == 2:
                time.sleep(0.1)
                self.start_game()

            # 메시지 처리 루프
            while True:
                try:
                    msg = self.request.recv(1024).decode().strip()
                    if not msg:
                        continue
                        
                    if msg == "/bye":
                        break
                    
                    # 재시작 투표 처리
                    if self.waiting_for_restart:
                        if msg.lower().strip() == 'y':
                            self.restart_votes[nickname] = 'y'
                            self.broadcast(f"{nickname}님이 재시작에 동의했습니다.")
                            if len(self.restart_votes) == len(self.users) and all(vote == 'y' for vote in self.restart_votes.values()):
                                time.sleep(0.5)
                                self.start_game()
                                self.restart_votes.clear()
                        else:
                            self.broadcast(f"[{nickname}] {msg}")
                        continue
                    
                    # 정답 체크
                    if msg.startswith("[정답]"):
                        answer = msg[4:].strip()
                        opponent = [user for user in self.users.keys() if user != nickname][0]
                        if answer == self.answer_words[opponent]:
                            win_msg = f"\n{nickname}님이 승리했습니다! 정답: {answer}"
                            self.broadcast(win_msg)
                            self.game_started = False
                            self.waiting_for_restart = True
                            time.sleep(0.1)
                            self.broadcast("\n게임 재시작을 원하시면 y를 입력하세요.")
                        else:
                            self.request.send("틀렸습니다. 계속 진행하세요.\n".encode())
                    else:
                        self.broadcast(f"[{nickname}] {msg}")
                    
                except Exception as e:
                    logging.error(f"Error handling message from {nickname}: {e}")
                    break

        except Exception as e:
            logging.error(f"Connection error: {e}")
        finally:
            if 'nickname' in locals() and nickname in self.users:
                del self.users[nickname]
                self.broadcast(f"{nickname}님이 퇴장했습니다.")
                logging.info(f"Player {nickname} disconnected. Current players: {len(self.users)}")

class GameServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """멀티스레드 게임 서버 클래스
    
    여러 클라이언트의 동시 접속을 처리하기 위한 스레드 기반 서버
    """
    allow_reuse_address = True
    daemon_threads = True
    _is_running = False

    def start(self):
        """서버 시작"""
        self._is_running = True
        self.serve_forever()
    
    def stop(self):
        """서버 종료"""
        self._is_running = False
        self.shutdown()
        self.server_close()

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def signal_handler(signum, frame):
    """시그널 처리 함수
    서버 종료 시그널(Ctrl+C 등) 처리
    """
    logging.info("Received signal to shutdown server...")
    if server._is_running:
        server.stop()

if __name__ == "__main__":
    setup_logging()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        server = GameServer(("", 8274), GameHandler)
        logging.info("게임 서버가 시작되었습니다...")
        server.start()
    except KeyboardInterrupt:
        logging.info("서버를 종료합니다...")
    except Exception as e:
        logging.error(f"서버 에러: {e}")
    finally:
        if hasattr(server, '_is_running') and server._is_running:
            server.stop()