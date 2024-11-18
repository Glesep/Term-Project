class A:
    num = 5
    def start(self):
        for i in range(self.num):
            print(i)
            
class B:
    # __init__ 함수는 생성자 역할을 한다
    def __init__(self, name):
        self.name = name
        self.start()

# A와 B를 다중상속 받은 클래스 C
class C(A, B):
    def myprint(self):
        print(self.name)
        
_c = C("Yoon")
_c.myprint()