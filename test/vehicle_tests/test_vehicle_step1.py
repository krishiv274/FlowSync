from src.entities.vehicle import Vehicle

v = Vehicle(0, 10)

for i in range(5):
    print(f"Time={i}, Position={v.position}, Velocity={v.velocity}")
    v.update(1)
