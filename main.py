import pygame
from time import time

pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("SoulSide")

FPS = 60
TPS = 60

running = True
end = False

latest_time_FPS = time()
latest_time_TPS = time()

while running:

    # INPUT
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end = True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                end = True

    # ZEIT
    current_time = time()

    time_diff_FPS = current_time - latest_time_FPS
    time_diff_TPS = current_time - latest_time_TPS

    # UPDATE
    if time_diff_TPS >= 1 / TPS:
        latest_time_TPS = current_time

        TODO: Hier soll später die logik zum updaten der Spielwelt rein. # type: ignore
        # Hier kommt später:
        # Spieler bewegen
        # Gegner bewegen
        # Physik
        # Räume aktualisieren
        # etc.

    # DRAW
    if time_diff_FPS >= 1 / FPS:
        latest_time_FPS = current_time

        screen.fill((0, 0, 0))

        TODO: Hier soll später die logik zum darstellen der geradigen Spielwelt rein. # type: ignore
        # Hier werden später Räume,
        # Spieler usw. gezeichnet.

        pygame.display.flip()

    if end:
        running = False

pygame.quit()