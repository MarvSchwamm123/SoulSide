# game/camera.py

import pygame


class Camera:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        
        self.position = pygame.Vector2(0, 0)

        self.scale = 50

    def world_to_screen(self, position: tuple[float, float]):
        x = (position[0] - self.position.x) * self.scale
        y = (position[1] - self.position.y) * self.scale

        y = self.screen.get_height() - y

        return int(x), int(y)

    def draw_room(self, room):
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

            pygame.draw.polygon(
                self.screen,
                (100, 100, 100),
                points
            )

            pygame.draw.polygon(
                self.screen,
                (255, 0, 0),
                points,
                width=2
            )


    def draw_entity(self, entitys):
        colors = {
            "player": (0, 100, 255),
            "enemy": (255, 0, 0), 
            "npc": (0, 200, 0),       
        }

        for entity in entitys:
            if not entity.visible:
                continue

            color = colors.get(entity.type, (150, 150, 150))

            left = entity.position.x - entity.width / 2
            bottom = entity.position.y

            top_left = self.world_to_screen((
                left,
                bottom + entity.height
            ))

            width = round(entity.width * self.scale)
            height = round(entity.height * self.scale)

            rect = pygame.Rect(
                top_left[0],
                top_left[1],
                width,
                height
            )

            pygame.draw.rect(
                self.screen,
                color,
                rect,
                width=2
            )
        
    def follow(self, player):
        self.position.x = player.position.x - (
            self.screen.get_width() / (2 * self.scale)
        )

        self.position.y = player.position.y + player.height / 2 - (
            self.screen.get_height() / (2 * self.scale)
        )
