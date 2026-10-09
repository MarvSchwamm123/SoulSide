import json
import pygame
from pathlib import Path


SETTINGS_PATH = (
    Path(__file__).resolve().parent.parent
    / "settings"
    / "controls.json"
)


def load_controls():
    with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        "left": pygame.key.key_code(data["left"]),
        "right": pygame.key.key_code(data["right"]),
        "jump": pygame.key.key_code(data["jump"])
    }