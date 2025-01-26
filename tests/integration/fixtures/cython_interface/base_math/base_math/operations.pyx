cdef class Vector:
    def __init__(self, double x, double y):
        self.x = x
        self.y = y

    cpdef Vector add(self, Vector other):
        return Vector(self.x + other.x, self.y + other.y)

    cpdef double dot(self, Vector other):
        return self.x * other.x + self.y * other.y

    cpdef Vector scale(self, double factor):
        return Vector(self.x * factor, self.y * factor)
