from base_math.operations cimport Vector

cdef class Rectangle:
    def __init__(self, Vector position, Vector size):
        self.position = position
        self.size = size

    cpdef double area(self):
        return self.size.x * self.size.y

    cpdef bint contains_point(self, Vector point):
        return (self.position.x <= point.x <= self.position.x + self.size.x and
                self.position.y <= point.y <= self.position.y + self.size.y)
