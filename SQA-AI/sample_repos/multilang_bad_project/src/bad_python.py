def monster(a, b, c, d, e, f, g, h, i, j):
    x = 0
    for n in range(100):
        if n % 2 == 0:
            if a > 0:
                if b > 0:
                    if c > 0:
                        if d > 0:
                            x += 1
                        else:
                            x += 2
                    else:
                        x += 3
                else:
                    x += 4
            else:
                x += 5
        else:
            if e < 0:
                x -= 1
            elif f < 0:
                x -= 2
            elif g < 0:
                x -= 3
            elif h < 0:
                x -= 4
            else:
                x -= 5

        try:
            if (i + j) % 3 == 0:
                x += 10
            else:
                x -= 10
        except Exception:
            x += 0

    return x


class GodClass:
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3
        self.d = 4
        self.e = 5
        

    def method1(self, x): return x + 1
    def method2(self, x): return x + 2
    def method3(self, x): return x + 3
    def method4(self, x): return x + 4
    def method5(self, x): return x + 5
    def method6(self, x): return x + 6
    def method7(self, x): return x + 7
    def method8(self, x): return x + 8
    def method9(self, x): return x + 9
    def method10(self, x): return x + 10
    
# change by Dave
