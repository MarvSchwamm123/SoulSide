import json

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from world.rooms import Room
from helper import Triangle


def load_room(
    position: tuple[int, int],
    connections: list[dict]
) -> Room:
    
    world_path = Path(__file__).resolve().parent.parent
    path = world_path / "world" / "rooms" / f"{position[0]}_{position[1]}.json"

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    collision = [
        Triangle(
            triangle["a"],
            triangle["b"],
            triangle["c"]
        )
        for triangle in data["collision"]
    ]

    return Room(
        position=position,
        images=data["images"],
        collision=collision,
        boarders=data["boarders"],
        connections=connections
    )