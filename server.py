# server.py
import socketserver
import signal
import logging
import time
import random
import threading

class GameHandler(socketserver.BaseRequestHandler):
    users = {}
    game_started = False
    current_topic = ""
    answer_words = {}
    current_turn = None
    waiting_for_restart = False
    restart_votes = {}
    
    topics = {
        "동물": ["사자", "호랑이", "코끼리", "기린", "팬더", "원숭이", "캥거루", "코알라"],
        "음식": ["피자", "햄버거", "스파게티", "초밥", "김치", "라면", "떡볶이", "비빔밥"],
        "나라": ["한국", "일본", "중국", "미국", "프랑스", "영국", "독일", "이탈리아"],
        "과일": ["사과", "바나나", "오렌지", "포도", "딸기", "키위", "망고", "파인애플"],
        "직업": ["의사", "교사", "요리사", "경찰", "소방관", "변호사", "프로그래머", "디자이너"]
    }
    
    def broadcast(self, message, exclude=None):
        logging.info(f"Broadcasting: {message}")
        for nickname, (sock, _) in self.users.items():
            if exclude and sock == exclude:
                continue
            try:
                sock.send(message.encode())
            except Exception as e:
                logging.error(f"Broadcasting error to {nickname}: {e}")

    def initialize_game(self):
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

    def check_restart_votes(self):
        if len(self.restart_votes) == len(self.users):
            if all(vote == 'y' for vote in self.restart_votes.values()):
                self.start_game()
            else:
                self.restart_votes.clear()

    def handle_nickname_setup(self):
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
        try:
            if len(self.users) >= 2:
                self.request.send("FULL".encode())
                return
                
            nickname = self.handle_nickname_setup()
            self.users[nickname] = (self.request, self.client_address)
            logging.info(f"Player {nickname} connected. Current players: {len(self.users)}")
            
            welcome_msg = f"{nickname}님이 입장했습니다."
            self.broadcast(welcome_msg)
            
            if len(self.users) == 2:
                time.sleep(0.1)
                self.start_game()

            while True:
                try:
                    msg = self.request.recv(1024).decode().strip()
                    if not msg:
                        continue
                        
                    if msg == "/bye":
                        break
                    
                    if msg.startswith("[정답]"):
                        answer = msg[4:].strip()
                        opponent = [user for user in self.users.keys() if user != nickname][0]
                        if answer == self.answer_words[opponent]:
                            win_msg = f"\n{nickname}님이 승리했습니다! 정답: {answer}"
                            self.broadcast(win_msg)
                            self.game_started = False
                            time.sleep(0.1)
                            self.broadcast("\n게임 재시작을 원하시면 y를 입력하세요.")
                            continue
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
    allow_reuse_address = True
    daemon_threads = True
    _is_running = False

    def start(self):
        self._is_running = True
        self.serve_forever()
    
    def stop(self):
        self._is_running = False
        self.shutdown()
        self.server_close()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def signal_handler(signum, frame):
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