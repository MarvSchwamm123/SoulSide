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

        # Start-Raum laden
        self.room = load_room(
            (0, 0),
            self.connections
        )
        
        self.controls = load_controls()
        self.pressed_keys = {
            "right": False,
            "left": False,
            "jump": False
        }
        
        self.player = Player(
            position=(1, 0.6),
            health=100,
            max_health=100,
            abilities=[],
            wounds=[],
            soul_loss_multiplier=1.0,
            speed=2
        )
        self.player_velocity_x = 0
        self.player_velocity_y = 0
        self.player_acceleration_x = 8
        self.cur_gravity = 0.8
        
        self.entitys = []
        
        self.can_jump = True

        # Camera
        self.camera = Camera(self.screen)
        
        self.entitys.append(self.player)

    def run(self):
        while self.running:
            current_time = perf_counter()

            if current_time - self.last_tps >= 1 / self.TPS:
                self.last_tps = current_time
                self.update()

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
                    
        self.key_events()
        self.move_player(1/self.TPS)
        #self.gravity()

    def draw(self):
        self.screen.fill((255, 255, 255))

        self.camera.draw_room(self.room)
        self.camera.draw_player(self.player)

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
            
    def gravity(self):
        for entity in self.entitys:
            y_speed_difference = entity.weight*self.cur_gravity
            entity.y_velocity -= y_speed_difference


    def move_player(self, delta_time):
        acceleration = self.player_acceleration_x
        max_speed = self.player.speed

        # Links und rechts
        if self.pressed_keys["left"] and not self.pressed_keys["right"]:
            self.player.x_velocity -= acceleration * delta_time

        elif self.pressed_keys["right"] and not self.pressed_keys["left"]:
            self.player.x_velocity += acceleration * delta_time

        else:
            # Abbremsen, wenn keine Richtung gedrückt wird
            friction = acceleration * 2 * delta_time

            if self.player.x_velocity > 0:
                self.player.x_velocity = max(0, self.player.x_velocity - friction)
            elif self.player.x_velocity < 0:
                self.player.x_velocity = min(0, self.player.x_velocity + friction)

        # Höchstgeschwindigkeit begrenzen
        self.player.x_velocity = max(
            -max_speed,
            min(max_speed, self.player.x_velocity)
        )

        # Springen
        if self.pressed_keys["jump"] and self.can_jump:
            self.player.y_velocity = self.player.jump_force
            self.can_jump = False

        # Position aktualisieren
        self.player.position[0] += self.player.x_velocity * delta_time
        self.player.position[1] += self.player.y_velocity * delta_time


if __name__ == "__main__":
    Game().run()