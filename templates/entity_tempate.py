import pygame


class Entity:
    def __init__(
        self,
        position,
        width=1.0,
        height=1.0,
        weight=1.0,
        texture=None,
    ):
        self.type = "entity"

        self.position = pygame.Vector2(position)
        self.width = width
        self.height = height

        self.x_velocity = 0.0
        self.y_velocity = 0.0
        self.weight = weight

        self.can_jump = False
        self.jump_held = False
        self.collision = True

        self.texture = texture
        self.visible = True

    def update(self, delta_time):
        """Entity-Verhalten pro Tick."""

    def draw(self, camera):
        """Darstellung über die Kamera."""
        if not self.visible:
            return

        camera.draw_entity(self)