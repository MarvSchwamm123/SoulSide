import pygame
import numpy as np

pygame.init()

# Fenster
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Komplexe Funktion")

clock = pygame.time.Clock()

# Farben
BG = (20, 20, 25)
AXIS = (100, 100, 100)
CURVE = (80, 200, 255)
TEXT = (240, 240, 240)

font = pygame.font.SysFont("Arial", 20)

# --------------------------------------------------
# Deine Formel:
#
# y = ((z^2 + 1)/(2*z))^(2/3) + 2*i/(z - 1/z)
# --------------------------------------------------

def funktion(z):
    return ((z**2 + 1) / (2*z))**(2/3) + 2j / (z - 1/z)


# z-Werte
# z darf hier NICHT 0, 1 oder -1 sein,
# weil dort Divisionen durch 0 entstehen.
z_values = np.linspace(-10, 10, 30000)

points = []

for z in z_values:
    if abs(z) < 0.02:
        continue

    if abs(z - 1) < 0.02 or abs(z + 1) < 0.02:
        continue

    try:
        y = funktion(z)

        real = y.real
        imag = y.imag

        # Extreme Werte ausblenden
        if abs(real) < 50 and abs(imag) < 50:
            points.append((real, imag))

    except:
        pass


# Zoom
SCALE = 80

# Mittelpunkt
CX = WIDTH // 2
CY = HEIGHT // 2


def to_screen(x, y):
    screen_x = CX + x * SCALE
    screen_y = CY - y * SCALE
    return int(screen_x), int(screen_y)


running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # Mausrad zum Zoomen
        if event.type == pygame.MOUSEWHEEL:
            SCALE *= 1.1 ** event.y

            SCALE = max(5, min(SCALE, 500))


    screen.fill(BG)

    # Achsen
    pygame.draw.line(
        screen,
        AXIS,
        (0, CY),
        (WIDTH, CY),
        1
    )

    pygame.draw.line(
        screen,
        AXIS,
        (CX, 0),
        (CX, HEIGHT),
        1
    )

    # Kurve
    last_point = None

    for x, y in points:

        sx, sy = to_screen(x, y)

        # Nur zeichnen, wenn Punkt im Fenster liegt
        if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:

            if last_point is not None:

                # Verhindert Linien quer durchs Bild
                if abs(sx - last_point[0]) < WIDTH // 2:
                    pygame.draw.line(
                        screen,
                        CURVE,
                        last_point,
                        (sx, sy),
                        2
                    )

            last_point = (sx, sy)

        else:
            last_point = None


    # Beschriftungen
    text1 = font.render(
        "Re(y)",
        True,
        TEXT
    )

    text2 = font.render(
        "Im(y)",
        True,
        TEXT
    )

    formula = font.render(
        "y = ((z² + 1)/(2z))^(2/3) + 2i/(z - 1/z)",
        True,
        TEXT
    )

    screen.blit(
        text1,
        (WIDTH - 70, CY + 10)
    )

    screen.blit(
        text2,
        (CX + 10, 10)
    )

    screen.blit(
        formula,
        (20, 20)
    )

    pygame.display.flip()
    clock.tick(60)


pygame.quit()