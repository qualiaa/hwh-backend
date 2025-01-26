
from sample_package.core.base cimport BaseOp

cdef class DependentOp:
    cdef:
        readonly BaseOp base_op
        readonly double factor
    
    cpdef double enhanced_compute(self)
