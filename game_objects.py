from cv2 import resize
import pygame
import math
from pygame.math import *
from utils import *
from pygame.constants import *

glow_radius = 8
glow_step = 1
internal_res = 256

blend_mode = BLEND_ADD

indicator_duration = 400
indicator_size = 8

class HitIndicator:
    def __init__(self, pos, score, tick):
        self.pos = convert_pos(Vector2(pos), internal_res)
        if score == 100:
            self.color = pygame.Color('green')
        elif score == 50:
            self.color = pygame.Color('yellow')
        else:
            self.color = pygame.Color('red')
        self.start_tick = tick
        self.ttl = indicator_duration
        self.size = indicator_size
        self.surf = pygame.Surface((indicator_size*2, indicator_size*2))
        self.surf.set_colorkey((0, 0, 0))
        self.darkener = pygame.Surface((indicator_size*2, indicator_size*2))
        pygame.draw.circle(self.surf, self.color, (indicator_size, indicator_size), indicator_size, 0)
    def update(self, tick):
        self.ttl = indicator_duration-tick+self.start_tick
        self.darkener.set_alpha(255-255*self.ttl/indicator_duration)
        # self.size = indicator_size*self.ttl/indicator_duration
    def render(self, surf):
        draw_surf = self.surf.copy()
        draw_surf.blit(self.darkener, (0, 0))
        surf.blit(draw_surf, self.pos-Vector2(indicator_size, indicator_size), special_flags=blend_mode)
        # pygame.draw.circle(surf, self.color, self.pos, self.size)
        

class GameObject:
    def __init__(self):
        self.alive = True
        pass
    def update(self, tick):
        pass
    def render(self, surf):
        pass
    def live(self):
        self.alive = True
    def die(self):
        self.alive = False

class Circle(GameObject):
    def __init__(self, pos, radius, appear_time, start_time, end_time, color):
        super().__init__()
        self.pos = Vector2(pos)
        self.radius = radius
        self.cur_radius = 0
        self.color = color
        self.appear_time = appear_time
        self.start_time = start_time
        self.end_time = end_time
        self.fade = 0

        surf_size = convert_scalar(self.radius, internal_res)*2+glow_radius*2
        self.surf = pygame.Surface((surf_size, surf_size))
        self.surf.set_colorkey((0, 0, 0))
        opacity_surf = pygame.Surface((surf_size, surf_size))
        opacity_surf.set_colorkey((0, 0, 0))
        for i in range(glow_radius, -1, -glow_step):
            opacity_surf.fill((0, 0, 0, 0))
            opacity_surf.set_alpha(255//(max(1, i)**2))
            pygame.draw.circle(opacity_surf, self.color, (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(self.radius, internal_res)+i, max(1, i)*2)
            self.surf.blit(opacity_surf, (0, 0))
    def update(self, tick, map_mode = False):
        if tick < self.start_time-self.appear_time and map_mode:
            self.die()
            return
        elif tick > self.end_time+self.appear_time:
            self.die()
            return
        else:
            self.live()
        if tick < self.start_time:
            self.cur_radius = lerp(self.radius, 0, (self.start_time-tick)/self.appear_time)
        elif tick >= self.start_time:
            self.cur_radius = self.radius
        
        if tick >= self.end_time:
            self.fade = quadscale(min(1, lerp(0, 1, (tick-self.end_time)/self.appear_time)))
        # elif tick > self.start_time and tick < self.end_time:
        #     self.cur_radius = self.radius
        # elif tick > self.end_time:
        #     self.cur_radius = lerp(self.radius, 0, (tick-self.end_time)/self.expand_time)
    def render(self, surf):
        if self.cur_radius == self.radius and self.fade == 0:
            # surf_size = convert_scalar(self.radius, surf.get_height())*2+glow_radius*2
            # pygame.draw.circle(surf, self.color, convert_pos(self.pos, surf.get_height()), convert_scalar(self.cur_radius, surf.get_height()), 2)
            # opacity_surf = pygame.Surface((surf_size, surf_size)) 
            # opacity_surf.set_colorkey(pygame.Color('black'))
            # for i in range(glow_radius, 0, -glow_step):
            #     opacity_surf.fill(pygame.Color('black'))
            #     opacity_surf.set_alpha(255/i)
            #     pygame.draw.circle(opacity_surf, self.color, (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(self.radius, surf.get_height())+i, i*2)
            #     surf.blit(opacity_surf, convert_pos(self.pos, surf.get_height())+Vector2(-surf_size/2, -surf_size/2))
            # self.surf.set_alpha(255)
            surf_size = surf.get_height()
            surf.blit(self.surf, convert_pos(self.pos, surf_size)+Vector2(-self.surf.get_width()/2, -self.surf.get_height()/2), special_flags=blend_mode)
        elif self.fade > 0:
            # surf_size = convert_scalar(self.radius, surf.get_height())*2+glow_radius*2
            # opacity_surf = pygame.Surface((surf_size, surf_size))
            # opacity_surf.set_colorkey(pygame.Color('black'))
            # opacity_surf.set_alpha(255-255*self.fade)
            # # pygame.draw.circle(opacity_surf, self.color, (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(self.radius, surf.get_height()), 2)
            # surf.blit(opacity_surf, convert_pos(self.pos, surf.get_height())+Vector2(-surf_size/2, -surf_size/2))
            # for i in range(glow_radius, 0, -glow_step):
            #     opacity_surf.fill(pygame.Color('black'))
            #     opacity_surf.set_alpha((255-255*self.fade)/i)
            #     pygame.draw.circle(opacity_surf, self.color, (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(self.radius, surf.get_height())+i, i*2)
            #     surf.blit(opacity_surf, convert_pos(self.pos, surf.get_height())+Vector2(-surf_size/2, -surf_size/2))
            # self.surf.set_alpha(255-255*self.fade)
            surf_size = surf.get_height()
            darken_surf = self.surf.copy()
            darkener = pygame.Surface((surf_size, surf_size))
            darkener.set_alpha(255*self.fade)
            darken_surf.blit(darkener, (0, 0))
            surf.blit(darken_surf, convert_pos(self.pos, surf_size)+Vector2(-self.surf.get_width()/2, -self.surf.get_height()/2), special_flags=blend_mode)
        else:
            # surf_size = convert_scalar(self.radius, surf.get_height())*2+glow_radius*2
            # opacity_surf = pygame.Surface((surf_size, surf_size))
            # opacity_surf.set_colorkey(pygame.Color('black'))
            # # opacity_surf.set_alpha(255*self.cur_radius/self.radius)
            # # pygame.draw.circle(opacity_surf, self.color, (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(self.radius, surf.get_height()), 2)
            # # pygame.draw.circle(opacity_surf, self.color, (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(self.cur_radius, surf.get_height()), 2)
            # # surf.blit(opacity_surf, convert_pos(self.pos, surf.get_height())+Vector2(-surf_size/2, -surf_size/2))
            # for i in range(glow_radius, 0, -glow_step):
            #     opacity_surf.fill(pygame.Color('black'))
            #     opacity_surf.set_alpha(255*(self.cur_radius/self.radius)/i)
            #     pygame.draw.circle(opacity_surf, self.color, (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(self.radius, surf.get_height())+i, i*2)
            #     pygame.draw.circle(opacity_surf, self.color, (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(self.cur_radius, surf.get_height())+i, i*2)
            #     surf.blit(opacity_surf, convert_pos(self.pos, surf.get_height())+Vector2(-surf_size/2, -surf_size/2))
            # self.surf.set_alpha(255*self.cur_radius/self.radius)
            resize_size = convert_scalar(self.cur_radius, surf.get_height())*2+glow_radius*2
            darken_surf = self.surf.copy()
            resized_surf = pygame.transform.smoothscale(self.surf, (resize_size, resize_size)).convert_alpha()
            surf_size = surf.get_height()
            darkener = pygame.Surface((surf_size, surf_size))
            darkener.set_alpha(255-255*quadscale(self.cur_radius/self.radius))
            resized_surf.blit(darkener, (0, 0))
            darken_surf.blit(darkener, (0, 0))
            surf.blit(darken_surf, convert_pos(self.pos, surf_size)+Vector2(-self.surf.get_width()/2, -self.surf.get_height()/2), special_flags=blend_mode)
            surf.blit(resized_surf, convert_pos(self.pos, surf_size)+Vector2(-resized_surf.get_width()/2, -resized_surf.get_height()/2), special_flags=blend_mode)
class Arc(GameObject):
    def __init__(self, pos, angle, arc, start_radius, radius, start_time, lifespan, hit_window, color, hidden = False):
        super().__init__()
        self.pos = Vector2(pos)
        self.color = color
        self.start_radius = start_radius
        self.end_radius = radius
        self.radius = self.start_radius
        self.start_time = start_time
        self.lifespan = lifespan
        self.ttl = lifespan
        self.angle = angle
        self.arc = arc
        self.arc_start = math.radians(angle-arc/2)
        self.arc_end = math.radians(angle+arc/2)
        self.hit_window = hit_window
        self.hidden = hidden

        surf_size = (convert_scalar(self.end_radius, internal_res)*2+glow_radius*2)
        self.surf_size = surf_size
        surf = pygame.Surface((surf_size, surf_size))
        surf.set_colorkey((0, 0, 0))
        opacity_surf = pygame.Surface((surf_size, surf_size))
        opacity_surf.fill((0, 0, 0, 0))
        opacity_surf.set_colorkey((0, 0, 0))
        line_surf = pygame.Surface((internal_res, internal_res))
        opacity_line_surf = pygame.Surface(line_surf.get_size())
        opacity_line_surf.fill((0, 0, 0, 0))
        opacity_line_surf.set_colorkey((0, 0, 0))
        pos = convert_pos(Vector2(self.pos), internal_res)
        point_a = pos+Vector2(convert_scalar(self.end_radius, line_surf.get_width()), 0).rotate_rad(-self.arc_start)
        point_b = pos+Vector2(convert_scalar(self.end_radius, line_surf.get_width()), 0).rotate_rad(-self.arc_end)
        for i in range(glow_radius, -1, -glow_step):
            opacity_surf.fill((0, 0, 0, 0))
            opacity_surf.set_alpha(255//(max(1, i)**2))
            opacity_line_surf.fill((0, 0, 0, 0))
            opacity_line_surf.set_alpha(255//(max(1, i)**2))
            # pygame.draw.line(opacity_line_surf, self.color, pos, point_a, max(1, i)*2)
            # pygame.draw.line(opacity_line_surf, self.color, pos, point_b, max(1, i)*2)
            pygame.draw.line(opacity_line_surf, self.color, pos+(pos-point_a).normalize()*i/2, point_a-(pos-point_a).normalize()*i/2, max(1, i)*2)
            pygame.draw.line(opacity_line_surf, self.color, pos+(pos-point_b).normalize()*i/2, point_b-(pos-point_b).normalize()*i/2, max(1, i)*2)
            line_surf.blit(opacity_line_surf, (0, 0))
            arc_change = math.radians(arc)*i/(4*glow_radius)
            arc_rect = pygame.Rect((glow_radius-i), (glow_radius-i), surf_size-(glow_radius-i)*2, surf_size-(glow_radius-i)*2)
            pygame.draw.arc(opacity_surf, self.color, arc_rect, self.arc_start-arc_change, self.arc_end+arc_change, max(1, i)*2)
            pygame.draw.arc(opacity_surf, self.color, arc_rect.move(1, 0), self.arc_start-arc_change, self.arc_end+arc_change, max(1, i)*2)
            pygame.draw.arc(opacity_surf, self.color, arc_rect.move(0, 1), self.arc_start-arc_change, self.arc_end+arc_change, max(1, i)*2)
            pygame.draw.arc(opacity_surf, self.color, arc_rect.move(-1, 0), self.arc_start-arc_change, self.arc_end+arc_change, max(1, i)*2)
            pygame.draw.arc(opacity_surf, self.color, arc_rect.move(0, -1), self.arc_start-arc_change, self.arc_end+arc_change, max(1, i)*2)

            surf.blit(opacity_surf, (0, 0))
        self.draw_center_point = pos+Vector2(convert_scalar(self.end_radius, internal_res), 0).rotate(-self.angle)
        self.draw_area = surf.get_bounding_rect()
        self.draw_surf = surf
        self.surf_center_point = -Vector2(self.draw_area.topleft)+Vector2(surf.get_size())/2+Vector2(convert_scalar(self.end_radius, internal_res), 0).rotate(-self.angle)
        line_area = line_surf.get_bounding_rect()
        self.line_pos = line_area.topleft
        self.line_surf = pygame.Surface(line_area.size)
        self.line_surf.blit(line_surf, (0, 0), area=line_area)
    def update(self, tick, map_mode = False):
        self.ttl = self.start_time+self.lifespan-tick
        self.radius = lerp(self.start_radius, self.end_radius, (self.lifespan-self.ttl)/self.lifespan)
        if tick < self.start_time and map_mode:
            self.die()
        elif self.ttl <= -self.hit_window['ok']:
            self.die()
        else:
            self.live()
    def render(self, surf):
        if self.ttl < 0:
            return
        rad = convert_scalar(self.radius, surf.get_height())
        end_rad = convert_scalar(self.end_radius, surf.get_height())

        if self.ttl > self.lifespan/2:

            if self.hidden:
                darken_value = 255*quadscale(abs(self.ttl-self.lifespan*3/4)/(self.lifespan/4))
            else:
                darken_value = 255*quadscale((self.ttl-self.lifespan/2)/(self.lifespan/2))

            darken_surf = self.draw_surf.copy()
            darkener = pygame.Surface(self.draw_area.size)
            darkener.set_alpha(darken_value)
            darken_surf.blit(darkener, self.draw_area)
            surf.blit(darken_surf, self.draw_center_point-self.surf_center_point+Vector2(rad-end_rad, 0).rotate(-self.angle), area=self.draw_area, special_flags=blend_mode)


            line_surf = self.line_surf.copy()
            darkener = pygame.Surface(self.line_surf.get_size())
            darkener.set_alpha(darken_value)
            line_surf.blit(darkener, (0, 0))            
            surf.blit(line_surf, self.line_pos, special_flags=blend_mode)

        elif not self.hidden:

            surf.blit(self.draw_surf, self.draw_center_point-self.surf_center_point+Vector2(rad-end_rad, 0).rotate(-self.angle), area=self.draw_area, special_flags=blend_mode)
            surf.blit(self.line_surf, self.line_pos, special_flags=blend_mode)


    def check_hit(self, mouse_movements):
        if len(mouse_movements) < 2:
            return -1
        for i in range(len(mouse_movements)-1):
            a = mouse_movements[i]
            b = mouse_movements[i+1]
            intersects = circle_line_segment_intersection((self.pos.x, self.pos.y), self.end_radius, a, b, False)
            for intersect in intersects:
                angle = (Vector2(intersect)-self.pos).as_polar()[1]
                anglediff = (self.angle - angle + 180 + 360) % 360 - 180
                if abs(anglediff) < self.arc/2:
                    offset = abs(self.ttl)
                    if offset < self.hit_window['good']:
                        self.die()
                        return 100
                    elif offset < self.hit_window['ok']:
                        self.die()
                        return 50
                    
            return -1


class Track(GameObject):
    def __init__(self, start_time, appear_time, end_time, start_pos, start_angle, end_pos, end_angle, circle_radius, hidden = False):
        super().__init__()
        # , center1 = None, radius1 = None, angle1a = None, angle1b = None, center2 = None, radius2 = None, angle2a = None, angle2b = None
        self.start_time = start_time
        self.appear_time = appear_time
        self.end_time = end_time
        self.start_pos = convert_pos(Vector2(start_pos), internal_res)
        self.start_angle = start_angle
        self.end_pos = convert_pos(Vector2(end_pos), internal_res)
        self.end_angle = end_angle

        self.hidden = hidden

        # self.center1 = convert_pos(Vector2(center1), internal_res)
        # self.radius1 = convert_scalar(radius1, internal_res)
        # self.angle1a = angle1a
        # self.angle1b = angle1b
        # self.center2 = convert_pos(Vector2(center2), internal_res)
        # self.radius2 = convert_scalar(radius2, internal_res)
        # self.angle2a = angle2a
        # self.angle2b = angle2b
        self.arc_count = 1
        self.opacity = 0

        self.surf = pygame.Surface((internal_res, internal_res))


        result = biarc_interpolator(self.start_pos, self.start_angle, self.end_pos, self.end_angle)

        a1a = round(180-(Vector2(result['c1'])-Vector2(result['pm'])).as_polar()[1])%360
        a1b = round(180-(Vector2(result['c1'])-Vector2(self.start_pos)).as_polar()[1])%360
        self.arc1start = a1b
        self.arc1end = a1a
        anglediff = (a1a-a1b + 180) % 360 - 180
        if anglediff > 0:
            a1a, a1b = a1b, a1a

        r1 = Vector2(result['pm']).distance_to(Vector2(result['c1']))
        self.arc1pos = Vector2(result['c1'])
        self.arc1radius = r1
        opacity_surf = pygame.Surface(self.surf.get_size())
        opacity_surf.set_colorkey((0, 0, 0))
        for i in range(glow_radius, -1, -glow_step):
            opacity_surf.fill((0, 0, 0, 0))
            opacity_surf.set_alpha(255//(max(1, i)**2))
            arc_change = math.radians(min(360-abs(a1a - a1b), abs(a1a - a1b)))*i/(4*glow_radius)
            arc_rect = pygame.Rect(result['c1'][0]-r1-i/2, result['c1'][1]-r1-i/2, r1*2+i, r1*2+i)
            pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect, math.radians(a1a)-arc_change, math.radians(a1b)+arc_change, max(1, i))
            pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect.move(1, 0), math.radians(a1a)-arc_change, math.radians(a1b)+arc_change, max(1, i))
            pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect.move(0, 1), math.radians(a1a)-arc_change, math.radians(a1b)+arc_change, max(1, i))
            pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect.move(-1, 0), math.radians(a1a)-arc_change, math.radians(a1b)+arc_change, max(1, i))
            pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect.move(0, -1), math.radians(a1a)-arc_change, math.radians(a1b)+arc_change, max(1, i))
            self.surf.blit(opacity_surf, (0, 0))
        
        if result['c2']:
            self.arc_count = 2
            a2a = round(180-(Vector2(result['c2'])-Vector2(result['pm'])).as_polar()[1])%360
            a2b = round(180-(Vector2(result['c2'])-Vector2(self.end_pos)).as_polar()[1])%360
            self.arc2start = a2b
            self.arc2end = a2a
            anglediff = (a2a-a2b + 180) % 360 - 180
            if anglediff > 0:
                a2a, a2b = a2b, a2a
            r2 = Vector2(result['pm']).distance_to(Vector2(result['c2']))
            self.arc2pos = Vector2(result['c2'])
            self.arc2radius = r2
            opacity_surf = pygame.Surface(self.surf.get_size())
            opacity_surf.set_colorkey((0, 0, 0))
            for i in range(glow_radius, -1, -glow_step):
                opacity_surf.fill((0, 0, 0, 0))
                opacity_surf.set_alpha(255//(max(1, i)**2))
                arc_change = math.radians(min(360-abs(a2a - a2b), abs(a2a - a2b)))*i/(4*glow_radius)
                arc_rect = pygame.Rect(result['c2'][0]-r2-i/2, result['c2'][1]-r2-i/2, r2*2+i, r2*2+i)
                pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect, math.radians(a2a)-arc_change, math.radians(a2b)+arc_change, max(1, i))
                pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect.move(1, 0), math.radians(a2a)-arc_change, math.radians(a2b)+arc_change, max(1, i))
                pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect.move(0, 1), math.radians(a2a)-arc_change, math.radians(a2b)+arc_change, max(1, i))
                pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect.move(-1, 0), math.radians(a2a)-arc_change, math.radians(a2b)+arc_change, max(1, i))
                pygame.draw.arc(opacity_surf, pygame.Color('white'), arc_rect.move(0, -1), math.radians(a2a)-arc_change, math.radians(a2b)+arc_change, max(1, i))
                self.surf.blit(opacity_surf, (0, 0))

        circle_surf_size = convert_scalar(circle_radius, internal_res)*2+glow_radius*2
        circle_surf = pygame.Surface((circle_surf_size, circle_surf_size))
        circle_surf.set_colorkey((0, 0, 0))
        opacity_surf = pygame.Surface((circle_surf_size, circle_surf_size))
        opacity_surf.set_colorkey((0, 0, 0))
        for i in range(glow_radius, -1, -glow_step):
            opacity_surf.fill((0, 0, 0, 0))
            opacity_surf.set_alpha(255//(max(1, i)**2))
            pygame.draw.circle(opacity_surf, pygame.Color('white'), (opacity_surf.get_width()/2, opacity_surf.get_height()/2), convert_scalar(circle_radius, internal_res)+i, max(1, i)*2)
            circle_surf.blit(opacity_surf, (0, 0))
        
        self.circle_surf = circle_surf
        self.circle_pos = self.start_pos
        self.circle_radius = convert_scalar(circle_radius, internal_res)
    def update(self, tick, map_mode = False):
        if tick < self.start_time-self.appear_time and map_mode:
            self.die()
            return
        elif tick > self.end_time:
            self.die()
            return
        else:
            self.live()
        

        if tick > self.start_time - self.appear_time and tick < self.start_time:
            self.opacity = quadscale((self.start_time-tick)/(self.appear_time))
            self.circle_pos = self.start_pos
        elif tick >= self.start_time:
            # if self.hidden:
            #     self.opacity = max(0, (tick-self.start_time)/(self.end_time-self.start_time))
            # else:
                # self.opacity = 1
            self.opacity = 1
            if self.arc_count == 1:
                anglediff = (180+self.arc1start-self.arc1end)%360-180
                self.circle_pos = self.arc1pos+Vector2(self.arc1radius, 0).rotate(-self.arc1start+lerp(0, anglediff, (tick-self.start_time)/(self.end_time-self.start_time)))
            elif self.arc_count == 2:
                anglediff1 = (180+self.arc1start-self.arc1end)%360-180
                anglediff2 = (180+self.arc2start-self.arc2end)%360-180
                arc1length = self.arc1radius*abs(anglediff1)
                arc2length = self.arc2radius*abs(anglediff2)
                arc_cutoff = lerp(self.start_time, self.end_time, arc1length/(arc1length+arc2length))
                if tick < arc_cutoff:
                    self.circle_pos = self.arc1pos+Vector2(self.arc1radius, 0).rotate(-self.arc1start+lerp(0, anglediff1, 1-(arc_cutoff-tick)/(arc_cutoff-self.start_time)))
                else:
                    self.circle_pos = self.arc2pos+Vector2(self.arc2radius, 0).rotate(-self.arc2start+lerp(0, anglediff2, 1-(tick-arc_cutoff)/(self.end_time-arc_cutoff)))
                    


    def render(self, surf):
        if self.opacity < 1:
            darken_surf = self.surf.copy()
            darkener = pygame.Surface(darken_surf.get_size())
            darkener.set_alpha(255*self.opacity)
            darken_surf.blit(darkener, (0, 0))
            surf.blit(darken_surf, (0, 0), special_flags=blend_mode)

            darken_surf = self.circle_surf.copy()
            darkener = pygame.Surface(darken_surf.get_size())
            darkener.set_alpha(255*self.opacity)
            darken_surf.blit(darkener, (0, 0))
            surf.blit(darken_surf, self.circle_pos-Vector2(darken_surf.get_size())/2, special_flags=blend_mode)
        else:
            surf.blit(self.surf, (0, 0), special_flags=blend_mode)
            surf.blit(self.circle_surf, self.circle_pos-Vector2(self.circle_surf.get_size())/2, special_flags=blend_mode)

    def check_hit(self, mouse_pos):
        pos = convert_pos(Vector2(mouse_pos), internal_res)
        if pos.distance_to(self.circle_pos) <= self.circle_radius:
            return 1
        return -1