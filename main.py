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

# cursor_size = 64
# cursor_surf = pygame.Surface((cursor_size, cursor_size))
# cursor_surf.set_colorkey(pygame.Color('black'))
# pygame.draw.circle(cursor_surf, pygame.Color('white'), (cursor_size/2, cursor_size/2), cursor_size/2, 0)
# pygame.draw.circle(cursor_surf, pygame.Color('black'), (cursor_size/2, cursor_size/2), cursor_size*3/8, cursor_size//8)
# pygame.mouse.set_cursor((cursor_size//2, cursor_size//2), cursor_surf)

# trail_opacity = 0.1
# trail_length = 32
# cursor_trail_surf = pygame.Surface((cursor_size, cursor_size))
# cursor_trail_surf.set_colorkey(pygame.Color('black'))
# pygame.draw.circle(cursor_trail_surf, pygame.Color('white'), (cursor_size/2, cursor_size/2), cursor_size/2, 0)

# mouse_hist = []


# last_pos = pygame.mouse.get_pos()

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
            
        # if event.type == MOUSEMOTION:
        #     mouse_moved = True
        #     mouse_hist.append(event.pos)
        #     if len(mouse_hist) > trail_length:
        #         mouse_hist.pop(0)

    # if not mouse_moved:
    #     mouse_hist = mouse_hist[1:]

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

    # trail_count = 0
    # for pos in mouse_hist:
    #     cursor_trail_surf.set_alpha(255*trail_opacity*trail_count/len(mouse_hist))
    #     screen.blit(cursor_trail_surf, (pos[0]-cursor_size/2, pos[1]-cursor_size/2))
    #     trail_count += 1        

    pygame.display.update()

    clock.tick()
