from base_math import Vector
from geometry import Rectangle

# Create vectors
pos = Vector(1.0, 2.0)
size = Vector(3.0, 4.0)

# Create rectangle
rect = Rectangle(pos, size)

# Test area calculation
assert rect.area() == 12.0, f"Expected area 12.0, got {rect.area()}"

# Test point containment
point_inside = Vector(2.0, 3.0)
point_outside = Vector(0.0, 0.0)

assert rect.contains_point(point_inside), "Point should be inside rectangle"
assert not rect.contains_point(point_outside), "Point should be outside rectangle"

# Test vector operations
v1 = Vector(1.0, 2.0)
v2 = Vector(3.0, 4.0)
v3 = v1.add(v2)
assert v3.x == 4.0 and v3.y == 6.0, "Vector addition failed"

dot_product = v1.dot(v2)
assert dot_product == 11.0, f"Expected dot product 11.0, got {dot_product}"

scaled = v1.scale(2.0)
assert scaled.x == 2.0 and scaled.y == 4.0, "Vector scaling failed"

print("All tests passed!")
