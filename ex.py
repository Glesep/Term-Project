import threading
import time

def regular_thread_work():
    for i in range(3):
        print(f"일반 쓰레드 작업 {i}")
        time.sleep(1)

# 일반 쓰레드 생성
thread = threading.Thread(target=regular_thread_work, daemon=True)
thread.start()

# 주 쓰레드 작업
print("주 쓰레드 작업 시작")
time.sleep(2)
print("주 쓰레드 작업 종료")

# 일반 쓰레드가 완료될 때까지 대기
# thread.join()