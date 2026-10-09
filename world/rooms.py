import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from helper import load_image, Triangle, get_entrances

class Room:
    def __init__(self, position: tuple[int, int], images: list[str], collision: list[Triangle], boarders: list[tuple[int, int]], connections: list[dict]):
        self.position = position
        
        self.image_layers = []
        for image_path in images:
            self.image_layers.append(load_image(image_path))
        
        self.collision = collision
        
        self.boarders = boarders
        
        self.entrances = get_entrances(self.position, connections)
        