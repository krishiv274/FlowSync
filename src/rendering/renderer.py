"""Renderer for traffic simulation visualization."""


class Camera:
    """Manages viewport transformations (pan, zoom, centering)."""

    def __init__(self, width=1200, height=800):
        """Initialize camera with default framing."""
        self.width = width
        self.height = height
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates."""
        screen_x = (world_x - self.offset_x) * self.zoom + self.width / 2
        screen_y = (world_y - self.offset_y) * self.zoom + self.height / 2
        return (screen_x, screen_y)

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_x - self.width / 2) / self.zoom + self.offset_x
        world_y = (screen_y - self.height / 2) / self.zoom + self.offset_y
        return (world_x, world_y)

    def pan(self, dx, dy):
        """Pan the camera by (dx, dy) in world units."""
        self.offset_x += dx / self.zoom
        self.offset_y += dy / self.zoom

    def zoom_in(self, factor=1.2):
        """Zoom in by the given factor."""
        self.zoom = min(self.zoom * factor, self.max_zoom)

    def zoom_out(self, factor=1.2):
        """Zoom out by the given factor."""
        self.zoom = max(self.zoom / factor, self.min_zoom)

    def reset(self):
        """Reset camera to default state."""
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.zoom = 1.0

    def fit_bounds(self, min_x, min_y, max_x, max_y, padding=50):
        """Adjust zoom and pan to fit the given world bounds on screen."""
        world_width = max_x - min_x
        world_height = max_y - min_y
        
        if world_width <= 0 or world_height <= 0:
            self.reset()
            return
        
        zoom_x = (self.width - 2 * padding) / world_width
        zoom_y = (self.height - 2 * padding) / world_height
        self.zoom = min(zoom_x, zoom_y, self.max_zoom)
        self.offset_x = min_x + world_width / 2
        self.offset_y = min_y + world_height / 2


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
        self.camera = Camera(width, height)
        self.pan_speed = 20.0
        self.background_color = (20, 24, 32)
        self.road_color = (52, 58, 68)
        self.lane_color = (120, 126, 138)
        self.edge_color = (30, 34, 42)
        self.vehicle_color = (70, 150, 255)
        self.stopped_vehicle_color = (245, 124, 0)
        self.signal_outline_color = (18, 18, 18)
        self.overlay_color = (240, 242, 246)
        self.keys_pressed = set()
        self._should_refit_scene = False
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
            if event.type == self.pygame.KEYDOWN:
                if event.key == self.pygame.K_ESCAPE:
                    return False
                self.keys_pressed.add(event.key)
                if event.key == self.pygame.K_EQUALS or event.key == self.pygame.K_PLUS:
                    self.camera.zoom_in(1.2)
                if event.key == self.pygame.K_MINUS:
                    self.camera.zoom_out(1.2)
                if event.key == self.pygame.K_c:
                    self.camera.reset()
                    self._should_refit_scene = True
            if event.type == self.pygame.KEYUP:
                self.keys_pressed.discard(event.key)
            if event.type == self.pygame.VIDEORESIZE:
                self.width = max(640, event.w)
                self.height = max(480, event.h)
                self.camera.width = self.width
                self.camera.height = self.height
                self.screen = self.pygame.display.set_mode(
                    (self.width, self.height),
                    self.pygame.RESIZABLE,
                )
            if event.type == self.pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.camera.zoom_in(1.15)
                elif event.y < 0:
                    self.camera.zoom_out(1.15)

        self._handle_continuous_pan()
        return True

    def update(self):
        """Advance renderer timing and maintain a steady frame rate."""
        if self.initialized and self.clock is not None:
            self.clock.tick(60)

    def _handle_continuous_pan(self):
        """Handle continuous panning based on held-down arrow keys."""
        if not self.pygame:
            return
        
        if self.pygame.K_LEFT in self.keys_pressed or self.pygame.K_a in self.keys_pressed:
            self.camera.pan(-self.pan_speed / self.camera.zoom, 0)
        if self.pygame.K_RIGHT in self.keys_pressed or self.pygame.K_d in self.keys_pressed:
            self.camera.pan(self.pan_speed / self.camera.zoom, 0)
        if self.pygame.K_UP in self.keys_pressed or self.pygame.K_w in self.keys_pressed:
            self.camera.pan(0, -self.pan_speed / self.camera.zoom)
        if self.pygame.K_DOWN in self.keys_pressed or self.pygame.K_s in self.keys_pressed:
            self.camera.pan(0, self.pan_speed / self.camera.zoom)

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

        # Auto-fit camera on first real frame
        if self.frame_count == 1:
            self._auto_fit_scene(roads)

        self.screen.fill(self.background_color)
        self._draw_roads(roads)
        self._draw_signals(signals)
        self._draw_vehicles(roads, vehicles)
        self._draw_overlay(roads, vehicles, signals)
        self.pygame.display.flip()

        # Re-fit scene on demand
        if self._should_refit_scene:
            self._auto_fit_scene(roads)
            self._should_refit_scene = False

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
        """Draw roads with lanes using camera-transformed world coordinates."""
        lane_height = 40.0
        road_spacing = 150.0
        x_start = 0.0
        y_start = 0.0

        for road_index, road in enumerate(roads):
            lanes = getattr(road, "lanes", [])
            road_length = getattr(road, "length", 1000.0)
            lane_count = max(1, len(lanes))

            road_world_x = x_start
            road_world_y = y_start + road_index * road_spacing

            # Draw road background
            road_end_x = road_world_x + road_length
            x0_screen, y0_screen = self.camera.world_to_screen(road_world_x - 10, road_world_y - 20)
            x1_screen, y1_screen = self.camera.world_to_screen(
                road_end_x + 10, road_world_y + lane_count * lane_height + 20
            )
            
            # Only draw if on screen
            if not self._rect_on_screen(x0_screen, y0_screen, x1_screen, y1_screen):
                continue

            road_rect = self.pygame.Rect(
                int(min(x0_screen, x1_screen)), int(min(y0_screen, y1_screen)),
                int(abs(x1_screen - x0_screen)), int(abs(y1_screen - y0_screen))
            )
            self.pygame.draw.rect(self.screen, self.edge_color, road_rect, border_radius=8)
            self.pygame.draw.rect(self.screen, self.road_color, road_rect, 0, border_radius=8)

            # Draw lane separators and labels
            for lane_index, lane in enumerate(lanes):
                lane_world_y = road_world_y + lane_index * lane_height
                lane_world_y_next = lane_world_y + lane_height

                # Draw lane separator line
                if lane_index > 0:
                    x0_s, y_sep = self.camera.world_to_screen(road_world_x, lane_world_y)
                    x1_s, _ = self.camera.world_to_screen(road_end_x, lane_world_y)
                    self.pygame.draw.line(self.screen, self.lane_color, (int(x0_s), int(y_sep)), (int(x1_s), int(y_sep)), 1)

                # Draw lane label
                label_x, label_y = self.camera.world_to_screen(road_world_x + 20, lane_world_y + lane_height / 2)
                if -100 < label_x < self.width + 100 and -100 < label_y < self.height + 100:
                    label_text = self.small_font.render(
                        f"R{getattr(road, 'id', road_index + 1)}L{getattr(lane, 'id', lane_index + 1)}",
                        True, self.overlay_color
                    )
                    self.screen.blit(label_text, (int(label_x), int(label_y) - 8))

    def _rect_on_screen(self, x0, y0, x1, y1):
        """Check if a rectangle is at least partially on screen."""
        return (x0 < self.width and x1 > 0 and y0 < self.height and y1 > 0)

    def _draw_vehicles(self, roads, vehicles):
        """Draw vehicles using camera-transformed world coordinates."""
        lane_height = 40.0
        road_spacing = 150.0
        x_start = 0.0
        y_start = 0.0

        for vehicle in vehicles:
            lane = getattr(vehicle, "lane", None)
            if lane is None:
                continue

            # Find road index and lane index
            road_index = None
            lane_index = None
            for r_idx, road in enumerate(roads):
                lanes = getattr(road, "lanes", [])
                for l_idx, l in enumerate(lanes):
                    if l is lane:
                        road_index = r_idx
                        lane_index = l_idx
                        break
                if road_index is not None:
                    break

            if road_index is None or lane_index is None:
                continue

            road_length = getattr(lane, "length", 1000.0)
            position = float(getattr(vehicle, "position", 0.0))
            velocity = float(getattr(vehicle, "velocity", 0.0))

            # Convert to world coordinates
            world_x = position
            world_y = y_start + road_index * road_spacing + lane_index * lane_height + lane_height / 2
            screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)

            # Only draw if on screen
            if not (-50 < screen_x < self.width + 50 and -50 < screen_y < self.height + 50):
                continue

            # Draw vehicle
            vehicle_color = self.vehicle_color if velocity > 0.5 else self.stopped_vehicle_color
            rect = self.pygame.Rect(0, 0, 24, 14)
            rect.center = (int(screen_x), int(screen_y))
            self.pygame.draw.rect(self.screen, vehicle_color, rect, border_radius=3)
            self.pygame.draw.rect(self.screen, (18, 18, 18), rect, 1, border_radius=3)

            # Draw vehicle label
            v_id = getattr(vehicle, "id", "V")
            label = self.small_font.render(str(v_id), True, (255, 255, 255))
            self.screen.blit(label, (int(screen_x) - label.get_width() // 2, int(screen_y) - 14))

    def _draw_signals(self, signals):
        """Draw traffic signals using camera-transformed world coordinates."""
        signal_colors = {
            "RED": (220, 72, 72),
            "YELLOW": (245, 196, 72),
            "GREEN": (88, 190, 117),
        }

        for signal in signals:
            position = getattr(signal, "position", (0, 0))
            if not isinstance(position, tuple) or len(position) != 2:
                continue

            world_x, world_y = position
            screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)

            # Only draw if on screen
            if not (-50 < screen_x < self.width + 50 and -50 < screen_y < self.height + 50):
                continue

            state = getattr(signal, "state", "RED")
            color = signal_colors.get(state, (200, 200, 200))
            
            # Draw signal housing
            body = self.pygame.Rect(int(screen_x) - 10, int(screen_y) - 22, 20, 44)
            self.pygame.draw.rect(self.screen, (28, 28, 28), body, border_radius=6)
            self.pygame.draw.rect(self.screen, self.signal_outline_color, body, 2, border_radius=6)
            
            # Draw active light
            light_center = body.center
            self.pygame.draw.circle(self.screen, color, light_center, 6)
            self.pygame.draw.circle(self.screen, (255, 255, 255), light_center, 6, 1)

            # Draw signal label
            sig_id = getattr(signal, "id", "?")
            label = self.small_font.render(f"S{sig_id}:{state}", True, self.overlay_color)
            self.screen.blit(label, (body.left - 15, body.bottom + 4))

    def _draw_overlay(self, roads, vehicles, signals):
        """Draw HUD with simulation and camera state."""
        # Calculate scene bounds for info
        scene_bounds = self._calculate_scene_bounds(roads)
        
        lines = [
            f"Frame: {self.frame_count}",
            f"Roads: {len(roads)}  Vehicles: {len(vehicles)}  Signals: {len(signals)}",
            f"Zoom: {self.camera.zoom:.2f}x  Pan: ({self.camera.offset_x:.1f}, {self.camera.offset_y:.1f})",
            f"Scene: X({scene_bounds[0]:.0f}-{scene_bounds[2]:.0f}) Y({scene_bounds[1]:.0f}-{scene_bounds[3]:.0f})",
            "Controls: ARROWS/WASD pan | +/- zoom | C reset | ESC quit",
        ]

        x = 12
        y = 12
        for line in lines:
            text = self.small_font.render(line, True, self.overlay_color)
            self.screen.blit(text, (x, y))
            y += 16

    def _calculate_scene_bounds(self, roads):
        """Calculate the bounding box of the scene."""
        if not roads:
            return (0, 0, 100, 100)

        min_x = 0
        max_x = 100
        min_y = 0
        max_y = 100

        lane_height = 40.0
        road_spacing = 150.0

        for road_index, road in enumerate(roads):
            lanes = getattr(road, "lanes", [])
            road_length = getattr(road, "length", 1000.0)
            lane_count = len(lanes) if lanes else 1

            max_x = max(max_x, road_length)
            max_y = max(max_y, road_index * road_spacing + lane_count * lane_height)

        return (min_x, min_y, max_x, max_y)

    def _auto_fit_scene(self, roads):
        """Auto-fit camera to show all roads and lanes."""
        min_x, min_y, max_x, max_y = self._calculate_scene_bounds(roads)
        self.camera.fit_bounds(min_x, min_y, max_x, max_y, padding=100)
