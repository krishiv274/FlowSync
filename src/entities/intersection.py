class Intersection:
    def __init__(self, intersection_id):
        self.id = intersection_id
        self.incoming_roads = []
        self.outgoing_roads = []
        self.signals = {}

    def add_incoming_road(self, road):
        self.incoming_roads.append(road)

    def add_outgoing_road(self, road):
        self.outgoing_roads.append(road)

    def add_signal(self, lane, signal):
        self.signals[lane] = signal
        return signal

    def get_signal_for_lane(self, lane):
        return self.signals.get(lane)

    def update(self, dt):
        """Update all signals at this intersection.
        
        Args:
            dt: Time step in seconds
        """
        for signal in self.signals.values():
            signal.update(dt)