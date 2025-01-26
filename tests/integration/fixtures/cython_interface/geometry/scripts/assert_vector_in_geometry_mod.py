from base_math import Vector
from geometry import Rectangle

pos = Vector(1.0, 2.0)
size = Vector(3.0, 4.0)

rect = Rectangle(pos, size)
assert rect.area() == 24.0
print("Regular install test passed!")
