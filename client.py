# client.py
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import threading
import socket
import sys

class GameClient:
    """게임 클라이언트 클래스
    
    서버와의 연결, UI 구성, 게임 진행을 관리하는 메인 클래스
    서버의 GameHandler 클래스와 상호작용하여 게임을 진행
    """
    
    def __init__(self):
        """클라이언트 초기화
        
        게임 상태 변수들을 초기화하고 연결 설정 창을 생성
        """
        self.setup_connection_window()
        self.current_turn = False  # 현재 턴 여부
        self.game_started = False  # 게임 시작 여부
        self.nickname = ""  # 사용자 닉네임
        
    def setup_connection_window(self):
        """서버 연결 설정 창 생성
        
        서버 주소를 입력받는 초기 창을 생성
        connect 메소드와 연결되어 서버 연결을 처리
        """
        self.win_connect = tk.Tk()
        self.win_connect.protocol("WM_DELETE_WINDOW", self.window_input_close)
        self.win_connect.title("게임 접속")
        
        tk.Label(self.win_connect, text="서버주소:").grid(row=0, column=0)
        self.input_addr_string = tk.StringVar(value="127.0.0.1:8274")
        self.input_addr = tk.Entry(self.win_connect, textvariable=self.input_addr_string, width=20)
        self.input_addr.grid(row=0, column=1, padx=5, pady=5)
        
        connect_button = tk.Button(self.win_connect, text="접속", command=self.connect)
        connect_button.grid(row=0, column=2, padx=5, pady=5)
        
        width = 280
        height = 40
        self.center_window(self.win_connect, width, height)
        
        self.input_addr.focus()
        self.win_connect.mainloop()
    
    def setup_chat_window(self):
        """게임 메인 창 설정
        
        채팅창, 입력창, 버튼 등 게임에 필요한 UI 구성요소 생성
        서버로부터 받은 메시지를 표시하고 사용자 입력을 처리
        """
        self.window = tk.Tk()
        self.window.title("단어 맞추기 게임")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 메인 프레임 구성
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 상단 정보 프레임
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 닉네임 표시
        self.nickname_label = tk.Label(info_frame, text=f"닉네임: {self.nickname}", 
                                     font=("Arial", 10, "bold"), fg="darkblue")
        self.nickname_label.pack(side=tk.LEFT)
        
        # 상태 표시 레이블
        self.status_label = tk.Label(info_frame, text="대기중...", 
                                   fg="blue", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT)
        
        # 구분선
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # 채팅창 프레임
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        # 채팅창과 스크롤바
        self.chat_list = tk.Text(chat_frame, wrap=tk.WORD, height=15, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_list.yview)
        self.chat_list.configure(yscrollcommand=scrollbar.set)
        
        self.chat_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 입력 프레임
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        # 메시지 입력창
        self.input_msg = tk.StringVar()
        self.inputbox = ttk.Entry(input_frame, textvariable=self.input_msg)
        self.inputbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.inputbox.bind("<Return>", self.send_message)
        
        # 버튼 프레임
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT)
        
        # 전송 버튼
        self.send_button = ttk.Button(button_frame, text="전송", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=2)
        
        # 정답 입력 버튼
        self.answer_button = ttk.Button(button_frame, text="정답 입력", command=self.send_answer)
        self.answer_button.pack(side=tk.LEFT, padx=2)
        
        # 창 크기 설정
        width = 400
        height = 500
        self.center_window(self.window, width, height)
        self.window.minsize(400, 300)
    
    def center_window(self, window, width, height):
        """창을 화면 중앙에 위치시키는 함수
        
        Args:
            window: 중앙에 위치시킬 창
            width: 창의 너비
            height: 창의 높이
        """
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def handle_nickname_setup(self):
        """닉네임 설정 처리
        
        서버의 handle_nickname_setup 메소드와 통신하여
        닉네임 설정 및 중복 체크를 수행
        
        Returns:
            bool: 닉네임 설정 성공 여부
        """
        while True:
            msg = self.sock.recv(1024).decode()
            
            if msg == "FULL":
                messagebox.showerror("오류", "게임방이 가득 찼습니다.")
                return False
                
            if msg == "NICKNAME_REQ":
                nickname = simpledialog.askstring("닉네임", "사용할 닉네임을 입력하세요:")
                if not nickname:
                    self.sock.close()
                    return False
                self.sock.send(nickname.encode())
                continue
                
            if msg == "NICKNAME_DUP":
                messagebox.showerror("오류", "이미 사용 중인 닉네임입니다.")
                continue
                
            if msg.startswith("NICKNAME_ACK:"):
                self.nickname = msg.split(":")[1]
                return True
                
            break
        return False
    
    def connect(self, event=None):
        """서버 연결 처리
        
        서버에 연결하고 닉네임 설정 후 게임 창을 생성
        메시지 수신 스레드를 시작
        """
        try:
            addr = self.input_addr_string.get().split(":")
            self.IP = addr[0]
            self.PORT = int(addr[1])
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.IP, self.PORT))
            
            self.win_connect.withdraw()
            
            if not self.handle_nickname_setup():
                self.win_connect.destroy()
                return
            
            self.win_connect.destroy()
            self.setup_chat_window()
            
            receive_thread = threading.Thread(target=self.recv_message)
            receive_thread.daemon = True
            receive_thread.start()
            
            self.window.mainloop()
                
        except Exception as e:
            messagebox.showerror("연결 오류", f"서버 연결 실패: {str(e)}")
            self.win_connect.destroy()
    
    def update_status(self, message):
        """상태 메시지 업데이트
        
        Args:
            message: 표시할 상태 메시지
        """
        self.status_label.config(text=message)
    
    def append_message(self, message):
        """채팅창에 메시지 추가
        
        Args:
            message: 추가할 메시지
        """
        self.chat_list.insert(tk.END, message + '\n')
        self.chat_list.see(tk.END)
        self.chat_list.update()
    
    def toggle_input(self, state):
        """입력 위젯들의 활성화/비활성화
        
        Args:
            state: True면 활성화, False면 비활성화
        """
        state = 'normal' if state else 'disabled'
        self.inputbox.config(state=state)
        self.send_button.config(state=state)
        self.answer_button.config(state=state)
    
    def send_message(self, event=None):
        """메시지 전송
        
        입력된 메시지를 서버로 전송
        """
        message = self.input_msg.get().strip()
        if message:
            try:
                self.sock.send(message.encode())
                self.input_msg.set("")
            except:
                messagebox.showerror("전송 오류", "메시지 전송에 실패했습니다.")
    
    def send_answer(self):
        """정답 전송
        
        정답을 입력받아 서버로 전송
        """
        answer = simpledialog.askstring("정답 입력", "상대방의 단어를 맞춰보세요:")
        if answer:
            try:
                self.sock.send(f"[정답] {answer}".encode())
            except:
                messagebox.showerror("전송 오류", "정답 전송에 실패했습니다.")
    
    def recv_message(self):
        """메시지 수신 처리
        
        서버로부터 메시지를 받아 처리하는 스레드 함수
        게임 상태, 턴, 채팅 메시지 등을 처리
        """
        while True:
            try:
                msg = self.sock.recv(1024).decode()
                if not msg:
                    continue
                
                # 게임 상태 메시지 처리
                if "게임 재시작을 원하시면" in msg:
                    self.game_started = False
                    self.update_status("재시작 대기중...")
                    self.toggle_input(True)
                elif "=== 게임 시작 ===" in msg:
                    self.game_started = True
                    self.toggle_input(True)
                
                # 게임 정보 표시
                if "당신의 단어:" in msg:
                    word_info = msg.split("\n")[1]
                    self.update_status(word_info)
                
                self.append_message(msg)
                
            except Exception as e:
                messagebox.showerror("연결 오류", "서버와의 연결이 끊어졌습니다.")
                self.window.destroy()
                break
    
    def on_closing(self):
        """창 종료 처리
        
        게임 종료 시 서버와의 연결을 종료하고 프로그램 종료
        """
        if messagebox.askokcancel("종료", "게임을 종료하시겠습니까?"):
            try:
                self.sock.send("/bye".encode())
                self.sock.close()
            except:
                pass
            self.window.destroy()
            sys.exit()
    
    def window_input_close(self, event=None):
        """연결 창 종료 처리"""
        self.win_connect.destroy()
        sys.exit()

if __name__ == "__main__":
    client = GameClient()