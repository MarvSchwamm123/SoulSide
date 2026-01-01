import pygame
from rooms.green_land import Green_Land

pygame.init()
screen_width=1000
screen_height=800

screen=pygame.display.set_mode((screen_width, screen_height))
clock=pygame.time.Clock()

current_area=Green_Land(screen_width, screen_height)

player=pygame.Rect(100, 500, 50, 50)
velocity_y=0
gravity=0.7
jump_strength=-13
on_ground=True
jump_pass=False
jump_pass_posib=False 
speed=4

cam_x=0
cam_y=0

running=True

ESCAPE=False
SPACE=False
LEFT=False
RIGHT=False
while running:
    keys=pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        ESCAPE=True
    if keys[pygame.K_SPACE]:
        SPACE=True
    if keys[pygame.K_a]:
        LEFT=True
    if keys[pygame.K_d]:
        RIGHT=True

    if ESCAPE:
        running=False
        ESCAPE=False
    
    if LEFT:
        player.x-=speed
        LEFT=False
    if RIGHT:
        player.x+=speed
        RIGHT=False
    
    if SPACE and on_ground:
        SPACE=False
        on_ground=False
        
        velocity_y=jump_strength
        jump_pass=True
    if jump_pass and not(SPACE):
        jump_pass=False
        velocity_y=0
    velocity_y+=gravity
    player.y+=velocity_y
    for platform in current_area.room1:
        if player.colliderect(platform):
            if velocity_y>0 and player.bottom>platform.top and player.top<platform.top:
                player.bottom=platform.top
                velocity_y=0
                on_ground=True
            elif velocity_y<0 and player.top<platform.bottom and player.bottom>platform.bottom:
                player.top=platform.bottom
                velocity_y=0
            elif player.right>platform.left and player.left<platform.left:
                player.right=platform.left
            elif player.left<platform.right and player.right>platform.right:
                player.left=platform.right

    for border in current_area.room1_cam_restriction_x_borders:
        if cam_x>border:
            cam_x=border
        if cam_x<-border:
            cam_x=-border
    for border in current_area.room1_cam_restriction_y_borders:
        if cam_y>border:
            cam_y=border
        if cam_y<-border:
            cam_y=-border

    for platform in current_area.room1:
        pygame.draw.rect(screen, (200, 200, 200), (platform.x+cam_x, platform.y+cam_y, platform.width, platform.height))
    pygame.draw.rect(screen, (200, 100, 100), (player.x+cam_x, player.y+cam_y, player.width, player.height))
    

pygame.quit()