from src.entities.vehicle import Vehicle
from src.physics.simple_model import SimpleModel

model = SimpleModel()

v1 = Vehicle(0, 5, model)
v2 = Vehicle(10, 0, model)

for i in range(10):
    v1.update(1, v2)
    v2.update(1)
    gap = round(v2.position - v1.position, 2)
    print("acc:", v1.acceleration, "gap:", gap)
