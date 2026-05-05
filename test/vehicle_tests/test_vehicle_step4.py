from src.entities.vehicle import Vehicle

v1 = Vehicle(0, 5 )
v2 = Vehicle(9, 0 )

for i in range(10):
    v1.update(1, v2)
    v2.update(1)
    distance = v2.position - v1.position
    print("pos:", v1.position,
          "vel:", v1.velocity,
          "acc:", v1.acceleration,
          "dist:", distance)
