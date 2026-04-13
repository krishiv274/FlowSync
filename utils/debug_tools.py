def print_lane_state(lane):
    print(f"\nLane {lane.id} state:")
    
    for i, v in enumerate(lane.vehicles):
        lead = None
        if i + 1 < len(lane.vehicles):
            lead = lane.vehicles[i + 1].id

        print(
            f"Vehicle {v.id} -> pos: {v.position:.2f} | "
            f"lead: {lead}"
        )


def check_sorted(lane):
    for i in range(len(lane.vehicles) - 1):
        v1 = lane.vehicles[i]
        v2 = lane.vehicles[i + 1]

        assert v1.position <= v2.position, (
            f"Sorting error: Vehicle {v1.id} ({v1.position}) "
            f"is ahead of Vehicle {v2.id} ({v2.position})"
        )


def check_no_overlap(lane, min_gap=0.1):
    for i in range(len(lane.vehicles) - 1):
        v1 = lane.vehicles[i]
        v2 = lane.vehicles[i + 1]

        gap = v2.position - v1.position
        assert gap >= min_gap, (
            f"Overlap detected: Vehicle {v1.id} and {v2.id} gap={gap}"
        )
