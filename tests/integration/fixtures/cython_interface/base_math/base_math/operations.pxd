cdef class Vector:
    cdef:
        readonly double x
        readonly double y

    cpdef Vector add(self, Vector other)
    cpdef double dot(self, Vector other)
    cpdef Vector scale(self, double factor)
