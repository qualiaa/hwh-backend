
from sample_package.core.base cimport BaseOp

cdef class DependentOp:
    def __init__(self, BaseOp base_op, double factor):
        self.base_op = base_op
        self.factor = factor
    
    cpdef double enhanced_compute(self):
        return self.base_op.compute() * self.factor
