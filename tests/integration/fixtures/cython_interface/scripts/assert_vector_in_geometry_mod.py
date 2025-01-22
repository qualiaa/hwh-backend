from base_math import Vector
from geometry import Rectangle

# Create vectors
pos = Vector(1.0, 2.0)
size = Vector(3.0, 4.0)

# Create rectangle
rect = Rectangle(pos, size)
assert rect.area() == 12.0
print("Regular install test passed!")
