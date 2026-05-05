"""Interactive pygame renderer with a lightweight UI traffic layer.

The renderer never mutates backend roads, lanes, vehicles, or signals. When
backend vehicles are present they are rendered first. The UI vehicle layer is
kept separate and exists only to make the visualization interactive.
"""

from __future__ import annotations

import math
import random
from typing import Any, Iterable, cast


WIDTH = 800
HEIGHT = 800
CENTER = (400, 400)
INTERSECTION_START = 350
INTERSECTION_END = 450
STOP_LINE = 332
CAR_LENGTH = 46
CAR_WIDTH = 28


class Camera:
    """World/screen transform used by all drawing and hit testing."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.scale = 1.0
        self.min_scale = 0.45
        self.max_scale = 2.8

    def world_to_screen(self, x: float, y: float) -> tuple[int, int]:
        sx = (x - self.offset_x) * self.scale + self.width * 0.5
        sy = (y - self.offset_y) * self.scale + self.height * 0.5
        return int(round(sx)), int(round(sy))

    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        wx = (x - self.width * 0.5) / max(self.scale, 0.001) + self.offset_x
        wy = (y - self.height * 0.5) / max(self.scale, 0.001) + self.offset_y
        return wx, wy

    def rect_to_screen(self, rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
        x, y, w, h = rect
        x0, y0 = self.world_to_screen(x, y)
        x1, y1 = self.world_to_screen(x + w, y + h)
        return min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)

    def pan(self, dx: float, dy: float) -> None:
        self.offset_x += dx / max(self.scale, 0.001)
        self.offset_y += dy / max(self.scale, 0.001)

    def zoom(self, factor: float) -> None:
        self.scale = max(self.min_scale, min(self.max_scale, self.scale * factor))

    def focus_intersection(self) -> None:
        self.offset_x = 0.0
        self.offset_y = 0.0


class Renderer:
    """Rendering and UI event emitter for traffic simulation."""

    SPAWN_DIRECTIONS = ("N", "S", "E", "W")
    TURNS = ("LEFT", "RIGHT", "STRAIGHT")

    def __init__(
        self,
        traffic_manager: Any | None = None,
        width: int = WIDTH,
        height: int = HEIGHT,
        title: str = "FlowSync Intersection Demo",
    ) -> None:
        self.traffic_manager = traffic_manager
        self.width = width
        self.height = height
        self.title = title

        self.pygame: Any = None
        self.screen: Any = None
        self.clock: Any = None
        self.font: Any = None
        self.small_font: Any = None
        self.initialized: bool = False
        self.console_fallback = False

        self.camera = Camera(width, height)
        self.running = True
        self.paused = False
        self.debug = False
        self.place_signal_mode = False
        self.keys_down: set[int] = set()

        self.ui_events: dict[str, Any] = self._new_event_packet()
        self._events_processed_since_draw = False

        self.ui_vehicles: list[dict[str, Any]] = []
        self.signals: list[dict[str, Any]] = []
        self.selected_signal: Any | None = None
        self.backend_signal_overrides: dict[int, str] = {}
        self._next_vehicle_id = 1
        self._next_signal_id = 1

        self.road_length = 940.0
        self.lane_offset = 28.0
        self.road_width = 86.0
        self.vehicle_radius = 7.0
        self.spawn_gap = 40.0
        self.min_gap = 24.0
        self.max_intersection_vehicles = 2
        self.base_speed = 118.0
        self.turn_zone = 22.0
        self.intersection_size = 96.0
        self._lane_geometry = self._build_lane_geometry()
        self.lane_directions = {
            "top_lane": "RIGHT",
            "bottom_lane": "LEFT",
            "left_lane": "DOWN",
            "right_lane": "UP",
        }

        self.colors = {
            "background": (21, 26, 27),
            "road": (43, 47, 50),
            "road_edge": (27, 30, 32),
            "lane": (232, 235, 231),
            "lane_dim": (158, 166, 161),
            "intersection": (118, 124, 122),
            "intersection_fill": (94, 100, 99),
            "panel": (16, 19, 20),
            "panel_border": (70, 78, 77),
            "text": (236, 239, 235),
            "muted": (169, 176, 172),
            "moving": (71, 207, 112),
            "slow": (245, 202, 67),
            "stopped": (234, 75, 69),
            "real_vehicle": (82, 169, 246),
            "signal_body": (17, 18, 19),
            "red": (238, 61, 57),
            "yellow": (248, 205, 75),
            "green": (72, 202, 106),
            "selection": (91, 180, 255),
            "off": (69, 73, 74),
        }

        self.initialize()

    def initialize(self) -> None:
        if self.initialized or self.console_fallback:
            return

        try:
            import pygame

            pygame.init()
            self.pygame = pygame
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            pygame.display.set_caption(self.title)
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("Arial", 17)
            self.small_font = pygame.font.SysFont("Arial", 13)
            self.initialized = True
        except Exception:
            self.console_fallback = True

    def draw(
        self,
        roads: Iterable[Any] | None = None,
        vehicles: Iterable[Any] | None = None,
        signals: Iterable[Any] | None = None,
    ) -> None:
        """Draw one frame. Backend state is read-only and optional."""
        if not self.initialized and not self.console_fallback:
            self.initialize()

        roads, real_vehicles, backend_signals = self._resolve_state(roads, vehicles, signals)
        if self.console_fallback or self.pygame is None:
            self._draw_console(roads, real_vehicles, backend_signals)
            return

        if not self._events_processed_since_draw:
            self.handle_events()

        dt = self.clock.tick(60) / 1000.0 if self.clock is not None else 1.0 / 60.0
        dt = max(0.001, min(dt, 0.05))

        if self._is_presentation_scene(real_vehicles, backend_signals):
            self._draw_presentation_scene(real_vehicles, backend_signals)
            self.pygame.display.flip()
            self._events_processed_since_draw = False
            return

        if not real_vehicles and not self.ui_vehicles:
            self._spawn_initial_flow()
        if not self.paused:
            self._update_ui_traffic(dt)

        self.clear()
        self.draw_roads()
        self.draw_lanes()
        self.draw_intersection()
        self.draw_signals(backend_signals)
        self.draw_vehicles(real_vehicles)
        self.draw_stats_panel(real_vehicles)
        self.draw_controls_panel()
        self.pygame.display.flip()
        self._events_processed_since_draw = False

    def handle_events(self) -> bool:
        """Process UI input and emit one-frame UI events."""
        if not self.initialized or self.pygame is None:
            return True

        if not self._events_processed_since_draw:
            self.ui_events = self._new_event_packet()
        self._events_processed_since_draw = True

        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                self.running = False
                return False

            if event.type == self.pygame.VIDEORESIZE:
                self.width = max(720, int(event.w))
                self.height = max(480, int(event.h))
                self.camera.width = self.width
                self.camera.height = self.height
                self.screen = self.pygame.display.set_mode((self.width, self.height), self.pygame.RESIZABLE)

            if event.type == self.pygame.MOUSEWHEEL:
                self.camera.zoom(1.1 if event.y > 0 else 1 / 1.1)

            if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(event.pos)

            if event.type == self.pygame.KEYDOWN:
                self.keys_down.add(event.key)
                if not self._handle_keydown(event.key):
                    return False

            if event.type == self.pygame.KEYUP:
                self.keys_down.discard(event.key)

        self._handle_camera_pan()
        return True

    def clear(self) -> None:
        self.screen.fill(self.colors["background"])

    def draw_roads(self) -> None:
        half = self.road_length * 0.5
        h_rect = self.pygame.Rect(self.camera.rect_to_screen((-half, -self.road_width * 0.5, self.road_length, self.road_width)))
        v_rect = self.pygame.Rect(self.camera.rect_to_screen((-self.road_width * 0.5, -half, self.road_width, self.road_length)))
        self.pygame.draw.rect(self.screen, self.colors["road_edge"], h_rect.inflate(8, 8), border_radius=4)
        self.pygame.draw.rect(self.screen, self.colors["road_edge"], v_rect.inflate(8, 8), border_radius=4)
        self.pygame.draw.rect(self.screen, self.colors["road"], h_rect, border_radius=2)
        self.pygame.draw.rect(self.screen, self.colors["road"], v_rect, border_radius=2)

    def draw_lanes(self) -> None:
        for lane_name, lane in self._lane_geometry.items():
            self._draw_dashed_line(lane["start"], lane["end"], self.colors["lane"], 20, 15, 2)
            self._draw_lane_arrow(lane)
            if self.debug:
                point = self._point_on_lane(lane, 0.08)
                label = self.small_font.render(f"{lane_name}: {lane['move']}", True, self.colors["muted"])
                self.screen.blit(label, self.camera.world_to_screen(*point))

    def draw_intersection(self) -> None:
        rect = self._intersection_world_rect()
        screen_rect = self.pygame.Rect(self.camera.rect_to_screen(rect))
        self.pygame.draw.rect(self.screen, self.colors["intersection_fill"], screen_rect, border_radius=4)
        self.pygame.draw.rect(self.screen, self.colors["intersection"], screen_rect, width=3, border_radius=4)

    def draw_signals(self, backend_signals: Iterable[Any] | None = None) -> None:
        backend_signals = list(backend_signals or [])
        if backend_signals:
            for index, signal in enumerate(backend_signals[:3]):
                state = self.backend_signal_overrides.get(id(signal), str(getattr(signal, "state", "RED")).upper())
                position = self._backend_signal_position(signal, index)
                self._draw_signal(position, state, signal is self.selected_signal)
            return

        for signal in self.signals:
            self._draw_signal((signal["x"], signal["y"]), signal["state"], signal is self.selected_signal)

    def draw_vehicles(self, real_vehicles: Iterable[Any] | None = None) -> None:
        for vehicle in real_vehicles or []:
            self._draw_real_vehicle(vehicle)
        for vehicle in self.ui_vehicles:
            self._draw_ui_vehicle(vehicle)

    def draw_stats_panel(self, real_vehicles: Iterable[Any]) -> None:
        real_vehicles = list(real_vehicles)
        total = len(real_vehicles) + len(self.ui_vehicles)
        in_intersection = sum(1 for vehicle in self.ui_vehicles if vehicle["in_intersection"])
        speeds = [float(getattr(vehicle, "velocity", 0.0) or 0.0) for vehicle in real_vehicles]
        speeds.extend(float(vehicle["speed"]) for vehicle in self.ui_vehicles)
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        fps = self.clock.get_fps() if self.clock is not None else 0.0

        lines = [
            f"Vehicles: {total}",
            f"In Intersection: {in_intersection}",
            f"Avg Speed: {avg_speed:.1f}",
            f"FPS: {fps:.0f}",
        ]
        if self.place_signal_mode:
            lines.append("Signal placement")
        if self.paused:
            lines.append("Paused")

        self._draw_panel((12, 12, 190, 30 + len(lines) * 18))
        for index, line in enumerate(lines):
            text = self.small_font.render(line, True, self.colors["text"])
            self.screen.blit(text, (24, 24 + index * 18))

    def draw_controls_panel(self) -> None:
        controls = [
            "[SPACE] Pause",
            "[V] Spawn",
            "[T] Place Light",
            "[DEL] Remove Selected",
            "[1/2/3] Signal",
            "[D] Debug",
            "[ESC] Exit",
        ]
        height = 58
        self._draw_panel((12, self.height - height - 12, self.width - 24, height))
        x = 24
        y = self.height - height + 7
        for control in controls:
            text = self.small_font.render(control, True, self.colors["text"])
            self.screen.blit(text, (x, y))
            x += text.get_width() + 22
            if x > self.width - 170:
                x = 24
                y += 20

    def update(self) -> None:
        """Compatibility hook for existing controller code."""
        return None

    def shutdown(self) -> None:
        if self.pygame is not None:
            self.pygame.quit()
        self.initialized = False

    def _is_presentation_scene(self, vehicles: Iterable[Any], signals: Iterable[Any]) -> bool:
        return bool(list(signals)) and any(hasattr(vehicle, "render_direction") for vehicle in vehicles)

    def _draw_presentation_scene(self, vehicles: Iterable[Any], signals: Iterable[Any]) -> None:
        self.screen.fill((45, 95, 68))
        self._draw_city_blocks()
        self._draw_presentation_roads()
        self._draw_presentation_lanes()
        self._draw_presentation_signals(signals)

        for vehicle in vehicles:
            self._draw_presentation_vehicle(vehicle)

        self._draw_presentation_panel(vehicles, signals)

    def _draw_city_blocks(self) -> None:
        blocks = [
            (44, 54, 250, 250),
            (506, 54, 250, 250),
            (44, 506, 250, 250),
            (506, 506, 250, 250),
        ]
        for rect_data in blocks:
            rect = self.pygame.Rect(rect_data)
            self.pygame.draw.rect(self.screen, (64, 121, 86), rect, border_radius=8)
            self.pygame.draw.rect(self.screen, (86, 143, 104), rect, width=2, border_radius=8)

    def _draw_presentation_roads(self) -> None:
        road = (48, 52, 55)
        edge = (31, 34, 36)
        h_edge = self.pygame.Rect(0, 336, WIDTH, 128)
        v_edge = self.pygame.Rect(336, 0, 128, HEIGHT)
        h_road = self.pygame.Rect(0, 350, WIDTH, 100)
        v_road = self.pygame.Rect(350, 0, 100, HEIGHT)

        self.pygame.draw.rect(self.screen, edge, h_edge)
        self.pygame.draw.rect(self.screen, edge, v_edge)
        self.pygame.draw.rect(self.screen, road, h_road)
        self.pygame.draw.rect(self.screen, road, v_road)
        self.pygame.draw.rect(self.screen, (62, 66, 69), (350, 350, 100, 100))
        self.pygame.draw.rect(self.screen, (92, 98, 96), (350, 350, 100, 100), width=2)

    def _draw_presentation_lanes(self) -> None:
        white = (238, 240, 234)
        yellow = (245, 203, 80)
        self.pygame.draw.line(self.screen, yellow, (0, 400), (STOP_LINE - 10, 400), 3)
        self.pygame.draw.line(self.screen, yellow, (462, 400), (800, 400), 3)
        self.pygame.draw.line(self.screen, yellow, (400, 0), (400, STOP_LINE - 10), 3)
        self.pygame.draw.line(self.screen, yellow, (400, 462), (400, 800), 3)

        self.pygame.draw.line(self.screen, (180, 185, 181), (INTERSECTION_START, INTERSECTION_START), (INTERSECTION_START, INTERSECTION_END), 2)
        self.pygame.draw.line(self.screen, (180, 185, 181), (INTERSECTION_START, INTERSECTION_START), (INTERSECTION_END, INTERSECTION_START), 2)
        self.pygame.draw.line(self.screen, white, (STOP_LINE, 354), (STOP_LINE, 446), 6)
        self.pygame.draw.line(self.screen, white, (354, STOP_LINE), (446, STOP_LINE), 6)
        self._draw_crosswalk((STOP_LINE + 8, 350), "H")
        self._draw_crosswalk((350, STOP_LINE + 8), "V")
        self._draw_arrow((120, 382), "E")
        self._draw_arrow((382, 120), "S")
        self._draw_small_label("West to East", (92, 456))
        self._draw_small_label("North to South", (456, 92))
        self._draw_small_label("Stop before intersection", (188, 314))

    def _draw_crosswalk(self, pos: tuple[int, int], orientation: str) -> None:
        x, y = pos
        color = (222, 225, 220)
        for offset in range(0, 84, 14):
            if orientation == "H":
                self.pygame.draw.rect(self.screen, color, (x + offset, y + 4, 7, 92))
            else:
                self.pygame.draw.rect(self.screen, color, (x + 4, y + offset, 92, 7))

    def _draw_arrow(self, pos: tuple[int, int], direction: str) -> None:
        x, y = pos
        color = (218, 224, 219)
        if direction == "E":
            points = [(x + 28, y), (x + 10, y - 10), (x + 10, y - 4), (x - 22, y - 4), (x - 22, y + 4), (x + 10, y + 4), (x + 10, y + 10)]
        else:
            points = [(x, y + 28), (x - 10, y + 10), (x - 4, y + 10), (x - 4, y - 22), (x + 4, y - 22), (x + 4, y + 10), (x + 10, y + 10)]
        self.pygame.draw.polygon(self.screen, color, points)

    def _draw_presentation_signals(self, signals: Iterable[Any]) -> None:
        for signal in signals:
            group = getattr(signal, "render_group", "HORIZONTAL")
            if group == "VERTICAL":
                self._draw_traffic_light((464, 300), signal, "North-South")
            else:
                self._draw_traffic_light((292, 420), signal, "West-East")

    def _draw_traffic_light(self, pos: tuple[int, int], signal: Any, label: str) -> None:
        x, y = pos
        state = str(getattr(signal, "state", "RED")).upper()
        lamp_colors = {
            "RED": (238, 61, 57),
            "YELLOW": (248, 205, 75),
            "GREEN": (72, 202, 106),
        }
        body = self.pygame.Rect(x, y, 42, 94)
        self.pygame.draw.rect(self.screen, (9, 10, 11), body.move(3, 4), border_radius=9)
        self.pygame.draw.rect(self.screen, (22, 24, 25), body, border_radius=9)
        self.pygame.draw.rect(self.screen, (4, 5, 6), body, width=2, border_radius=9)
        for index, lamp in enumerate(("RED", "YELLOW", "GREEN")):
            color = lamp_colors[lamp] if state == lamp else (70, 74, 74)
            center = (x + 21, y + 18 + index * 29)
            if state == lamp:
                self.pygame.draw.circle(self.screen, (*color, 90), center, 17)
            self.pygame.draw.circle(self.screen, color, center, 10)
            self.pygame.draw.circle(self.screen, (4, 5, 6), center, 10, 2)
        self._draw_small_label(label, (x - 12, y + 100))

    def _draw_presentation_vehicle(self, vehicle: Any) -> None:
        direction = getattr(vehicle, "render_direction", "WEST_EAST")
        position = int(getattr(vehicle, "position", 0.0) or 0.0)
        velocity = float(getattr(vehicle, "velocity", 0.0) or 0.0)
        stopped = velocity < 0.1
        color = (233, 77, 68) if stopped else (64, 156, 229)

        if direction == "NORTH_SOUTH":
            rect = self.pygame.Rect(376, position - CAR_LENGTH, CAR_WIDTH, CAR_LENGTH)
        elif direction == "EAST_WEST":
            rect = self.pygame.Rect(WIDTH - position, 416, CAR_LENGTH, CAR_WIDTH)
        elif direction == "SOUTH_NORTH":
            rect = self.pygame.Rect(416, HEIGHT - position, CAR_WIDTH, CAR_LENGTH)
        else:
            rect = self.pygame.Rect(position - CAR_LENGTH, 376, CAR_LENGTH, CAR_WIDTH)

        self.pygame.draw.rect(self.screen, (7, 8, 9), rect.move(4, 5), border_radius=7)
        self.pygame.draw.rect(self.screen, color, rect, border_radius=7)
        self.pygame.draw.rect(self.screen, (188, 226, 246), rect.inflate(-18, -12), border_radius=4)
        self.pygame.draw.rect(self.screen, (8, 10, 11), rect, width=2, border_radius=7)

    def _draw_presentation_panel(self, vehicles: Iterable[Any], signals: Iterable[Any]) -> None:
        signals = list(signals)
        vehicles = list(vehicles)
        rect = self.pygame.Rect(18, 18, 278, 134)
        panel = self.pygame.Surface(rect.size, self.pygame.SRCALPHA)
        panel.fill((16, 20, 22, 220))
        self.screen.blit(panel, rect.topleft)
        self.pygame.draw.rect(self.screen, (86, 96, 96), rect, width=1, border_radius=8)

        self._draw_text("FlowSync Intersection", (34, 32), self.font, (245, 247, 242))
        self._draw_text("Coordinated two-signal demo", (34, 57), self.small_font, (178, 187, 182))
        y = 84
        for signal in signals:
            group = getattr(signal, "render_group", "HORIZONTAL").title()
            state = str(getattr(signal, "state", "RED")).upper()
            timer = float(getattr(signal, "timer", 0.0) or 0.0)
            self._draw_text(f"{group}: {state}  {timer:04.1f}s", (34, y), self.small_font, self._state_color(state))
            y += 20
        stopped = sum(1 for vehicle in vehicles if float(getattr(vehicle, "velocity", 0.0) or 0.0) < 0.1)
        self._draw_text(f"Vehicles: {len(vehicles)}   Stopped: {stopped}", (34, y), self.small_font, (218, 224, 219))

    def _draw_small_label(self, text: str, pos: tuple[int, int]) -> None:
        self._draw_text(text, pos, self.small_font, (236, 239, 235))

    def _draw_text(self, text: str, pos: tuple[int, int], font: Any, color: tuple[int, int, int]) -> None:
        surface = font.render(text, True, color)
        self.screen.blit(surface, pos)

    def _state_color(self, state: str) -> tuple[int, int, int]:
        return {
            "RED": (255, 111, 103),
            "YELLOW": (255, 220, 105),
            "GREEN": (108, 230, 137),
        }.get(state, (236, 239, 235))

    def _handle_keydown(self, key: int) -> bool:
        if key == self.pygame.K_ESCAPE:
            self.running = False
            return False
        if key == self.pygame.K_SPACE:
            self.paused = not self.paused
        elif key == self.pygame.K_d:
            self.debug = not self.debug
        elif key == self.pygame.K_t:
            self.place_signal_mode = not self.place_signal_mode
        elif key == self.pygame.K_v:
            self._try_spawn_random_vehicle()
            self.ui_events["spawn_vehicle"] = True
        elif key in (self.pygame.K_DELETE, self.pygame.K_BACKSPACE):
            self._remove_selected()
        elif key in (self.pygame.K_1, self.pygame.K_2, self.pygame.K_3):
            state = {self.pygame.K_1: "RED", self.pygame.K_2: "YELLOW", self.pygame.K_3: "GREEN"}[key]
            self._set_selected_signal_state(state)
        elif key == self.pygame.K_f:
            self.camera.focus_intersection()
        elif key in (self.pygame.K_EQUALS, self.pygame.K_PLUS):
            self.camera.zoom(1.12)
        elif key == self.pygame.K_MINUS:
            self.camera.zoom(1 / 1.12)
        return True

    def _handle_camera_pan(self) -> None:
        speed = 18.0
        if self.pygame.K_LEFT in self.keys_down:
            self.camera.pan(-speed, 0)
        if self.pygame.K_RIGHT in self.keys_down:
            self.camera.pan(speed, 0)
        if self.pygame.K_UP in self.keys_down:
            self.camera.pan(0, -speed)
        if self.pygame.K_DOWN in self.keys_down:
            self.camera.pan(0, speed)

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        world = self.camera.screen_to_world(*pos)
        backend_signal = self._backend_signal_at_world(world)
        if backend_signal is not None:
            self.selected_signal = backend_signal
            self.place_signal_mode = False
            return

        signal = self._signal_at_world(world)
        if signal is not None:
            self.selected_signal = signal
            self.place_signal_mode = False
            return

        if self.place_signal_mode or len(self.signals) < 3:
            if len(self.signals) < 3:
                self._place_signal(world)
            self.place_signal_mode = False
            return

        self._try_spawn_vehicle_at(world)

    def _resolve_state(
        self,
        roads: Iterable[Any] | None,
        vehicles: Iterable[Any] | None,
        signals: Iterable[Any] | None,
    ) -> tuple[list[Any], list[Any], list[Any]]:
        manager = self.traffic_manager
        if roads is None and manager is not None:
            getter = getattr(manager, "get_roads", None)
            roads = cast(list[Any], getter() if callable(getter) else getattr(manager, "roads", []))
        if vehicles is None and manager is not None:
            getter = getattr(manager, "get_vehicles", None)
            vehicles = cast(list[Any], getter() if callable(getter) else getattr(manager, "vehicles", []))
        if signals is None and manager is not None:
            getter = getattr(manager, "get_signals", None)
            signals = cast(list[Any], getter() if callable(getter) else getattr(manager, "signals", []))
        return list(roads or []), list(vehicles or []), list(signals or [])

    def _build_lane_geometry(self) -> dict[str, dict[str, Any]]:
        half = self.road_length * 0.5
        off = self.lane_offset
        return {
            "top_lane": {
                "start": (-half, -off),
                "end": (half, -off),
                "move": "RIGHT",
                "spawn": "W",
                "angle": 0.0,
                "axis": "x",
                "sign": 1,
            },
            "bottom_lane": {
                "start": (half, off),
                "end": (-half, off),
                "move": "LEFT",
                "spawn": "E",
                "angle": math.pi,
                "axis": "x",
                "sign": -1,
            },
            "left_lane": {
                "start": (-off, -half),
                "end": (-off, half),
                "move": "DOWN",
                "spawn": "N",
                "angle": math.pi / 2,
                "axis": "y",
                "sign": 1,
            },
            "right_lane": {
                "start": (off, half),
                "end": (off, -half),
                "move": "UP",
                "spawn": "S",
                "angle": -math.pi / 2,
                "axis": "y",
                "sign": -1,
            },
        }

    def _direction_to_lane(self, direction: str) -> str:
        return {
            "N": "left_lane",
            "S": "right_lane",
            "E": "bottom_lane",
            "W": "top_lane",
        }[direction]

    def _lane_to_direction(self, lane_name: str) -> str:
        return self._lane_geometry[lane_name]["spawn"]

    def _try_spawn_random_vehicle(self) -> bool:
        for _ in range(8):
            direction = random.choice(self.SPAWN_DIRECTIONS)
            turn = random.choice(self.TURNS)
            if self._can_spawn(direction):
                self._spawn_vehicle(direction, turn)
                return True
        return False

    def _try_spawn_vehicle_at(self, world: tuple[float, float]) -> None:
        lane_name, progress = self._nearest_lane(world)
        direction = self._lane_to_direction(lane_name)
        if self._safe_gap_on_lane(lane_name, progress, self.spawn_gap):
            self._spawn_vehicle(direction, random.choice(self.TURNS), progress=progress)
            self.ui_events["spawn_vehicle"] = True

    def _spawn_vehicle(self, direction: str, turn: str, progress: float = 0.0) -> dict[str, Any]:
        lane_name = self._direction_to_lane(direction)
        lane = self._lane_geometry[lane_name]
        x, y = self._point_on_lane(lane, progress)
        vehicle = {
            "id": self._next_vehicle_id,
            "x": x,
            "y": y,
            "direction": direction,
            "lane_id": lane_name,
            "speed": random.uniform(self.base_speed * 0.72, self.base_speed * 1.05),
            "target_speed": random.uniform(self.base_speed * 0.85, self.base_speed * 1.1),
            "target_turn": turn,
            "state": "MOVING",
            "progress": progress,
            "in_intersection": False,
            "has_turned": False,
            "slowing": False,
        }
        self._next_vehicle_id += 1
        self.ui_vehicles.append(vehicle)
        return vehicle

    def _spawn_initial_flow(self) -> None:
        for direction in self.SPAWN_DIRECTIONS:
            for progress in (0.02, 0.18):
                if self._can_spawn(direction):
                    self._spawn_vehicle(direction, random.choice(self.TURNS), progress)

    def _can_spawn(self, direction: str) -> bool:
        lane_name = self._direction_to_lane(direction)
        return self._safe_gap_on_lane(lane_name, 0.0, self.spawn_gap)

    def _safe_gap_on_lane(self, lane_name: str, progress: float, gap: float) -> bool:
        lane = self._lane_geometry[lane_name]
        for vehicle in self.ui_vehicles:
            if vehicle["lane_id"] != lane_name:
                continue
            distance = abs(float(vehicle["progress"]) - progress) * self._lane_length(lane)
            if distance < gap:
                return False
        return True

    def _update_ui_traffic(self, dt: float) -> None:
        lanes = self._vehicles_by_lane()
        intersection_count = sum(1 for vehicle in self.ui_vehicles if vehicle["in_intersection"])

        for lane_name, lane_vehicles in lanes.items():
            lane = self._lane_geometry[lane_name]
            lane_vehicles.sort(key=lambda vehicle: float(vehicle["progress"]), reverse=True)
            front_progress = 2.0
            for vehicle in lane_vehicles:
                was_in_intersection = bool(vehicle["in_intersection"])
                target_speed = float(vehicle["target_speed"])
                desired_speed = target_speed
                distance_to_front = (front_progress - float(vehicle["progress"])) * self._lane_length(lane)
                distance_to_intersection = self._distance_to_intersection(vehicle)

                if 0 <= distance_to_front < self.min_gap:
                    desired_speed = 0.0
                elif self._must_stop_before_intersection(vehicle, distance_to_intersection, intersection_count):
                    desired_speed = 0.0
                elif 0 < distance_to_intersection < 90.0:
                    desired_speed = min(desired_speed, max(24.0, target_speed * distance_to_intersection / 90.0))

                self._apply_speed(vehicle, desired_speed, dt)
                if vehicle["state"] == "MOVING":
                    vehicle["progress"] += (vehicle["speed"] * dt) / max(self._lane_length(lane), 1.0)

                vehicle["x"], vehicle["y"] = self._point_on_lane(lane, float(vehicle["progress"]))
                vehicle["in_intersection"] = self._point_in_intersection((vehicle["x"], vehicle["y"]))

                if vehicle["in_intersection"] and not was_in_intersection:
                    intersection_count += 1

                if vehicle["in_intersection"] and not vehicle["has_turned"]:
                    self._apply_turn(vehicle)
                    lane = self._lane_geometry[vehicle["lane_id"]]

                front_progress = float(vehicle["progress"])

        self.ui_vehicles = [vehicle for vehicle in self.ui_vehicles if not self._vehicle_exited(vehicle)]

    def _vehicles_by_lane(self) -> dict[str, list[dict[str, Any]]]:
        lanes = {lane_name: [] for lane_name in self._lane_geometry}
        for vehicle in self.ui_vehicles:
            lanes.setdefault(vehicle["lane_id"], []).append(vehicle)
        return lanes

    def _must_stop_before_intersection(self, vehicle: dict[str, Any], distance: float, intersection_count: int) -> bool:
        if vehicle["in_intersection"]:
            return False
        if distance < 0 or distance > 46.0:
            return False
        if self._blocking_signal_for_vehicle(vehicle):
            return True
        return intersection_count >= self.max_intersection_vehicles

    def _blocking_signal_for_vehicle(self, vehicle: dict[str, Any]) -> bool:
        for signal in self.signals:
            if signal["state"] != "RED":
                continue
            if math.hypot(vehicle["x"] - signal["x"], vehicle["y"] - signal["y"]) < 82.0:
                return True
        return False

    def _apply_speed(self, vehicle: dict[str, Any], desired_speed: float, dt: float) -> None:
        current = float(vehicle["speed"])
        if desired_speed < current:
            current = max(desired_speed, current - 260.0 * dt)
        else:
            current = min(desired_speed, current + 160.0 * dt)
        vehicle["speed"] = current
        vehicle["state"] = "STOPPED" if current < 2.0 else "MOVING"
        vehicle["slowing"] = 2.0 <= current < self.base_speed * 0.45

    def _apply_turn(self, vehicle: dict[str, Any]) -> None:
        turn = vehicle["target_turn"]
        if turn == "STRAIGHT":
            vehicle["has_turned"] = True
            return

        lane_order = ["top_lane", "left_lane", "bottom_lane", "right_lane"]
        current_index = lane_order.index(vehicle["lane_id"])
        next_index = (current_index + 1) % 4 if turn == "LEFT" else (current_index - 1) % 4
        next_lane_name = lane_order[next_index]
        next_lane = self._lane_geometry[next_lane_name]
        vehicle["lane_id"] = next_lane_name
        vehicle["direction"] = self._lane_to_direction(next_lane_name)
        vehicle["progress"] = self._progress_near_intersection(next_lane)
        vehicle["x"], vehicle["y"] = self._point_on_lane(next_lane, float(vehicle["progress"]))
        vehicle["has_turned"] = True

    def _distance_to_intersection(self, vehicle: dict[str, Any]) -> float:
        lane = self._lane_geometry[vehicle["lane_id"]]
        progress_at_center = self._progress_near_intersection(lane)
        return (progress_at_center - float(vehicle["progress"])) * self._lane_length(lane)

    def _progress_near_intersection(self, lane: dict[str, Any]) -> float:
        start = lane["start"]
        end = lane["end"]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        denom = max(1.0, dx * dx + dy * dy)
        return max(0.0, min(1.0, ((0.0 - start[0]) * dx + (0.0 - start[1]) * dy) / denom))

    def _vehicle_exited(self, vehicle: dict[str, Any]) -> bool:
        if float(vehicle["progress"]) > 1.02:
            return True
        sx, sy = self.camera.world_to_screen(vehicle["x"], vehicle["y"])
        margin = 140
        return sx < -margin or sx > self.width + margin or sy < -margin or sy > self.height + margin

    def _draw_ui_vehicle(self, vehicle: dict[str, Any]) -> None:
        if vehicle["state"] == "STOPPED":
            color = self.colors["stopped"]
        elif vehicle["slowing"]:
            color = self.colors["slow"]
        else:
            color = self.colors["moving"]
        center = self.camera.world_to_screen(vehicle["x"], vehicle["y"])
        radius = max(4, int(self.vehicle_radius * self.camera.scale))
        self.pygame.draw.circle(self.screen, color, center, radius)
        self.pygame.draw.circle(self.screen, (9, 11, 11), center, radius, 2)
        if self.debug:
            text = self.small_font.render(vehicle["target_turn"][0], True, self.colors["text"])
            self.screen.blit(text, (center[0] + radius + 2, center[1] - 7))

    def _draw_real_vehicle(self, vehicle: Any) -> None:
        lane = self._lane_geometry["top_lane"]
        lane_obj = getattr(vehicle, "lane", None)
        position = float(getattr(vehicle, "position", 0.0) or 0.0)
        length = float(getattr(lane_obj, "length", self.road_length) or self.road_length)
        progress = max(0.0, min(1.0, position / max(length, 1.0)))
        x, y = self._point_on_lane(lane, progress)
        speed = float(getattr(vehicle, "velocity", 0.0) or 0.0)
        color = self.colors["stopped"] if speed < 0.1 else self.colors["real_vehicle"]
        center = self.camera.world_to_screen(x, y)
        radius = max(4, int(self.vehicle_radius * self.camera.scale))
        self.pygame.draw.circle(self.screen, color, center, radius)
        self.pygame.draw.circle(self.screen, (8, 10, 10), center, radius, 2)

    def _place_signal(self, world: tuple[float, float]) -> None:
        if len(self.signals) >= 3:
            return
        signal = {
            "id": self._next_signal_id,
            "x": world[0],
            "y": world[1],
            "state": "RED",
        }
        self._next_signal_id += 1
        self.signals.append(signal)
        self.selected_signal = signal
        self.ui_events["signal_change"] = {"signal": signal, "state": signal["state"]}

    def _set_selected_signal_state(self, state: str) -> None:
        if isinstance(self.selected_signal, dict):
            self.selected_signal["state"] = state
            self.ui_events["signal_change"] = {"signal": self.selected_signal, "state": state}
        elif self.selected_signal is not None:
            self.backend_signal_overrides[id(self.selected_signal)] = state
            self.ui_events["signal_change"] = {"signal": self.selected_signal, "state": state}

    def _remove_selected(self) -> None:
        if isinstance(self.selected_signal, dict) and self.selected_signal in self.signals:
            self.signals.remove(self.selected_signal)
            self.selected_signal = None
            self.ui_events["remove_signal"] = True
            return
        if self.ui_vehicles:
            target = min(self.ui_vehicles, key=lambda vehicle: math.hypot(vehicle["x"], vehicle["y"]))
            self.ui_vehicles.remove(target)
            self.ui_events["remove_vehicle"] = True

    def _signal_at_world(self, world: tuple[float, float]) -> dict[str, Any] | None:
        for signal in self.signals:
            if math.hypot(world[0] - signal["x"], world[1] - signal["y"]) <= 18.0:
                return signal
        return None

    def _backend_signal_at_world(self, world: tuple[float, float]) -> Any | None:
        roads, vehicles, signals = self._resolve_state(None, None, None)
        del roads, vehicles
        for index, signal in enumerate(signals[:3]):
            sx, sy = self._backend_signal_position(signal, index)
            if math.hypot(world[0] - sx, world[1] - sy) <= 22.0:
                return signal
        return None

    def _backend_signal_position(self, signal: Any, index: int) -> tuple[float, float]:
        raw = getattr(signal, "position", None)
        if isinstance(raw, tuple) and len(raw) >= 2:
            progress = max(0.0, min(1.0, float(raw[0]) / max(self.road_length, 1.0)))
            x, y = self._point_on_lane(self._lane_geometry["top_lane"], progress)
            return x, y - self.lane_offset * 1.15
        fallback = [(-54.0, -54.0), (54.0, -54.0), (54.0, 54.0)]
        return fallback[index % len(fallback)]

    def _draw_signal(self, world: tuple[float, float], state: str, selected: bool) -> None:
        color = {"RED": self.colors["red"], "YELLOW": self.colors["yellow"], "GREEN": self.colors["green"]}.get(state, self.colors["off"])
        center = self.camera.world_to_screen(*world)
        radius = max(8, int(10 * self.camera.scale))
        glow_radius = radius * 2
        glow = self.pygame.Surface((glow_radius * 2, glow_radius * 2), self.pygame.SRCALPHA)
        self.pygame.draw.circle(glow, (*color, 60), (glow_radius, glow_radius), glow_radius)
        self.screen.blit(glow, (center[0] - glow_radius, center[1] - glow_radius))
        self.pygame.draw.circle(self.screen, self.colors["signal_body"], center, radius + 5)
        self.pygame.draw.circle(self.screen, color, center, radius)
        self.pygame.draw.circle(self.screen, (7, 8, 8), center, radius + 5, 2)
        if selected:
            self.pygame.draw.circle(self.screen, self.colors["selection"], center, radius + 10, 3)

    def _nearest_lane(self, point: tuple[float, float]) -> tuple[str, float]:
        best_lane = "top_lane"
        best_progress = 0.0
        best_distance = float("inf")
        for lane_name, lane in self._lane_geometry.items():
            distance, progress = self._distance_to_lane(point, lane)
            if distance < best_distance:
                best_lane = lane_name
                best_progress = progress
                best_distance = distance
        return best_lane, best_progress

    def _distance_to_lane(self, point: tuple[float, float], lane: dict[str, Any]) -> tuple[float, float]:
        px, py = point
        sx, sy = lane["start"]
        ex, ey = lane["end"]
        dx = ex - sx
        dy = ey - sy
        denom = max(1.0, dx * dx + dy * dy)
        progress = max(0.0, min(0.98, ((px - sx) * dx + (py - sy) * dy) / denom))
        lx, ly = self._point_on_lane(lane, progress)
        return math.hypot(px - lx, py - ly), progress

    def _point_on_lane(self, lane: dict[str, Any], progress: float) -> tuple[float, float]:
        sx, sy = lane["start"]
        ex, ey = lane["end"]
        return sx + (ex - sx) * progress, sy + (ey - sy) * progress

    def _lane_length(self, lane: dict[str, Any]) -> float:
        return math.dist(lane["start"], lane["end"])

    def _point_in_intersection(self, point: tuple[float, float]) -> bool:
        x, y, w, h = self._intersection_world_rect()
        return x <= point[0] <= x + w and y <= point[1] <= y + h

    def _intersection_world_rect(self) -> tuple[float, float, float, float]:
        size = self.intersection_size
        return -size * 0.5, -size * 0.5, size, size

    def _draw_lane_arrow(self, lane: dict[str, Any]) -> None:
        x, y = self._point_on_lane(lane, 0.28)
        angle = lane["angle"]
        length = 22.0
        tip = (x + math.cos(angle) * length, y + math.sin(angle) * length)
        tail = (x - math.cos(angle) * length * 0.45, y - math.sin(angle) * length * 0.45)
        left = (tip[0] - math.cos(angle - 0.7) * 9.0, tip[1] - math.sin(angle - 0.7) * 9.0)
        right = (tip[0] - math.cos(angle + 0.7) * 9.0, tip[1] - math.sin(angle + 0.7) * 9.0)
        self._draw_world_line(tail, tip, self.colors["lane_dim"], 2)
        self._draw_world_line(tip, left, self.colors["lane_dim"], 2)
        self._draw_world_line(tip, right, self.colors["lane_dim"], 2)

    def _draw_dashed_line(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int],
        dash: int,
        gap: int,
        width: int,
    ) -> None:
        sx, sy = self.camera.world_to_screen(*start)
        ex, ey = self.camera.world_to_screen(*end)
        total = math.hypot(ex - sx, ey - sy)
        if total <= 1:
            return
        ux = (ex - sx) / total
        uy = (ey - sy) / total
        distance = 0.0
        while distance < total:
            end_distance = min(total, distance + dash)
            p0 = (int(sx + ux * distance), int(sy + uy * distance))
            p1 = (int(sx + ux * end_distance), int(sy + uy * end_distance))
            self.pygame.draw.line(self.screen, color, p0, p1, width)
            distance += dash + gap

    def _draw_world_line(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int],
        width: int,
    ) -> None:
        self.pygame.draw.line(self.screen, color, self.camera.world_to_screen(*start), self.camera.world_to_screen(*end), width)

    def _draw_panel(self, rect_data: tuple[int, int, int, int]) -> None:
        rect = self.pygame.Rect(rect_data)
        surface = self.pygame.Surface(rect.size, self.pygame.SRCALPHA)
        surface.fill((*self.colors["panel"], 220))
        self.screen.blit(surface, rect.topleft)
        self.pygame.draw.rect(self.screen, self.colors["panel_border"], rect, width=1, border_radius=6)

    def _new_event_packet(self) -> dict[str, Any]:
        return {
            "spawn_vehicle": False,
            "remove_vehicle": False,
            "add_lane": False,
            "remove_lane": False,
            "signal_change": None,
            "remove_signal": False,
        }

    def _draw_console(self, roads: list[Any], vehicles: list[Any], signals: list[Any]) -> None:
        print(f"[Renderer] roads={len(roads)} vehicles={len(vehicles) + len(self.ui_vehicles)} signals={len(signals) or len(self.signals)}")
