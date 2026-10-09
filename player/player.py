import pygame


class Player:
    def __init__(self, position: tuple[float, float], speed: int, health: int, max_health: int, abilities: list, wounds: list, soul_loss_multiplier: float):
        self.position = pygame.Vector2(position)

        self.health = health
        self.max_health = max_health

        self.abilities = abilities
        self.wounds = wounds
        
        self.jump_force = 10
        self.speed = speed
        
        self.y_velocity = 0
        self.x_velocity = 0
        
        self.weight = 1

        self.soul_loss_multiplier = soul_loss_multiplier

        # Größe des Spielers in Welt-Einheiten
        self.width = 1
        self.height = 2
        
        self.hitbox_width = 0.6
        self.hitbox_height = 1.8
        self.hitbox_offset_x = 0.2
        self.hitbox_offset_y = 0.1

    def take_damage(self, damage):
        if damage <= 0:
            return

        self.health = max(0, self.health - damage)

        self.wounds.append({
            "damage": damage,
            "soul_loss": damage * self.soul_loss_multiplier
        })

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def upgrade_health(self, amount):
        self.max_health += amount
        self.health += amount

    def upgrade_soul_control(self, reduction):
        self.soul_loss_multiplier = max(0.0, self.soul_loss_multiplier - reduction)

    def is_alive(self):
        return self.health > 0