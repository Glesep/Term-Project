import tkinter
import threading
import socket
import sys
import time

IP = ""
PORT = 0
MyNickname = ""
MyWord = ""
timer_thread = None
timer_running = False

def window_input_close(win_object):
    print("윈도우 종료")
    
    # 채팅창에서 나갈 때
    if 'window' in globals() and win_object == window:
        bye = tkinter.StringVar(value="/bye")
        send_message(bye)

    # 닉네임 설정 창에서 나갈 때
    elif 'win_nickname' in globals() and win_object == win_nickname:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        win_object.destroy()
    
    # 연결 창에서 나갈 때
    else:
        win_object.destroy()
        
    sys.exit(1)


def connect(event=None):
    global IP, PORT, sock
    input_string = input_addr_string.get()
    addr = input_string.split(":")
    IP = addr[0]
    PORT = int(addr[1])
    
    
    print(f"서버 접속시도 [{IP}:{PORT}]")
    connectionResult = sock.connect_ex((IP, PORT))
    if connectionResult == 0:
        print ("접속 성공")
        win_connect.destroy()
    else:
        print("접속 실패")
    


def set_nickname(msg):
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
    global timer_running
    timer_running = True
    remaining_time = 60
    
    while timer_running and remaining_time > 0:
        timer_label.config(text=f"남은 시간: {remaining_time}초")
        time.sleep(1)
        remaining_time -= 1
        
    if timer_running:
        timer_label.config(text="시간 초과!")
        sock.send("/timeout".encode())

def reset_timer():
    global timer_running
    timer_running = False
    timer_label.config(text="남은 시간: 60초")

def recv_message():
    global sock, timer_thread
    while True:
        try:
            if not sock:
                break
        
            msg = sock.recv(1024)
            msg_decode = msg.decode()

            if "승리하셨습니다!!" in msg_decode or "퇴장" in msg_decode:
                reset_timer()
                timer_label.config(text="남은 시간: ")
                nickname_label.config(fg="black")
                word_label.config(text=f"나의 단어: ")

            if "당신의 차례입니다" in msg_decode:
                if timer_thread:
                    reset_timer()
                timer_thread = threading.Thread(target=start_timer)
                timer_thread.daemon = True
                timer_thread.start()

            elif "상대방의" in msg_decode:
                reset_timer()

            if msg_decode.startswith("/t"):
                word = msg_decode[len("/t"):].strip()
                word_label.config(text=f"나의 단어: {word}")


            else:
                chat_list.insert(tkinter.END, msg_decode + "\n", "message")
                chat_list.see(tkinter.END)
        except:
            break
def send_message(msg):
    global sock
    message = msg.get()
    
    if message == "/start":
        nickname_label.config(fg="blue")
    
    sock.send(message.encode())
    msg.set("")
    
    if message == "/bye":
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        window.destroy()


# =================================================================================


# GUI 초기화 코드
win_connect = tkinter.Tk()
win_connect.protocol("WM_DELETE_WINDOW", lambda: window_input_close(win_connect))
win_connect.title("접속대상")

tkinter.Label(win_connect, text="접속대상").grid(row=0, column=0)


input_addr_string = tkinter.StringVar(value="127.0.0.1:8274")

input_addr = tkinter.Entry(win_connect, textvariable=input_addr_string, width=20)
input_addr.grid(row=0, column=1, padx=5, pady=5)
input_addr.bind("<Return>", lambda event: connect())

connect_button = tkinter.Button(win_connect, text="접속하기", command=connect)
connect_button.grid(row=0, column=2, padx=5, pady=5)

width = 280
height = 40
screen_width = win_connect.winfo_screenwidth()
screen_height = win_connect.winfo_screenheight()
x = int((screen_width / 2) - (width / 2))
y = int((screen_height / 2) - (height / 2))
win_connect.geometry('%dx%d+%d+%d' % (width, height, x, y))
input_addr.focus()

# 소켓 연결 준비
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

win_connect.mainloop()




# 닉네임 입력 창
win_nickname = tkinter.Tk()
win_nickname.protocol("WM_DELETE_WINDOW", lambda: window_input_close(win_nickname))
win_nickname.title("닉네임 입력")

tkinter.Label(win_nickname, text="닉네임 입력").grid(row=0, column=0)
input_nickname_str = tkinter.StringVar()
input_nickname = tkinter.Entry(win_nickname, textvariable=input_nickname_str, width=20)
input_nickname.grid(row=0, column=1, padx=5, pady=5)
input_nickname.bind("<Return>", lambda event: set_nickname(input_nickname_str))

input_nickname_button = tkinter.Button(win_nickname, text="확인", command=lambda:set_nickname(input_nickname_str))
input_nickname_button.grid(row=0, column=2, padx=5, pady=5)

win_nickname.geometry('%dx%d+%d+%d' % (width, height, x, y))
input_nickname.focus()
win_nickname.mainloop()




# 메인 채팅창
window = tkinter.Tk()
window.protocol("WM_DELETE_WINDOW", lambda: window_input_close(window))
window.title("채팅 클라이언트")

# 상단 정보를 담을 프레임
info_frame = tkinter.Frame(window)
info_frame.pack(fill=tkinter.X, padx=5, pady=5)
# 왼쪽에 닉네임 표시
nickname_label = tkinter.Label(info_frame, text=f"나의 닉네임: {MyNickname}", anchor="w")
nickname_label.pack(side=tkinter.LEFT)

right_info_frame = tkinter.Frame(info_frame)
right_info_frame.pack(side=tkinter.RIGHT)
# 단어 레이블
word_label = tkinter.Label(right_info_frame, text=f"나의 단어: {MyWord}")
word_label.pack()
# 타이머 레이블
timer_label = tkinter.Label(right_info_frame, text="남은 시간: ")
timer_label.pack()

chat_frame = tkinter.Frame(window)
chat_frame.pack(fill=tkinter.BOTH, expand=True, padx=5, pady=5)

scroll = tkinter.Scrollbar(chat_frame)
scroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)

chat_list = tkinter.Text(chat_frame, height=15, width=50, wrap=tkinter.WORD, font=('Arial', 10))
chat_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

# 스크롤바 연결
scroll.config(command=chat_list.yview)
chat_list.config(yscrollcommand=scroll.set)

# Text 위젯에 태그 설정
chat_list.tag_config("message", spacing1=5, spacing3=5)  # 메시지 위아래 간격 설정


input_frame = tkinter.Frame(window)
input_frame.pack(fill=tkinter.X, padx=5, pady=10)

input_msg = tkinter.StringVar()
inputbox = tkinter.Entry(input_frame, textvariable=input_msg)
inputbox.bind("<Return>", lambda event: send_message(input_msg))
inputbox.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True, ipady=8)

send_button = tkinter.Button(input_frame, text="전송",
                             command=lambda:send_message(input_msg),
                             font=('Arial, 10'),
                             width=5,
                             height=1)
send_button.pack(side=tkinter.RIGHT, padx=5, ipady=3)

receive_thread = threading.Thread(target=recv_message)
receive_thread.daemon=True
receive_thread.start()

width = 800
height = 800
x = int((screen_width / 2) - (width / 2))
y = int((screen_height / 2) - (height / 2))
window.geometry('%dx%d+%d+%d' % (width, height, x, y))
window.mainloop()