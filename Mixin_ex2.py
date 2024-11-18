class A:
    def start(self):
        print("A start")
        
class B:
    def __init__(self, name):
        self.name = name
        
class C(A, B):
    # C 클래스에서 start() 함수 오버라이딩
    def start(self):
        print("C start")
    
    # 부모 클래스 A의 start를 실행하고 싶으면 super()함수 사용
    """
    def start(self):
        super().start()
        print("C start")
    """
        
_c = C("Yoon")
_c.start()