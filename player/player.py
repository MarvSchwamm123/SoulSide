import pygame


class Player:
    def __init__(self, position: tuple[float, float], speed: int, health: int, max_health: int, abilities: list, wounds: list, soul_loss_multiplier: float):
        self.position = pygame.Vector2(position)
        
        self.visible = True
        self.type = "player"

        self.jump_hold_time = 0.25
        self.max_jump_hold_time = 0.5
        self.jump_hold_force = 18
        self.jump_cut_multiplier = 0.5
        self.jump_held = False
        self.jump_force = 11
        
        self.estimated_x = self.position[0]
        self.estimated_y = self.position[1]

        self.health = health
        self.max_health = max_health

        self.abilities = abilities
        self.wounds = wounds
        
        self.speed = speed
        
        self.y_velocity = 0
        self.x_velocity = 0
        
        self.weight = 1

        self.soul_loss_multiplier = soul_loss_multiplier

        # Größe des Spielers in Welt-Einheiten
        self.width = 1
        self.height = 2

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
    
    def start_jump(self, can_jump):
        if not can_jump:
            return False

        self.y_velocity = self.jump_force
        self.jump_held = True
        self.jump_hold_time = 0.0

        return True

    def update_jump(self, delta_time):
        if (
            self.jump_held
            and self.jump_hold_time < self.max_jump_hold_time
            and self.y_velocity > 0
        ):
            progress = self.jump_hold_time / self.max_jump_hold_time

            # Die zusätzliche Sprungkraft nimmt während des Haltens ab.
            force = self.jump_hold_force * (1.0 - progress)

            self.y_velocity += force * delta_time
            self.jump_hold_time += delta_time
