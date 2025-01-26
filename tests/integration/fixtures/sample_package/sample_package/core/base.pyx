
cdef class BaseOp:
    def __init__(self, double value):
        print("Hello from BaseOp")
        self.value = value
    
    cpdef double compute(self):
        print("<compute compute>")

        return self.value * 2.0
