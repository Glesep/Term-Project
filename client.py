import tkinter
import sys
import socket
from threading import Thread

win_connect = tkinter.Tk()
win_connect.title("접속대상")

tkinter.Label(win_connect, text="접속대상").grid(row=0, column=0)
input_addr_string = tkinter.StringVar(value="127.0.0.1:8274")
input_addr = tkinter.Entry(win_connect, textvariable=input_addr_string, width=20)
input_addr.grid(row=0, column=1, padx=5, pady=5)
connect_button = tkinter.Button(win_connect, text="접속하기")
connect_button.grid(row=0, column=2, padx=5, pady=5)

width = 280
height = 40

screen_width = win_connect.winfo_screenwidth()
screen_height = win_connect.winfo_screenheight()

x = int((screen_width / 2) - (width / 2))
y = int((screen_height / 2) - (height / 2))

win_connect.geometry(f'{width}x{height}+{x}+{y}')
input_addr.focus()
win_connect.mainloop()













# =========================================================
def recv_message(sock):
    while True:
        msg = sock.recv(1024)
        print(msg.decode())

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 8274))

th = Thread(target=recv_message, args=(sock, ))
th.daemon = True
th.start()

while True:
    msg = input()
    sock.send(msg.encode())
    if msg == "/bye":
        break
sock.close()