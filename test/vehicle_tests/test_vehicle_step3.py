from src.entities.vehicle import Vehicle

v1 = Vehicle(0, 0, 4)
v2 = Vehicle(20, 0, 2)

for i in range(5):
    distance = v2.position - v1.position
    print(distance, v1.acceleration, v2.acceleration)
    v1.update(i)
    v2.update(i)
