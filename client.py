'''
참조한 소스 코드
https://blog.naver.com/nkj2001/222743970693

위 블로그의 채팅 기능 구현법을 참조하여 텀프로젝트의 채팅기능을 구현하였습니다.
추가로 구현한 사항은 주석으로 설명을 적어 놓았습니다.
'''


import tkinter
import threading
import socket
import sys
import time

IP = ""                 # 클라이언트가 입력한 서버 IP 주소
PORT = 0                # 클라이언트가 입력한 서버 PORT 번호
MyNickname = ""         # 본인 닉네임 저장 변수
MyWord = ""             # 본인 단어 저장 변수
timer_thread = None     # timer를 돌리기 위한 thread 변수 미리 선언
timer_running = False   # timer가 실행되고 있는지 확인하는 flag

def window_input_close(win_object):
    """
    클라이언트에게 뜨는 창의 우측 상단 X키를 눌렀을 때 실행되는 함수
    
    Args:
        win_object (tkinter의 window 객체): 어느 윈도우인지 매개변수로 전달
    """
    print("윈도우 종료")
    
    # 채팅창에서 나갈 때
    if 'window' in globals() and win_object == window:
        bye = tkinter.StringVar(value="/bye")
        send_message(bye)   # /bye라는 메세지를 서버로 전송

    # 닉네임 설정 창에서 나갈 때
    elif 'win_nickname' in globals() and win_object == win_nickname:
        # 서버와의 연결을 끊고 창을 닫음
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        win_object.destroy()
    
    # 연결 창에서 나갈 때
    else:
        # 연결 자체가 안되었기 때문에 창만 닫음
        win_object.destroy() 
        
    sys.exit(1) # 프로그램 실행 종료


def connect(event=None):
    """
    서버 접속 시도시 실행되는 함수
    """
    global IP, PORT, sock
    
    input_string = input_addr_string.get()  # StringVar 변수에서 str 변수로 변환
    # ":" 기준으로 IP와 PORT 추출
    addr = input_string.split(":")          
    IP = addr[0]
    PORT = int(addr[1])
    
    print(f"서버 접속시도 [{IP}:{PORT}]")
    
    # 서버 측과 접속 시도
    # 접속 성공 시, 현재 창 닫기 (다음 창으로 진행)
    # 접속 실패 시, 접속 실패 문구가 콘솔로 뜸
    connectionResult = sock.connect_ex((IP, PORT))
    if connectionResult == 0:
        print ("접속 성공")
        win_connect.destroy()
    else:
        print("접속 실패")
    


def set_nickname(msg):
    """
    닉네임 설정 시도 시 실행되는 함수
    Args:
        msg (StringVar): 입력받은 닉네임
    """
    global MyNickname, sock
    
    msg_str = msg.get()
    
    send_message(msg)
    MyNickname = sock.recv(1024).decode()
    
    if MyNickname == msg_str:
        print(f"나의 닉네임: {MyNickname}")
        win_nickname.destroy()
    else:
        print("중복된 닉네임입니다!")


def start_timer():
    """
    타이머를 실행시키는 함수
    """
    
    global timer_running
    timer_running = True
    remaining_time = 60     # 60초 설정
    
    # 1초마다 remaining_time에서 1을 빼어 표시
    while timer_running and remaining_time > 0:
        timer_label.config(text=f"남은 시간: {remaining_time}초")
        time.sleep(1)       
        remaining_time -= 1
    
    # 시간 초과 시, /timeout 메세지 서버측에 전송
    if timer_running:
        timer_label.config(text="시간 초과!")
        sock.send("/timeout".encode())

def reset_timer():
    """
    타이머를 리셋하는 함수
    """
    global timer_running
    timer_running = False
    timer_label.config(text="남은 시간: 60초")

def recv_message():
    """
    메세지를 수신하는 함수
    """
    global sock, timer_thread
    while True:
        try:
            if not sock:    # 연결이 되어있지 않다면, 종료
                break
        
            msg = sock.recv(1024)
            msg_decode = msg.decode()

            # 게임을 종료해야 할 때
            if "승리하셨습니다!!" in msg_decode or "퇴장" in msg_decode:
                reset_timer()
                timer_label.config(text="남은 시간: ")
                nickname_label.config(fg="black")
                word_label.config(text=f"나의 단어: ")

            # 질문/정답을 말하는 턴일 때
            if "당신의 차례입니다" in msg_decode:
                if timer_thread:
                    reset_timer()
                timer_thread = threading.Thread(target=start_timer)
                timer_thread.daemon = True
                timer_thread.start()

            # 질문을 한 이후
            elif "상대방의" in msg_decode:
                reset_timer()

            # /t: 설정된 단어를 서버측에 알려주기 위한 신호
            if msg_decode.startswith("/t"):
                word = msg_decode[len("/t"):].strip()
                word_label.config(text=f"나의 단어: {word}")

            # 나머지 일반적인 채팅 시
            else:   
                chat_list.insert(tkinter.END, msg_decode + "\n", "message")
                chat_list.see(tkinter.END)
        except:
            break
        
def send_message(msg):
    """
    메세지를 서버측으로 보내는 함수
    Args:
        msg (StringVar): 서버측에 보낸 메세지
    """
    global sock
    message = msg.get()
    
    if message == "/start": # /start 투표를 했을 경우 클라이언트가 인지할 수 있도록 이름 색을 바꿔 표시
        nickname_label.config(fg="blue")    
    
    sock.send(message.encode())
    msg.set("")             # 메세지 원본 삭제
    
    if message == "/bye":   # 클라이언트가 접속을 종료한다는 의미: /bye
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        window.destroy()


# ====================================== 여기까지 함수/변수 정의 ===========================================


win_connect = tkinter.Tk()
# X 버튼을 누를 때 window_input_close 실행
win_connect.protocol("WM_DELETE_WINDOW", lambda: window_input_close(win_connect))
win_connect.title("접속대상")

tkinter.Label(win_connect, text="접속대상").grid(row=0, column=0)

# tkinter의 문자열 데이터 전용 변수 StringVar, input_addr_string의 기본값으로 127.0.0.1:8274 설정
input_addr_string = tkinter.StringVar(value="127.0.0.1:8274")

# 입력 창을 만드는 tkinter.Entry
# textvariable=input_addr_string: 입력 창에 입력한 내용은 input_addr_string에 저장된다는 의미
input_addr = tkinter.Entry(win_connect, textvariable=input_addr_string, width=20)
input_addr.grid(row=0, column=1, padx=5, pady=5)
# enter 키 입력 시, connect() 함수 실행
input_addr.bind("<Return>", lambda event: connect())

# 접속하기 키 클릭 시, connect 함수 실행
connect_button = tkinter.Button(win_connect, text="접속하기", command=connect)
connect_button.grid(row=0, column=2, padx=5, pady=5)

# 창 크기, 나타나는 위치 조정
width = 280
height = 40
screen_width = win_connect.winfo_screenwidth()
screen_height = win_connect.winfo_screenheight()
x = int((screen_width / 2) - (width / 2))
y = int((screen_height / 2) - (height / 2))
win_connect.geometry('%dx%d+%d+%d' % (width, height, x, y))

# 창이 나타날 때 바로 입력 가능하게 하는 함수 focus()
input_addr.focus()

# 소켓 연결 준비를 위한 sock 객체 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 창 띄우기
win_connect.mainloop()


# 닉네임 입력 창
win_nickname = tkinter.Tk()
# X 버튼을 누를 때 window_input_close 실행
win_nickname.protocol("WM_DELETE_WINDOW", lambda: window_input_close(win_nickname))
win_nickname.title("닉네임 입력")

tkinter.Label(win_nickname, text="닉네임 입력").grid(row=0, column=0)
input_nickname_str = tkinter.StringVar()
input_nickname = tkinter.Entry(win_nickname, textvariable=input_nickname_str, width=20)
input_nickname.grid(row=0, column=1, padx=5, pady=5)
# enter 입력 시, set_nickname() 함수 실행
input_nickname.bind("<Return>", lambda event: set_nickname(input_nickname_str))

# 확인 키 클릭 시, set_nickname 함수 실행
input_nickname_button = tkinter.Button(win_nickname, text="확인", command=lambda:set_nickname(input_nickname_str))
input_nickname_button.grid(row=0, column=2, padx=5, pady=5)

win_nickname.geometry('%dx%d+%d+%d' % (width, height, x, y))
input_nickname.focus()

win_nickname.mainloop()


# 메인 채팅창
window = tkinter.Tk()
# X 버튼을 누를 때 window_input_close 실행
window.protocol("WM_DELETE_WINDOW", lambda: window_input_close(window))
window.title("채팅 클라이언트")

# 상단 정보를 담을 프레임
info_frame = tkinter.Frame(window)
info_frame.pack(fill=tkinter.X, padx=5, pady=5)
# 왼쪽에 닉네임 표시
nickname_label = tkinter.Label(info_frame, text=f"나의 닉네임: {MyNickname}", anchor="w")
nickname_label.pack(side=tkinter.LEFT)

# 오른쪽에 위치할 정보들을 담을 프레임 생성
right_info_frame = tkinter.Frame(info_frame)
right_info_frame.pack(side=tkinter.RIGHT)
# right_info_frame 내에 단어, 타이머 레이블을 담기

# 단어 레이블
word_label = tkinter.Label(right_info_frame, text=f"나의 단어: {MyWord}")
word_label.pack()
# 타이머 레이블
timer_label = tkinter.Label(right_info_frame, text="남은 시간: ")
timer_label.pack()

# 채팅창 프레임
chat_frame = tkinter.Frame(window)
chat_frame.pack(fill=tkinter.BOTH, expand=True, padx=5, pady=5)

# 스크롤을 채팅창 프레임에 담기
scroll = tkinter.Scrollbar(chat_frame)
scroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
# 채팅창을 채팅창 프레임에 담기
chat_list = tkinter.Text(chat_frame, height=15, width=50, wrap=tkinter.WORD, font=('Arial', 10))
chat_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

# 스크롤바를 채팅창과 연결
scroll.config(command=chat_list.yview)
chat_list.config(yscrollcommand=scroll.set)

# 메시지 위아래 간격 설정
chat_list.tag_config("message", spacing1=5, spacing3=5)  

# 입력 창 프레임 설정
input_frame = tkinter.Frame(window)
input_frame.pack(fill=tkinter.X, padx=5, pady=10)

input_msg = tkinter.StringVar()
inputbox = tkinter.Entry(input_frame, textvariable=input_msg)
# enter 입력 시, send_message() 함수 실행
inputbox.bind("<Return>", lambda event: send_message(input_msg))
inputbox.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True, ipady=8)

# enter 입력 시, send_message() 함수 실행
send_button = tkinter.Button(input_frame, text="전송",
                             command=lambda:send_message(input_msg),
                             font=('Arial, 10'),
                             width=5,
                             height=1)
send_button.pack(side=tkinter.RIGHT, padx=5, ipady=3)

# 서버측에서 오는 메세지를 받을(recv_message 함수를 이용) 데몬 쓰레드 설정, 실행
receive_thread = threading.Thread(target=recv_message)
receive_thread.daemon=True
receive_thread.start()

# 창 크기, 위치 설정 후 실행
width = 800
height = 800
x = int((screen_width / 2) - (width / 2))
y = int((screen_height / 2) - (height / 2))
window.geometry('%dx%d+%d+%d' % (width, height, x, y))
window.mainloop()