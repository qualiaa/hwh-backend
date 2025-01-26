
from base_math.operations cimport Vector

cdef class Rectangle:
    cdef:
        readonly Vector position
        readonly Vector size

    cpdef double area(self)
    cpdef bint contains_point(self, Vector point)
