import pygame
from rooms.green_land import Green_Land

pygame.init()
screen_width = 1000
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()

current_area=Green_Land(screen_width, screen_height)

player = pygame.Rect(100, 500, 50, 50)
velocity_y = 0
gravity = 0.7
jump_strength = -12
on_ground = True
jump_pass = False
jump_pass_posib = False

speed = 4

running = True
while running:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if keys[pygame.K_ESCAPE]:
        running = False

    # --- Bewegung horizontal ---
    if keys[pygame.K_a]:
        player.x -= speed
    if keys[pygame.K_d]:
        player.x += speed

    # --- Springen ---
    if keys[pygame.K_SPACE]:
        if on_ground:
            on_ground = False
            velocity_y = jump_strength
            jump_pass = True
            jump_pass_posib = False
        if not on_ground and jump_pass:
            velocity_y -= 0.3
            jump_pass_posib = True
    if not jump_pass_posib:
        jump_pass = False

    # --- Schwerkraft ---
    velocity_y += gravity
    player.y += velocity_y

    # --- Kollisionserkennung ---
    on_ground = False
    for platform in current_area.room1:
        if player.colliderect(platform):
            # Spieler fällt AUF die Plattform
            if velocity_y > 0 and player.bottom > platform.top and player.top < platform.top:
                player.bottom = platform.top
                velocity_y = 0
                on_ground = True
            # Spieler springt GEGEN die Unterseite der Plattform
            elif velocity_y < 0 and player.top < platform.bottom and player.bottom > platform.bottom:
                player.top = platform.bottom
                velocity_y = 0
            # Seitliche Kollisionen (links / rechts)
            elif player.right > platform.left and player.left < platform.left:
                player.right = platform.left
            elif player.left < platform.right and player.right > platform.right:
                player.left = platform.right

    # --- Zeichnen ---
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (200, 100, 100), player)
    for platform in current_area.room1:
        pygame.draw.rect(screen, (100, 200, 100), platform, 5)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
