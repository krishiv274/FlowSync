"""MovSim-style pygame renderer for the FlowSync traffic simulation.

The renderer is intentionally a read-only visualization layer. It builds a
screen layout from public road, lane, vehicle, and signal state without
mutating simulation objects or making driving decisions.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class LaneView:
    lane: Any
    index: int
    centerline: tuple[float, float, float, float]
    orientation: str
    direction: int
    road_id: Any
    length: float


@dataclass(frozen=True)
class RoadView:
    road: Any
    index: int
    rect: tuple[float, float, float, float]
    orientation: str
    lanes: tuple[LaneView, ...]
    length: float


class Camera:
    """World-to-screen transform with offset and scalable zoom."""

    def __init__(self, width: int, height: int, scale: float = 1.0) -> None:
        self.width = width
        self.height = height
        self.offset = [0.0, 0.0]
        self.scale = scale
        self.min_scale = 0.35
        self.max_scale = 3.0

    def world_to_screen(self, x: float, y: float) -> tuple[int, int]:
        sx = (x - self.offset[0]) * self.scale + self.width * 0.5
        sy = (y - self.offset[1]) * self.scale + self.height * 0.5
        return int(round(sx)), int(round(sy))

    def world_rect_to_screen(self, rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
        x, y, w, h = rect
        x0, y0 = self.world_to_screen(x, y)
        x1, y1 = self.world_to_screen(x + w, y + h)
        left = min(x0, x1)
        top = min(y0, y1)
        return left, top, abs(x1 - x0), abs(y1 - y0)

    def pan(self, dx: float, dy: float) -> None:
        self.offset[0] += dx / max(self.scale, 0.001)
        self.offset[1] += dy / max(self.scale, 0.001)

    def zoom(self, factor: float) -> None:
        self.scale = max(self.min_scale, min(self.max_scale, self.scale * factor))

    def fit_bounds(self, bounds: tuple[float, float, float, float], padding: float = 80.0) -> None:
        min_x, min_y, max_x, max_y = bounds
        span_x = max(1.0, max_x - min_x)
        span_y = max(1.0, max_y - min_y)
        usable_w = max(1.0, self.width - padding * 2.0)
        usable_h = max(1.0, self.height - padding * 2.0)
        self.scale = max(self.min_scale, min(self.max_scale, min(usable_w / span_x, usable_h / span_y)))
        self.offset = [min_x + span_x * 0.5, min_y + span_y * 0.5]


class Renderer:
    """Render roads, lanes, intersections, signals, vehicles, and light UI."""

    def __init__(
        self,
        traffic_manager: Any | None = None,
        width: int = 1200,
        height: int = 800,
        title: str = "FlowSync Traffic Simulation",
    ) -> None:
        self.traffic_manager = traffic_manager
        self.width = width
        self.height = height
        self.title = title

        self.pygame = None
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.initialized = False
        self.console_fallback = False

        self.camera = Camera(width, height, scale=1.0)
        self.frame_count = 0
        self.running = True
        self.paused = False
        self.reset_requested = False
        self.keys_down: set[int] = set()

        self.lane_width = 34.0
        self.road_margin = 12.0
        self.world_padding = 130.0
        self.vehicle_size = (25.0, 13.0)
        self._layout: tuple[RoadView, ...] = ()
        self._lane_lookup: dict[int, LaneView] = {}
        self._track_cache: dict[int, dict[str, Any]] = {}
        self._last_layout_signature: tuple[Any, ...] | None = None
        self._last_frame_time = time.monotonic()
        self._needs_fit = True

        self.colors = {
            "background": (18, 21, 24),
            "grass": (29, 44, 38),
            "asphalt": (46, 50, 54),
            "asphalt_dark": (31, 34, 37),
            "edge": (118, 125, 124),
            "lane": (225, 229, 225),
            "lane_dim": (153, 160, 157),
            "intersection": (55, 58, 61),
            "priority": (74, 79, 82),
            "vehicle": (54, 149, 224),
            "vehicle_alt": (238, 169, 69),
            "brake": (230, 72, 72),
            "stopped": (214, 92, 78),
            "text": (232, 235, 232),
            "muted": (162, 169, 166),
            "signal_body": (21, 23, 24),
            "red": (230, 64, 61),
            "yellow": (245, 197, 66),
            "green": (74, 190, 105),
            "off": (67, 70, 72),
        }

        self.initialize()

    def initialize(self) -> None:
        """Initialize pygame resources, falling back to console-safe mode."""
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

    def handle_events(self) -> bool:
        """Process renderer controls. Returns False when the window should quit."""
        if not self.initialized or self.pygame is None:
            return True

        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                self.running = False
                return False

            if event.type == self.pygame.KEYDOWN:
                self.keys_down.add(event.key)
                if event.key == self.pygame.K_ESCAPE:
                    self.running = False
                    return False
                if event.key == self.pygame.K_SPACE:
                    self.paused = not self.paused
                if event.key == self.pygame.K_r:
                    self.reset_requested = True
                    self._track_cache.clear()
                    self._needs_fit = True
                if event.key in (self.pygame.K_EQUALS, self.pygame.K_PLUS):
                    self.camera.zoom(1.12)
                if event.key == self.pygame.K_MINUS:
                    self.camera.zoom(1 / 1.12)
                if event.key == self.pygame.K_0:
                    self._needs_fit = True

            if event.type == self.pygame.KEYUP:
                self.keys_down.discard(event.key)

            if event.type == self.pygame.VIDEORESIZE:
                self.width = max(720, int(event.w))
                self.height = max(480, int(event.h))
                self.camera.width = self.width
                self.camera.height = self.height
                self.screen = self.pygame.display.set_mode((self.width, self.height), self.pygame.RESIZABLE)
                self._needs_fit = True

            if event.type == self.pygame.MOUSEWHEEL:
                self.camera.zoom(1.1 if event.y > 0 else 1 / 1.1)

        pan = 18.0
        if self.pygame.K_LEFT in self.keys_down or self.pygame.K_a in self.keys_down:
            self.camera.pan(-pan, 0)
        if self.pygame.K_RIGHT in self.keys_down or self.pygame.K_d in self.keys_down:
            self.camera.pan(pan, 0)
        if self.pygame.K_UP in self.keys_down or self.pygame.K_w in self.keys_down:
            self.camera.pan(0, -pan)
        if self.pygame.K_DOWN in self.keys_down or self.pygame.K_s in self.keys_down:
            self.camera.pan(0, pan)

        return True

    def update(self) -> None:
        """Compatibility hook for the existing controller."""
        return None

    def draw(
        self,
        roads: Iterable[Any] | None = None,
        vehicles: Iterable[Any] | None = None,
        signals: Iterable[Any] | None = None,
    ) -> None:
        """Draw one frame using passed collections or the stored traffic manager."""
        if not self.initialized and not self.console_fallback:
            self.initialize()

        roads, vehicles, signals = self._resolve_state(roads, vehicles, signals)
        self._update_layout(roads, signals)
        self.frame_count += 1

        if self.console_fallback or self.pygame is None:
            self._draw_console(roads, vehicles, signals)
            return

        self.handle_events()
        self.clear()
        self.draw_roads()
        self.draw_lanes()
        self.draw_intersections()
        self.draw_signals(signals)
        self.draw_vehicles(vehicles)
        self._draw_hud(len(roads), len(vehicles), len(signals))
        self.pygame.display.flip()
        if self.clock is not None:
            self.clock.tick(60)

    def clear(self) -> None:
        self.screen.fill(self.colors["background"])

    def draw_roads(self) -> None:
        for view in self._layout:
            rect = self.pygame.Rect(self.camera.world_rect_to_screen(view.rect))
            if not self._rect_visible(rect, margin=80):
                continue
            self.pygame.draw.rect(self.screen, self.colors["edge"], rect.inflate(8, 8), border_radius=4)
            self.pygame.draw.rect(self.screen, self.colors["asphalt"], rect, border_radius=3)

    def draw_lanes(self) -> None:
        for view in self._layout:
            for lane_view in view.lanes:
                x0, y0, x1, y1 = lane_view.centerline
                start = self.camera.world_to_screen(x0, y0)
                end = self.camera.world_to_screen(x1, y1)
                self._draw_lane_edge_ticks(lane_view)
                if lane_view.index > 0:
                    self._draw_dashed_line(start, end, self.colors["lane"], dash=18, gap=16, width=2)
                self._draw_direction_arrow(lane_view)

    def draw_intersections(self) -> None:
        if not self._layout:
            return

        for cx, cy, size in self._intersection_zones():
            rect = self._world_rect_center(cx, cy, size, size)
            screen_rect = self.pygame.Rect(self.camera.world_rect_to_screen(rect))
            self.pygame.draw.rect(self.screen, self.colors["intersection"], screen_rect, border_radius=2)

            priority = self.pygame.Rect(self.camera.world_rect_to_screen(self._world_rect_center(cx, cy, size * 0.42, size * 0.42)))
            self.pygame.draw.rect(self.screen, self.colors["priority"], priority, width=2, border_radius=2)

            x0, y0 = self.camera.world_to_screen(cx - size * 0.5, cy - size * 0.5)
            x1, y1 = self.camera.world_to_screen(cx + size * 0.5, cy + size * 0.5)
            self.pygame.draw.line(self.screen, self.colors["lane_dim"], (x0, y0), (x1, y1), 1)
            self.pygame.draw.line(self.screen, self.colors["lane_dim"], (x0, y1), (x1, y0), 1)

    def draw_vehicles(self, vehicles: Iterable[Any] | None = None) -> None:
        vehicles = list(vehicles if vehicles is not None else self._resolve_state()[1])
        now = time.monotonic()
        dt = max(0.001, min(0.1, now - self._last_frame_time))
        self._last_frame_time = now
        smoothing = 1.0 if self.paused else min(1.0, dt * 14.0)
        visible_ids = set()

        for vehicle in vehicles:
            lane_view = self._lane_lookup.get(id(getattr(vehicle, "lane", None)))
            if lane_view is None:
                continue

            target = self._vehicle_world_position(vehicle, lane_view)
            vehicle_id = id(vehicle)
            visible_ids.add(vehicle_id)
            track = self._track_cache.setdefault(vehicle_id, {"pos": target, "color_index": vehicle_id % 5})
            old_x, old_y = track["pos"]
            draw_x = old_x + (target[0] - old_x) * smoothing
            draw_y = old_y + (target[1] - old_y) * smoothing
            track["pos"] = (draw_x, draw_y)

            sx, sy = self.camera.world_to_screen(draw_x, draw_y)
            if sx < -80 or sx > self.width + 80 or sy < -80 or sy > self.height + 80:
                continue

            color = self._vehicle_color(vehicle, int(track["color_index"]))
            angle = 0 if lane_view.orientation == "horizontal" else -90
            if lane_view.direction < 0:
                angle += 180
            self._draw_vehicle_body((sx, sy), angle, color, vehicle)

        for cached_id in list(self._track_cache):
            if cached_id not in visible_ids:
                del self._track_cache[cached_id]

    def draw_signals(self, signals: Iterable[Any] | None = None) -> None:
        signals = list(signals if signals is not None else self._resolve_state()[2])
        for signal in signals:
            position = self._signal_world_position(signal)
            if position is None:
                continue
            sx, sy = self.camera.world_to_screen(*position)
            if sx < -70 or sx > self.width + 70 or sy < -70 or sy > self.height + 70:
                continue

            state = str(getattr(signal, "state", "RED")).upper()
            radius = max(4, int(6 * self.camera.scale))
            spacing = radius * 2 + 4
            body = self.pygame.Rect(0, 0, radius * 3, spacing * 3 + 8)
            body.center = (sx, sy)
            self.pygame.draw.rect(self.screen, self.colors["signal_body"], body, border_radius=5)

            light_order = ("RED", "YELLOW", "GREEN")
            for index, light in enumerate(light_order):
                cx = body.centerx
                cy = body.top + spacing // 2 + 5 + index * spacing
                color = self._signal_color(light) if light == state else self.colors["off"]
                self.pygame.draw.circle(self.screen, color, (cx, cy), radius)
                self.pygame.draw.circle(self.screen, (8, 9, 9), (cx, cy), radius, 1)

            self._draw_stop_line(position)

    def shutdown(self) -> None:
        if self.pygame is not None:
            self.pygame.quit()
        self.initialized = False

    def _resolve_state(
        self,
        roads: Iterable[Any] | None = None,
        vehicles: Iterable[Any] | None = None,
        signals: Iterable[Any] | None = None,
    ) -> tuple[list[Any], list[Any], list[Any]]:
        manager = self.traffic_manager
        if roads is None and manager is not None:
            getter = getattr(manager, "get_roads", None)
            roads = getter() if callable(getter) else getattr(manager, "roads", [])
        if vehicles is None and manager is not None:
            getter = getattr(manager, "get_vehicles", None)
            vehicles = getter() if callable(getter) else getattr(manager, "vehicles", [])
        if signals is None and manager is not None:
            getter = getattr(manager, "get_signals", None)
            signals = getter() if callable(getter) else getattr(manager, "signals", [])

        return list(roads or []), list(vehicles or []), list(signals or [])

    def _update_layout(self, roads: list[Any], signals: list[Any]) -> None:
        signature = tuple(
            (
                id(road),
                getattr(road, "id", None),
                float(getattr(road, "length", 1000.0) or 1000.0),
                tuple(id(lane) for lane in getattr(road, "lanes", []) or []),
            )
            for road in roads
        )
        if signature == self._last_layout_signature:
            if self._needs_fit and self._layout:
                self.camera.fit_bounds(self._scene_bounds(), padding=90.0)
                self._needs_fit = False
            return

        self._last_layout_signature = signature
        self._layout = tuple(self._build_layout(roads, signals))
        self._lane_lookup = {
            id(lane_view.lane): lane_view
            for road_view in self._layout
            for lane_view in road_view.lanes
            if lane_view.lane is not None
        }
        self._needs_fit = True
        if self._layout:
            self.camera.fit_bounds(self._scene_bounds(), padding=90.0)
            self._needs_fit = False

    def _build_layout(self, roads: list[Any], signals: list[Any]) -> list[RoadView]:
        if not roads:
            return []

        max_length = max(float(getattr(road, "length", 1000.0) or 1000.0) for road in roads)
        signal_x = self._primary_signal_x(signals, default=max_length * 0.55)
        horizontal_y = 0.0
        vertical_x = signal_x
        road_views: list[RoadView] = []
        horizontal_count = 0
        vertical_count = 0

        for road_index, road in enumerate(roads):
            orientation = self._road_orientation(road, road_index)
            lanes = tuple(getattr(road, "lanes", []) or [])
            lane_count = max(1, len(lanes))
            length = float(getattr(road, "length", 1000.0) or 1000.0)
            thickness = lane_count * self.lane_width + self.road_margin * 2.0

            if orientation == "vertical":
                x = vertical_x + vertical_count * (thickness + self.lane_width * 1.2)
                y = horizontal_y - length * 0.5
                rect = (x - thickness * 0.5, y, thickness, length)
                vertical_count += 1
            else:
                x = 0.0
                y = horizontal_y + horizontal_count * (thickness + self.lane_width * 1.2)
                rect = (x, y - thickness * 0.5, length, thickness)
                horizontal_count += 1

            lane_views = self._build_lane_views(road, road_index, lanes, orientation, rect, length)
            road_views.append(RoadView(road, road_index, rect, orientation, tuple(lane_views), length))

        if len(road_views) == 1 and road_views[0].orientation == "horizontal":
            road_views.append(self._visual_cross_road(road_views[0], vertical_x))

        return road_views

    def _build_lane_views(
        self,
        road: Any,
        road_index: int,
        lanes: tuple[Any, ...],
        orientation: str,
        rect: tuple[float, float, float, float],
        length: float,
    ) -> list[LaneView]:
        lane_objects = lanes if lanes else (None,)
        x, y, w, h = rect
        lane_views = []
        for lane_index, lane in enumerate(lane_objects):
            direction = self._lane_direction(lane, road, orientation)
            if orientation == "vertical":
                lane_x = x + self.road_margin + lane_index * self.lane_width + self.lane_width * 0.5
                centerline = (lane_x, y + 6.0, lane_x, y + h - 6.0)
            else:
                lane_y = y + self.road_margin + lane_index * self.lane_width + self.lane_width * 0.5
                centerline = (x + 6.0, lane_y, x + w - 6.0, lane_y)
            lane_views.append(
                LaneView(
                    lane=lane,
                    index=lane_index,
                    centerline=centerline,
                    orientation=orientation,
                    direction=direction,
                    road_id=getattr(road, "id", road_index + 1),
                    length=float(getattr(lane, "length", length) or length) if lane is not None else length,
                )
            )
        return lane_views

    def _visual_cross_road(self, base: RoadView, center_x: float) -> RoadView:
        lane_count = max(1, len(base.lanes))
        thickness = lane_count * self.lane_width + self.road_margin * 2.0
        length = min(700.0, max(360.0, base.length * 0.7))
        rect = (center_x - thickness * 0.5, -length * 0.5, thickness, length)
        lane_views = []
        for lane_index in range(lane_count):
            lane_x = rect[0] + self.road_margin + lane_index * self.lane_width + self.lane_width * 0.5
            lane_views.append(
                LaneView(
                    lane=None,
                    index=lane_index,
                    centerline=(lane_x, rect[1] + 6.0, lane_x, rect[1] + rect[3] - 6.0),
                    orientation="vertical",
                    direction=1,
                    road_id="cross",
                    length=length,
                )
            )
        return RoadView(None, -1, rect, "vertical", tuple(lane_views), length)

    def _road_orientation(self, road: Any, road_index: int) -> str:
        raw = getattr(road, "orientation", None) or getattr(road, "direction", None)
        if isinstance(raw, str):
            value = raw.lower()
            if value in ("vertical", "north", "south", "n", "s"):
                return "vertical"
            if value in ("horizontal", "east", "west", "e", "w"):
                return "horizontal"
        return "horizontal" if road_index % 2 == 0 else "vertical"

    def _lane_direction(self, lane: Any, road: Any, orientation: str) -> int:
        raw = getattr(lane, "direction", None) if lane is not None else None
        if raw is None:
            raw = getattr(road, "direction", None)
        if isinstance(raw, (int, float)):
            return -1 if raw < 0 else 1
        if isinstance(raw, str):
            value = raw.lower()
            if value in ("west", "left", "north", "up", "reverse", "-1"):
                return -1
        return 1

    def _vehicle_world_position(self, vehicle: Any, lane_view: LaneView) -> tuple[float, float]:
        position = float(getattr(vehicle, "position", 0.0) or 0.0)
        progress = max(0.0, min(1.0, position / max(lane_view.length, 1.0)))
        if lane_view.direction < 0:
            progress = 1.0 - progress

        x0, y0, x1, y1 = lane_view.centerline
        return x0 + (x1 - x0) * progress, y0 + (y1 - y0) * progress

    def _signal_world_position(self, signal: Any) -> tuple[float, float] | None:
        raw = getattr(signal, "position", None)
        if not isinstance(raw, tuple) or len(raw) < 2:
            return None

        signal_x = float(raw[0])
        signal_y = float(raw[1])
        for lane_view in self._lane_lookup.values():
            lane = lane_view.lane
            intersection = getattr(lane, "intersection", None) if lane is not None else None
            get_signal = getattr(intersection, "get_signal_for_lane", None)
            if callable(get_signal) and get_signal(lane) is signal:
                x0, y0, x1, y1 = lane_view.centerline
                progress = max(0.0, min(1.0, signal_x / max(lane_view.length, 1.0)))
                if lane_view.direction < 0:
                    progress = 1.0 - progress
                sx = x0 + (x1 - x0) * progress
                sy = y0 + (y1 - y0) * progress
                if lane_view.orientation == "horizontal":
                    sy -= self.lane_width * 0.75
                else:
                    sx += self.lane_width * 0.75
                return sx, sy

        return signal_x, signal_y

    def _primary_signal_x(self, signals: list[Any], default: float) -> float:
        for signal in signals:
            position = getattr(signal, "position", None)
            if isinstance(position, tuple) and position:
                return float(position[0])
        return default

    def _intersection_zones(self) -> list[tuple[float, float, float]]:
        horizontal = [view for view in self._layout if view.orientation == "horizontal"]
        vertical = [view for view in self._layout if view.orientation == "vertical"]
        zones = []
        for h_view in horizontal:
            hx, hy, hw, hh = h_view.rect
            for v_view in vertical:
                vx, vy, vw, vh = v_view.rect
                if hx <= vx + vw and vx <= hx + hw and hy <= vy + vh and vy <= hy + hh:
                    cx = max(hx, vx) + (min(hx + hw, vx + vw) - max(hx, vx)) * 0.5
                    cy = max(hy, vy) + (min(hy + hh, vy + vh) - max(hy, vy)) * 0.5
                    zones.append((cx, cy, max(hh, vw) + 4.0))
        return zones

    def _scene_bounds(self) -> tuple[float, float, float, float]:
        min_x = min(view.rect[0] for view in self._layout) - self.world_padding
        min_y = min(view.rect[1] for view in self._layout) - self.world_padding
        max_x = max(view.rect[0] + view.rect[2] for view in self._layout) + self.world_padding
        max_y = max(view.rect[1] + view.rect[3] for view in self._layout) + self.world_padding
        return min_x, min_y, max_x, max_y

    def _draw_vehicle_body(self, center: tuple[int, int], angle: float, color: tuple[int, int, int], vehicle: Any) -> None:
        length = max(12, int(self.vehicle_size[0] * self.camera.scale))
        width = max(7, int(self.vehicle_size[1] * self.camera.scale))
        surface = self.pygame.Surface((length + 4, width + 4), self.pygame.SRCALPHA)
        rect = surface.get_rect()
        body = self.pygame.Rect(2, 2, length, width)
        self.pygame.draw.rect(surface, color, body, border_radius=max(2, int(3 * self.camera.scale)))
        self.pygame.draw.rect(surface, (14, 16, 17), body, width=1, border_radius=max(2, int(3 * self.camera.scale)))

        if float(getattr(vehicle, "acceleration", 0.0) or 0.0) < -0.2:
            brake = self.pygame.Rect(3, 3, max(2, length // 7), max(2, width // 4))
            self.pygame.draw.rect(surface, self.colors["brake"], brake, border_radius=1)
            brake.bottom = rect.bottom - 3
            self.pygame.draw.rect(surface, self.colors["brake"], brake, border_radius=1)

        rotated = self.pygame.transform.rotate(surface, angle)
        draw_rect = rotated.get_rect(center=center)
        self.screen.blit(rotated, draw_rect)

    def _vehicle_color(self, vehicle: Any, color_index: int) -> tuple[int, int, int]:
        velocity = float(getattr(vehicle, "velocity", 0.0) or 0.0)
        acceleration = float(getattr(vehicle, "acceleration", 0.0) or 0.0)
        if acceleration < -0.35:
            return self.colors["brake"]
        if velocity < 0.1:
            return self.colors["stopped"]
        palette = [
            self.colors["vehicle"],
            self.colors["vehicle_alt"],
            (129, 202, 116),
            (181, 129, 220),
            (236, 226, 105),
        ]
        return palette[color_index % len(palette)]

    def _draw_lane_edge_ticks(self, lane_view: LaneView) -> None:
        x0, y0, x1, y1 = lane_view.centerline
        if lane_view.orientation == "horizontal":
            offset = self.lane_width * 0.5
            self._draw_solid_world_line((x0, y0 - offset), (x1, y1 - offset), self.colors["edge"], 2)
            self._draw_solid_world_line((x0, y0 + offset), (x1, y1 + offset), self.colors["edge"], 2)
        else:
            offset = self.lane_width * 0.5
            self._draw_solid_world_line((x0 - offset, y0), (x1 - offset, y1), self.colors["edge"], 2)
            self._draw_solid_world_line((x0 + offset, y0), (x1 + offset, y1), self.colors["edge"], 2)

    def _draw_direction_arrow(self, lane_view: LaneView) -> None:
        x0, y0, x1, y1 = lane_view.centerline
        cx = x0 + (x1 - x0) * 0.36
        cy = y0 + (y1 - y0) * 0.36
        angle = 0.0 if lane_view.orientation == "horizontal" else math.pi / 2.0
        if lane_view.direction < 0:
            angle += math.pi
        length = 22.0
        tip = (cx + math.cos(angle) * length, cy + math.sin(angle) * length)
        tail = (cx - math.cos(angle) * length * 0.45, cy - math.sin(angle) * length * 0.45)
        left = (tip[0] - math.cos(angle - 0.65) * 10.0, tip[1] - math.sin(angle - 0.65) * 10.0)
        right = (tip[0] - math.cos(angle + 0.65) * 10.0, tip[1] - math.sin(angle + 0.65) * 10.0)
        self._draw_solid_world_line(tail, tip, self.colors["lane_dim"], 2)
        self._draw_solid_world_line(tip, left, self.colors["lane_dim"], 2)
        self._draw_solid_world_line(tip, right, self.colors["lane_dim"], 2)

    def _draw_stop_line(self, signal_position: tuple[float, float]) -> None:
        sx, sy = signal_position
        for lane_view in self._lane_lookup.values():
            x0, y0, x1, y1 = lane_view.centerline
            if lane_view.orientation == "horizontal" and abs(sy - y0) < self.lane_width * 1.5:
                self._draw_solid_world_line((sx, y0 - self.lane_width * 0.45), (sx, y0 + self.lane_width * 0.45), self.colors["lane"], 3)
                return
            if lane_view.orientation == "vertical" and abs(sx - x0) < self.lane_width * 1.5:
                self._draw_solid_world_line((x0 - self.lane_width * 0.45, sy), (x0 + self.lane_width * 0.45, sy), self.colors["lane"], 3)
                return

    def _draw_hud(self, road_count: int, vehicle_count: int, signal_count: int) -> None:
        text = f"Roads {road_count}   Vehicles {vehicle_count}   Signals {signal_count}"
        controls = "SPACE pause   R reset flag   ESC quit   WASD/arrows pan   +/- zoom"
        if self.paused:
            text += "   PAUSED"
        label = self.small_font.render(text, True, self.colors["text"])
        hint = self.small_font.render(controls, True, self.colors["muted"])
        self.screen.blit(label, (14, 12))
        self.screen.blit(hint, (14, 30))

    def _draw_console(self, roads: list[Any], vehicles: list[Any], signals: list[Any]) -> None:
        if self.frame_count % 30 == 1:
            print(
                f"[Renderer] frame={self.frame_count} roads={len(roads)} "
                f"vehicles={len(vehicles)} signals={len(signals)}"
            )

    def _draw_dashed_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        dash: int = 12,
        gap: int = 10,
        width: int = 1,
    ) -> None:
        x0, y0 = start
        x1, y1 = end
        total = math.hypot(x1 - x0, y1 - y0)
        if total <= 0:
            return
        ux = (x1 - x0) / total
        uy = (y1 - y0) / total
        distance = 0.0
        while distance < total:
            segment_end = min(total, distance + dash)
            sx = x0 + ux * distance
            sy = y0 + uy * distance
            ex = x0 + ux * segment_end
            ey = y0 + uy * segment_end
            self.pygame.draw.line(self.screen, color, (int(sx), int(sy)), (int(ex), int(ey)), width)
            distance += dash + gap

    def _draw_solid_world_line(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int],
        width: int,
    ) -> None:
        self.pygame.draw.line(self.screen, color, self.camera.world_to_screen(*start), self.camera.world_to_screen(*end), width)

    def _world_rect_center(self, cx: float, cy: float, w: float, h: float) -> tuple[float, float, float, float]:
        return cx - w * 0.5, cy - h * 0.5, w, h

    def _rect_visible(self, rect: Any, margin: int = 0) -> bool:
        return rect.right >= -margin and rect.left <= self.width + margin and rect.bottom >= -margin and rect.top <= self.height + margin

    def _signal_color(self, state: str) -> tuple[int, int, int]:
        return {
            "RED": self.colors["red"],
            "YELLOW": self.colors["yellow"],
            "GREEN": self.colors["green"],
        }.get(state, self.colors["off"])
