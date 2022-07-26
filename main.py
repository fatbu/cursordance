import sys
import pygame, pygame.midi, pygame.font
from pygame.constants import *
import traceback

from game_scenes import *
from game_objects import *

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
# screen = pygame.display.set_mode((800, 600))

width, height = pygame.display.get_surface().get_size()

clock = pygame.time.Clock()

pygame.font.init()
pygame.mixer.init()

active_scene = MapScene()

while True:
    # mouse_moved = False
    pressed_keys = pygame.key.get_pressed()
    events = pygame.event.get()
    for event in events:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]    
            if event.key == pygame.K_F4 and alt_pressed:
                pygame.quit()
                sys.exit()

    try:
        active_scene.update(events)
    except Exception as e:
        print(traceback.format_exc())
    screen.fill(pygame.Color('black'))



    try:
        active_scene.render(screen)
    except Exception as e:
        print(traceback.format_exc())


    active_scene = active_scene.next

    if active_scene == None:
        pygame.quit()
        sys.exit()      

    pygame.display.flip()

    clock.tick()
