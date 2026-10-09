# game/camera.py

import pygame


class Camera:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen

        # Position der Kamera in Weltkoordinaten
        self.position = pygame.Vector2(0, 0)

        # Pixel pro Welt-Einheit
        self.scale = 50

    def world_to_screen(self, position: tuple[float, float]):
        x = (position[0] - self.position.x) * self.scale
        y = (position[1] - self.position.y) * self.scale

        # Unsere Welt hat Y nach oben,
        # Pygame hat Y nach unten.
        y = self.screen.get_height() - y

        return int(x), int(y)

    def draw_room(self, room):
        # Raumgrenzen
        points = []

        for point in room.boarders:
            world_position = (
                room.position[0] + point[0],
                room.position[1] + point[1]
            )

            points.append(
                self.world_to_screen(world_position)
            )

        if len(points) >= 2:
            pygame.draw.polygon(
                self.screen,
                (0, 0, 0),
                points,
                width=3
            )

        # Kollisionsdreiecke
        for triangle in room.collision:
            points = [
                self.world_to_screen((
                    room.position[0] + triangle.a.x,
                    room.position[1] + triangle.a.y
                )),
                self.world_to_screen((
                    room.position[0] + triangle.b.x,
                    room.position[1] + triangle.b.y
                )),
                self.world_to_screen((
                    room.position[0] + triangle.c.x,
                    room.position[1] + triangle.c.y
                ))
            ]

            # Füllung
            pygame.draw.polygon(
                self.screen,
                (100, 100, 100),
                points
            )

            # Rand
            pygame.draw.polygon(
                self.screen,
                (255, 0, 0),
                points,
                width=2
            )

    def draw_player(self, player):
        left = player.position.x - player.width / 2
        bottom = player.position.y

        top_left = self.world_to_screen((
            left,
            bottom + player.height
        ))

        rect = pygame.Rect(
            top_left[0],
            top_left[1],
            round(player.width * self.scale),
            round(player.height * self.scale)
        )

        pygame.draw.rect(
            self.screen,
            (80, 30, 100),
            rect
        )