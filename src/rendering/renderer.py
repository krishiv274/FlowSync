"""Renderer for traffic simulation visualization."""


class Renderer:
    """Handles rendering of simulation entities."""

    def __init__(self, width=1200, height=800, title="FlowSync"):
        """Initialize the renderer and try to create a pygame window."""
        self.width = width
        self.height = height
        self.title = title
        self.frame_count = 0
        self.initialized = False
        self.console_fallback = False
        self.pygame = None
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.background_color = (20, 24, 32)
        self.road_color = (52, 58, 68)
        self.lane_color = (120, 126, 138)
        self.edge_color = (30, 34, 42)
        self.vehicle_color = (70, 150, 255)
        self.stopped_vehicle_color = (245, 124, 0)
        self.signal_outline_color = (18, 18, 18)
        self.overlay_color = (240, 242, 246)
        self.initialize()

    def initialize(self):
        """Initialize pygame resources if possible."""
        if self.initialized or self.console_fallback:
            return

        try:
            import pygame

            pygame.init()
            self.pygame = pygame
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption(self.title)
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("Arial", 18)
            self.small_font = pygame.font.SysFont("Arial", 14)
            self.initialized = True
        except Exception:
            self.console_fallback = True
            self.pygame = None
            self.screen = None
            self.clock = None
            self.font = None
            self.small_font = None

    def handle_events(self):
        """Process window events and return False when the app should exit."""
        if not self.initialized or self.pygame is None:
            return True

        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                return False
            if event.type == self.pygame.KEYDOWN and event.key == self.pygame.K_ESCAPE:
                return False
            if event.type == self.pygame.VIDEORESIZE:
                self.width = max(640, event.w)
                self.height = max(480, event.h)
                self.screen = self.pygame.display.set_mode(
                    (self.width, self.height),
                    self.pygame.RESIZABLE,
                )

        return True

    def update(self):
        """Advance renderer timing and maintain a steady frame rate."""
        if self.initialized and self.clock is not None:
            self.clock.tick(60)

    def draw(self, roads, vehicles, signals):
        """Draw the traffic simulation."""
        self.frame_count += 1

        if self.console_fallback or self.pygame is None:
            self._draw_console(roads, vehicles, signals)
            return

        if not self.initialized:
            self.initialize()
            if self.console_fallback or self.pygame is None:
                self._draw_console(roads, vehicles, signals)
                return

        self.screen.fill(self.background_color)
        self._draw_roads(roads)
        self._draw_signals(signals)
        self._draw_vehicles(roads, vehicles)
        self._draw_overlay(roads, vehicles, signals)
        self.pygame.display.flip()

    def shutdown(self):
        """Release pygame resources."""
        if self.pygame is not None:
            try:
                self.pygame.quit()
            except Exception:
                pass
        self.initialized = False

    def _draw_console(self, roads, vehicles, signals):
        print(f"\n--- Frame {self.frame_count} ---")
        print(f"Roads: {len(roads)}")
        print("Vehicles:")
        for vehicle in vehicles:
            pos = getattr(vehicle, "position", None)
            vel = getattr(vehicle, "velocity", None)
            print(f"  Vehicle id={getattr(vehicle, 'id', id(vehicle))} pos={pos} vel={vel}")
        print("Signals:")
        for signal in signals:
            state = getattr(signal, "state", None)
            print(f"  Signal id={getattr(signal, 'id', id(signal))} state={state}")

    def _draw_roads(self, roads):
        lane_height = 48
        road_width = self.width - 160
        x = 80

        for road_index, road in enumerate(roads):
            lanes = getattr(road, "lanes", [])
            lane_count = max(1, len(lanes))
            road_top = 70 + road_index * (lane_count * lane_height + 90)
            road_bottom = road_top + lane_count * lane_height

            self.pygame.draw.rect(
                self.screen,
                self.edge_color,
                (x - 10, road_top - 16, road_width + 20, road_bottom - road_top + 32),
                border_radius=18,
            )
            self.pygame.draw.rect(
                self.screen,
                self.road_color,
                (x, road_top, road_width, road_bottom - road_top),
                border_radius=14,
            )

            for lane_index in range(1, lane_count):
                y = road_top + lane_index * lane_height
                self.pygame.draw.line(
                    self.screen,
                    self.lane_color,
                    (x + 18, y),
                    (x + road_width - 18, y),
                    2,
                )

            for lane_index, lane in enumerate(lanes):
                lane_center = road_top + lane_index * lane_height + lane_height // 2
                label = self.small_font.render(
                    f"Road {getattr(road, 'id', road_index + 1)} Lane {getattr(lane, 'id', lane_index + 1)}",
                    True,
                    self.overlay_color,
                )
                self.screen.blit(label, (x + 8, lane_center - 28))

    def _draw_vehicles(self, roads, vehicles):
        road_map = self._build_lane_layout(roads)

        for vehicle in vehicles:
            lane = getattr(vehicle, "lane", None)
            lane_info = road_map.get(lane)
            if lane_info is None:
                continue

            road_top, lane_height, x, road_width, lane_index = lane_info
            road_length = max(1.0, float(getattr(lane, "length", 1000)))
            position = float(getattr(vehicle, "position", 0.0))
            x_pos = x + min(max(position / road_length, 0.0), 1.0) * road_width
            y_pos = road_top + lane_index * lane_height + lane_height / 2

            velocity = float(getattr(vehicle, "velocity", 0.0))
            vehicle_color = self.vehicle_color if velocity > 0 else self.stopped_vehicle_color
            rect = self.pygame.Rect(0, 0, 26, 14)
            rect.center = (int(x_pos), int(y_pos))
            self.pygame.draw.rect(self.screen, vehicle_color, rect, border_radius=4)
            self.pygame.draw.rect(self.screen, (18, 18, 18), rect, 1, border_radius=4)

            label = self.small_font.render(str(getattr(vehicle, "id", "V")), True, (255, 255, 255))
            self.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.top - 16))

    def _draw_signals(self, signals):
        signal_colors = {
            "RED": (220, 72, 72),
            "YELLOW": (245, 196, 72),
            "GREEN": (88, 190, 117),
        }

        for signal in signals:
            position = getattr(signal, "position", (0, 0))
            if not isinstance(position, tuple) or len(position) != 2:
                continue

            x_pos, y_pos = position
            state = getattr(signal, "state", "RED")
            color = signal_colors.get(state, (200, 200, 200))
            body = self.pygame.Rect(int(x_pos) - 10, int(y_pos) - 22, 20, 44)
            light = self.pygame.Rect(0, 0, 14, 14)
            light.center = body.center

            self.pygame.draw.rect(self.screen, (28, 28, 28), body, border_radius=8)
            self.pygame.draw.rect(self.screen, self.signal_outline_color, body, 2, border_radius=8)
            self.pygame.draw.circle(self.screen, color, light.center, 6)

            label = self.small_font.render(f"S{getattr(signal, 'id', '?')}:{state}", True, self.overlay_color)
            self.screen.blit(label, (body.left - 12, body.bottom + 4))

    def _draw_overlay(self, roads, vehicles, signals):
        lines = [
            f"Frame: {self.frame_count}",
            f"Roads: {len(roads)}  Vehicles: {len(vehicles)}  Signals: {len(signals)}",
            "Controls: ESC quit",
        ]

        x = 16
        y = 14
        for line in lines:
            text = self.small_font.render(line, True, self.overlay_color)
            self.screen.blit(text, (x, y))
            y += 18

    def _build_lane_layout(self, roads):
        layout = {}
        lane_height = 48
        road_width = self.width - 160
        x = 80

        for road_index, road in enumerate(roads):
            lanes = getattr(road, "lanes", [])
            lane_count = max(1, len(lanes))
            road_top = 70 + road_index * (lane_count * lane_height + 90)

            for lane_index, lane in enumerate(lanes):
                layout[lane] = (road_top, lane_height, x, road_width, lane_index)

        return layout
