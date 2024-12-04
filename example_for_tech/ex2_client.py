import tkinter
import threading
import socket
import sys


IP = ""
PORT = 0

# X 버튼을 눌러 종료를 하였을 떄
def window_input_close(event=None):
    print("윈도우 종료")
    win_connect.destroy()
    # 프로그램 종료
    sys.exit(1)

# 접속 버튼을 눌렀을 때
def connect(event=None):
    global IP, PORT
    # input_addr_string의 값을 받아서 변수에 저장
    input_string = input_addr_string.get()
    # IP와 PORT번호 분리
    addr = input_string.split(":")

    IP = addr[0]
    PORT = int(addr[1])
    print("서버 접속 [{}:{}]".format(IP, PORT))
    
    # 작업이 끝난 후 창을 닫음
    win_connect.destroy()

def recv_message():
    global sock
    while True:
        msg = sock.recv(1024)
        # tkinter.END : 현재 내용의 가장 끝 위치 참조
        # 가장 끝 위치에 msg 내용을 기록하겠다
        chat_list.insert(tkinter.END, msg.decode("utf-8"))
        # 가장 끝 위치로 자동 스크롤을 내리겠다
        chat_list.see(tkinter.END)

def send_message(event=None):
    global sock
    # input_msg의 내용을 가져옴
    message = input_msg.get()
    sock.send(bytes(message, "utf-8"))
    # input_msg의 값을 빈 문자열으로 설정
    input_msg.set("")
    if message == "/bye":
        sock.close()
        window.quit()


# =================================================================
    
    
win_connect = tkinter.Tk()
# X 버튼을 누를 때 실행되는 함수 연결
win_connect.protocol("WM_DELETE_WINDOW", window_input_close)
win_connect.title("접속대상")

# 라벨 추가, 그리드를 설정해야 배치됨
tkinter.Label(win_connect, text="접속대상").grid(row=0, column=0)

# tkinter의 문자열 데이터 전용 변수
input_addr_string = tkinter.StringVar(value="127.0.0.1:8274")

# 사용자로부터 텍스트 입력을 받는 단일 텍스트 박스
# win_connect 윈도우에 추가, textvariable - 이전에 생성한 변수와 연결, 위젯 너비 20
input_addr = tkinter.Entry(win_connect, textvariable=input_addr_string, width=20)

# 그리드 설정, 여백 추가
input_addr.grid(row=0, column=1, padx=5, pady=5)

# 접속하기 버튼 추가, 접속하기 버튼을 눌렀을 때 connect 함수 실행
connect_button = tkinter.Button(win_connect, text="접속하기", command=connect)

# 그리드 설정, 여백 추가
connect_button.grid(row=0, column=2, padx=5, pady=5)

width = 280
height = 40

# 현재 모니터의 크기를 가져오기
screen_width = win_connect.winfo_screenwidth()
screen_height = win_connect.winfo_screenheight()

# 모니터의 중앙 위치 계산
x = int((screen_width / 2) - (width / 2))
y = int((screen_height / 2) - (height / 2))

# 윈도우 크기와 위치 설정 (width, height: 크기, x, y: 위치)
win_connect.geometry('%dx%d+%d+%d' % (width, height, x, y))

# 텍스트 박스에 포커스를 줌으로써 윈도우가 시작되자마자 텍스트 입력 가능
input_addr.focus()

# Tkinter GUI 프로그램 실행
win_connect.mainloop()

window = tkinter.Tk()
window.title("채팅 클라이언트")
# 프레임을 사용하여 다른 위젯들을 담는 컨테이너 역할으로 사용
frame = tkinter.Frame(window)
# 스크롤바 생성
scroll = tkinter.Scrollbar(frame)
# 부모 위젯의 오른쪽에 scroll 배치, scroll을 부모 위젯의 높이만큼 확장
scroll.pack(side = tkinter.RIGHT, fill=tkinter.Y)
# Listbox를 프레임안에 담고 scroll과 연결
chat_list = tkinter.Listbox(frame, height=15, width=50, yscrollcommand=scroll.set)
# 부모 위젯의 왼쪽에 Listbox 배치, Listbox를 수직 수평 모두 확장
chat_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH, padx=5, pady=5)
# 프레임 생성
frame.pack()

# 문자열 변수 설정
input_msg = tkinter.StringVar()
# 입력 창 설정
inputbox = tkinter.Entry(window, textvariable=input_msg)
# 입력 창에 enter 키 이벤트가 일어났을 때 send_message 함수를 실행
inputbox.bind("<Return>", send_message)

# 왼쪽에, 상하좌우 확장하며, 사용 공간을 확장하며 배치
inputbox.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES, padx=5, pady=5)
# 전송 버튼 생성, 누를 시 send_message 함수 실행
send_button = tkinter.Button(window, text="전송", command=send_message)
# 오른쪽에, 좌우 확장하며 배치
send_button.pack(side=tkinter.RIGHT, fill=tkinter.X, padx=5, pady=5)


# 소캣 제작
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print(f"서버 접속시도 [{IP}:{PORT}]")
# 소켓 연결 시도 후 코드 반환(0: 연결 성공, 0 이외의 값: 연결 실패)
connectionResult = sock.connect_ex((IP, PORT))
# 연결 성공 시
if connectionResult == 0:
    # recv_message 함수에 대한 데몬 쓰레드 실행
    receive_thread = threading.Thread(target=recv_message)
    receive_thread.daemon=True
    receive_thread.start()

    # 채팅창 크기 설정 이후 창 실행
    width = 383
    height = 292

    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))

    window.geometry('%dx%d+%d+%d' % (width, height, x, y))
    window.mainloop()


win_connect.mainloop()