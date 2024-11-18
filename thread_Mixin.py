# ThreadMixin 실습

import time
import threading

def getOrder():
    for i in range(5):
        print (f"주문밭기 {i}")
        time.sleep(i)
        
def makeCoffee():
    for i in range(5):
        print (f"커피만들기{i}")
        time.sleep(1)
        
'''
쓰레드 = 일꾼
일꾼 한 명은 2가지 일을 동시에 할 수 없음
따라서 주문받기가 끝나야만 커피를 만들 수 있음
'''

# getOrder()
# makeCoffee()

'''
기존의 일꾼(쓰레드) 1명으로 처리하던 일을
일을 전담할 서브 일꾼(쓰레드)을 2명 뽑아서 각각 일을 맡김

기존의 일꾼(메인 쓰레드)는 서브 일꾼을 관리하는 일을 함

th1 = 주문을 받는 일을 처리하는 쓰레드
th2 = 커피만드는 일을 처리하는 쓰레드
'''
th1 = threading.Thread(target=getOrder)
th2 = threading.Thread(target=makeCoffee)

# 일 시작
th1.start()
th2.start()