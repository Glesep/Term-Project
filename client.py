import tkinter
import threading
import socket
import sys

# 사용자가 입력한 서버의 주소와 포트를 저장하는 변수들
IP = ""
PORT = 0

# 접속 버튼을 눌렀을 때 실행되는 함수
def connect(event=None):
    global IP, PORT
    input_string = input_addr_string.get()
    addr = input_string.split(":")
    IP = addr[0]
    PORT = int(addr[1])
    print(f"서버 접속 [{IP}:{PORT}]")
    win_connect.destroy()

def recv_message():
    global sock
    while True:
        msg = sock.recv(1024)
        chat_list.insert(tkinter.END, msg.decode("utf-8"))
        chat_list.see(tkinter.END)

def send_message(event=None):
    global sock
    message = input_msg.get()
    sock.send(bytes(message, "utf-8"))
    input_msg.set("")
    if message == "/bye":
        sock.close()
        window.quit()
        
# 현재 팝업된 접속대상 윈도우 제거, 프로그램 종료
def window_input_close(event=None):
    print("윈도우 종료")
    win_connect.destroy()
    sys.exit(1)

win_connect = tkinter.Tk()  # 메인 윈도우 역할을 할 위젯 생성
win_connect.protocol("WM_DELETE_WINDOW", window_input_close)    # "WM_DELETE_WINDOW": x버튼을 누를 시 -> window_input_close 실행
win_connect.title("접속대상")   # 위젯의 제목

tkinter.Label(win_connect, text="접속대상").grid(row=0, column=0)
input_addr_string = tkinter.StringVar(value="127.0.0.1:8274")   # tkinter.StringVar(value="127.0.0.1:8274"): 문자열 변수와 연결, 기본 값 = 127.0.0.1:8274
input_addr = tkinter.Entry(win_connect, textvariable=input_addr_string, width=20)
input_addr.grid(row=0, column=1, padx=5, pady=5)

connect_button = tkinter.Button(win_connect, text="접속", command=connect)  # win_connect 객체 안에 "접속"이라는 버튼을 만들고 버튼을 누를 시 connect 함수 실행
connect_button.grid(row=0, column=2, padx=5, pady=5)

width = 280
height = 40

# 현재 모니터의 해상도를 구함
screen_width = win_connect.winfo_screenwidth()
screen_height = win_connect.winfo_screenheight()

x = int((screen_width / 2) - (width / 2))
y = int((screen_height / 2) - (height / 2))

win_connect.geometry(f'{width}x{height}+{x}+{y}')
input_addr.focus()
win_connect.mainloop()

window = tkinter.Tk()
window.title("채팅 클라이언트")

# listbox와 scrollbar를 하나의 그룹으로 묶기 위해 Frame 위젯 사용
frame = tkinter.Frame(window)

# Scrollbar 객체 정의
scroll = tkinter.Scrollbar(frame)
scroll.pack(side = tkinter.RIGHT, fill=tkinter.Y)
# Listbox 객체 정의
chat_list = tkinter.Listbox(frame, height=15, width=50, yscrollcommand=scroll.set)
chat_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH, padx=5, pady=5)

frame.pack()

input_msg = tkinter.StringVar()
inputbox = tkinter.Entry(window, textvariable=input_msg)
# Entry 객체에 입력하는 문자열들은 input_msg에 저장되고, send_message() 내에서 input_msg의 내용을 가져옴
inputbox.bind("<Return>", send_message)
inputbox.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES, padx=5, pady=5)
# 전송 버튼 클릭 시, send_message 실행
send_button = tkinter.Button(window, text="전송", command=send_message)
send_button.pack(side=tkinter.RIGHT, fill=tkinter.X, padx=5, pady=5)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"서버 접속시도 [{IP}:{PORT}]")
r = sock.connect_ex((IP, PORT))
if r == 0:
    receive_thread = threading.Thread(target=recv_message)
    receive_thread.daemon=True
    receive_thread.start()

    width = 383
    height = 292

    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))

    window.geometry(f'{width}x{height}+{x}+{y}')
    window.mainloop()