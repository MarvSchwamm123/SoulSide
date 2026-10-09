# helper.py

import json
import pygame


def load_image(path: str) -> pygame.Surface:
    return pygame.image.load(path).convert_alpha()

class Triangle:
    def __init__(self, a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]):
        self.a = pygame.Vector2(a)
        self.b = pygame.Vector2(b)
        self.c = pygame.Vector2(c)


def get_entrances(
    position: tuple[int, int],
    connections: list[dict]
):
    entrances = []

    for connection in connections:
        room_a = tuple(connection["room_a"])
        room_b = tuple(connection["room_b"])

        if position == room_a:
            entrances.append({
                "start": tuple(connection["entrance_a"]["start"]),
                "end": tuple(connection["entrance_a"]["end"]),
                "target": room_b
            })

        elif position == room_b:
            entrances.append({
                "start": tuple(connection["entrance_b"]["start"]),
                "end": tuple(connection["entrance_b"]["end"]),
                "target": room_a
            })

    return entrances