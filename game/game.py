# game/game.py

import sys
from pathlib import Path
from settings import load_controls

sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
import pygame
from time import perf_counter

from camera import Camera
from world.loader import load_room
from player.player import Player

class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("SoulSide")

        self.running = True

        self.FPS = 120
        self.TPS = 60

        self.last_fps = perf_counter()
        self.last_tps = perf_counter()

        # Connections laden
        project_root = Path(__file__).resolve().parent.parent
        
        with open(project_root / "world" / "connections.json", "r", encoding="utf-8") as file:
            self.connections = json.load(file)

        self.room = load_room(
            (10, 0),
            self.connections
        )
        
        self.controls = load_controls()
        self.pressed_keys = {
            "right": False,
            "left": False,
            "jump": False
        }
        
        self.player = Player(
            position=(15, 0.6),
            health=100,
            max_health=100,
            abilities=[],
            wounds=[],
            soul_loss_multiplier=1.0,
            speed=5
        )
        self.player_velocity_x = 0
        self.player_velocity_y = 0
        self.player_acceleration_x = 50
        self.cur_gravity = 25
        
        self.on_floor = False
        
        self.entitys = []

        self.camera = Camera(self.screen)
        
        self.entitys.append(self.player)

    def run(self):
        for i in range(0, 10):
            print("                                                                           ")
        print("\033[H", end="")
        while self.running:
            current_time = perf_counter()

            if current_time - self.last_tps >= 1 / self.TPS:
                self.last_tps = current_time
                print("update                                                               ")
                self.update()
                print("\033[H", end="")

            if current_time - self.last_fps >= 1 / self.FPS:
                self.last_fps = current_time
                self.draw()

        pygame.quit()

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == self.controls["jump"]:
                    if self.player.start_jump(self.on_floor):
                        self.on_floor = False

            elif event.type == pygame.KEYUP:
                if event.key == self.controls["jump"]:
                    if self.player.jump_held and self.player.y_velocity > 0:
                        self.player.y_velocity *= self.player.jump_cut_multiplier

                    self.player.jump_held = False

        self.key_events()

        delta_time = 1 / self.TPS

        self.player.update_jump(delta_time)
        self.gravity(delta_time)
        self.move_player(delta_time)
        
        self.check_room_transition()
        self.camera.follow(self.player)

    def draw(self):
        self.screen.fill((255, 255, 255))

        self.camera.draw_room(self.room)
        self.camera.draw_entity(self.entitys)

        pygame.display.flip()
        
    def key_events(self):
        keys = pygame.key.get_pressed()

        if keys[self.controls["left"]]:
            self.pressed_keys["left"] = True
        else:
            self.pressed_keys["left"] = False

        if keys[self.controls["right"]]:
            self.pressed_keys["right"] = True
        else:
            self.pressed_keys["right"] = False

        if keys[self.controls["jump"]]:
            self.pressed_keys["jump"] = True
        else:
            self.pressed_keys["jump"] = False 

    def gravity(self, delta_time):
        for entity in self.entitys:
            entity.y_velocity -= (
                entity.weight * self.cur_gravity * delta_time
            )

    def move_player(self, delta_time):
        acceleration = self.player_acceleration_x
        max_speed = self.player.speed

        if self.pressed_keys["left"] and not self.pressed_keys["right"]:
            self.player.x_velocity -= acceleration * delta_time

        elif self.pressed_keys["right"] and not self.pressed_keys["left"]:
            self.player.x_velocity += acceleration * delta_time

        else:
            friction = acceleration * 2 * delta_time

            if self.player.x_velocity > 0:
                self.player.x_velocity = max(
                    0, self.player.x_velocity - friction
                )
            elif self.player.x_velocity < 0:
                self.player.x_velocity = min(
                    0, self.player.x_velocity + friction
                )

        self.player.x_velocity = max(
            -max_speed,
            min(max_speed, self.player.x_velocity)
        )

        dx = self.player.x_velocity * delta_time
        dy = self.player.y_velocity * delta_time

        collisions = self.calc_collision(self.player, dx, dy)

        if collisions:
            print("Kollision:", collisions,"                                                                                                            ")

    def entity_rect_points(self, entity, x, y):
        left = x - entity.width / 2
        right = x + entity.width / 2
        bottom = y
        top = y + entity.height

        return [
            pygame.Vector2(left, bottom),
            pygame.Vector2(left, top),
            pygame.Vector2(right, bottom),
            pygame.Vector2(right, top),
        ]

    def rect_triangle_collision(self, rect_points, triangle_points):
        axes = [
            pygame.Vector2(1, 0),
            pygame.Vector2(0, 1),
        ]

        for i in range(3):
            edge = (
                triangle_points[(i + 1) % 3]
                - triangle_points[i]
            )
            axes.append(pygame.Vector2(-edge.y, edge.x))

        for axis in axes:
            rect_projection = [p.dot(axis) for p in rect_points]
            tri_projection = [p.dot(axis) for p in triangle_points]

            # Berührung allein zählt noch nicht als Überschneidung.
            if (
                max(rect_projection) <= min(tri_projection)
                or max(tri_projection) <= min(rect_projection)
            ):
                return False

        return True

    def calc_collision(self, entity, dx, dy):
        collisions = []

        # Dreiecke von Raumkoordinaten in Weltkoordinaten umrechnen.
        triangles = []
        room_offset = pygame.Vector2(self.room.position)

        for triangle in self.room.collision:
            triangles.append([
                triangle.a + room_offset,
                triangle.b + room_offset,
                triangle.c + room_offset,
            ])

        def collides_at(x, y):
            rect = self.entity_rect_points(entity, x, y)

            for triangle in triangles:
                if self.rect_triangle_collision(rect, triangle):
                    return True

            return False

        # X-Achse separat bewegen.
        if dx != 0:
            start_x = entity.position.x
            target_x = start_x + dx

            if collides_at(target_x, entity.position.y):
                low, high = 0.0, 1.0

                for _ in range(16):
                    middle = (low + high) / 2
                    test_x = start_x + dx * middle

                    if collides_at(test_x, entity.position.y):
                        high = middle
                    else:
                        low = middle

                entity.position.x = start_x + dx * low
                entity.x_velocity = 0
                collisions.append("rechts" if dx > 0 else "links")
            else:
                entity.position.x = target_x

        # Y-Achse separat bewegen.
        if dy != 0:
            start_y = entity.position.y
            target_y = start_y + dy

            if collides_at(entity.position.x, target_y):
                low, high = 0.0, 1.0

                for _ in range(16):
                    middle = (low + high) / 2
                    test_y = start_y + dy * middle

                    if collides_at(entity.position.x, test_y):
                        high = middle
                    else:
                        low = middle

                entity.position.y = start_y + dy * low
                entity.y_velocity = 0

                if dy < 0:
                    collisions.append("unten")
                    self.on_floor = True
                    entity.jump_held = False
                else:
                    collisions.append("oben")
            else:
                entity.position.y = target_y
                if dy < 0:
                    self.on_floor = False

        return collisions

    def check_room_transition(self):
        player = self.player

        left = player.position.x - player.width / 2
        right = player.position.x + player.width / 2
        bottom = player.position.y
        top = bottom + player.height

        current_room = tuple(self.room.position)

        for connection in self.connections:
            for side_a, side_b in [
                ("room_a", "room_b"),
                ("room_b", "room_a")
            ]:
                if tuple(connection[side_a]) != current_room:
                    continue

                entrance = connection[
                    "entrance_a" if side_a == "room_a" else "entrance_b"
                ]

                target_room = tuple(connection[side_b])

                start = entrance["start"]
                end = entrance["end"]

                # Position der Öffnung in Weltkoordinaten
                room_offset = pygame.Vector2(current_room)
                start = pygame.Vector2(start) + room_offset
                end = pygame.Vector2(end) + room_offset

                # Funktioniert für vertikale und horizontale Eingänge.
                if start.x == end.x:
                    door_x = start.x
                    door_min_y = min(start.y, end.y)
                    door_max_y = max(start.y, end.y)

                    crossed = (
                        left <= door_x <= right
                        and top > door_min_y
                        and bottom < door_max_y
                    )

                elif start.y == end.y:
                    door_y = start.y
                    door_min_x = min(start.x, end.x)
                    door_max_x = max(start.x, end.x)

                    crossed = (
                        bottom <= door_y <= top
                        and right > door_min_x
                        and left < door_max_x
                    )

                else:
                    continue

                if crossed:
                    self.room = load_room(target_room, self.connections)

                    # Spieler auf die Seite des neuen Raums setzen
                    if start.x == end.x:
                        # Vertikaler Eingang: links oder rechts
                        if target_room[0] > current_room[0]:
                            player.position.x = door_x + 0.51
                        elif target_room[0] < current_room[0]:
                            player.position.x = door_x - 0.51

                    elif start.y == end.y:
                        # Horizontaler Eingang: oben oder unten
                        if target_room[1] > current_room[1]:
                            player.position.y = door_y + 0
                        elif target_room[1] < current_room[1]:
                            player.position.y = door_y - 2.01

                    return



if __name__ == "__main__":
    Game().run()