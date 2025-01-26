from dependent_package.operations import DependentOp
from sample_package.core.base import BaseOp

base = BaseOp(2.0)
assert base.compute() == 4.0, "Base computation failed"

enhanced = DependentOp(base, 3.0)
result = enhanced.enhanced_compute()
assert result == 13.0, f"Enhanced computation failed. Expected 12.0, got {result}"

print("Cython dependency test passed!")
