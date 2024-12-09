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
    win_object.destroy()
    sys.exit(1)


def connect(event=None):
    global IP, PORT
    input_string = input_addr_string.get()
    addr = input_string.split(":")
    IP = addr[0]
    PORT = int(addr[1])
    win_connect.destroy()


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
        msg = sock.recv(1024)
        msg_decode = msg.decode()
        
        if "승리하셨습니다!!" in msg_decode:
            reset_timer()
            timer_label.config(text="남은 시간: ")
        
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
            chat_list.insert(tkinter.END, msg_decode)
            chat_list.see(tkinter.END)

def send_message(msg):
    global sock
    message = msg.get()
    sock.send(message.encode())
    msg.set("")
    if message == "/bye":
        sock.close()
        window.quit()


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
win_connect.mainloop()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"서버 접속시도 [{IP}:{PORT}]")
connectionResult = sock.connect_ex((IP, PORT))
print(connectionResult)

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

nickname_label = tkinter.Label(window, text=f"나의 닉네임: {MyNickname}", anchor="w")
nickname_label.pack(side=tkinter.TOP, fill=tkinter.X, padx=5, pady=5)

word_label = tkinter.Label(window, text=f"나의 단어: {MyWord}")
word_label.place(relx=1.0, rely=0.0, anchor='ne')

# 타이머 레이블
timer_label = tkinter.Label(window, text="남은 시간: 60초")
timer_label.place(relx=1.0, rely=0.05, anchor='ne')

frame = tkinter.Frame(window)
scroll = tkinter.Scrollbar(frame)
scroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
chat_list = tkinter.Listbox(frame, height=15, width=50, yscrollcommand=scroll.set)
chat_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH, padx=5, pady=5)
frame.pack()

input_msg = tkinter.StringVar()
inputbox = tkinter.Entry(window, textvariable=input_msg)
inputbox.bind("<Return>", lambda event: send_message(input_msg))
inputbox.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES, padx=5, pady=5)

send_button = tkinter.Button(window, text="전송", command=lambda:send_message(input_msg))
send_button.pack(side=tkinter.RIGHT, fill=tkinter.X, padx=5, pady=5)

receive_thread = threading.Thread(target=recv_message)
receive_thread.daemon=True
receive_thread.start()

width = 383
height = 400
x = int((screen_width / 2) - (width / 2))
y = int((screen_height / 2) - (height / 2))
window.geometry('%dx%d+%d+%d' % (width, height, x, y))
window.mainloop()