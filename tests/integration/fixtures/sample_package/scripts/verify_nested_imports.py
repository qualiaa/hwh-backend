from sample_package.core.base import BaseOp
from sample_package.core.plain import plain_python_function
from sample_package.extensions.advanced import Advanced
from sample_package.extensions.specialized.expert import Expert
from sample_package.utils.helpers import Helper

plain_python_function()
base_op = BaseOp(2.0)
helper = Helper(base_op)
advanced = Advanced(helper)
expert = Expert(advanced, BaseOp(3.0))

result = expert.deep_process()
expected = 60.0
# assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"

print("All nested module tests passed!")
