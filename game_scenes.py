from re import U
import time
import tkinter
import tkinter.filedialog
from turtle import pos
import pygame
from pygame.constants import *
from game_objects import *
import random
import pygame_textinput
from pydub import AudioSegment
from utils import *
from os import path
import sys
import os

cursor_size = 64
cursor_surf = pygame.Surface((cursor_size, cursor_size))
cursor_surf.set_colorkey((0, 0, 0))
pygame.draw.circle(cursor_surf, (255, 255, 255), (cursor_size/2, cursor_size/2), cursor_size/2, 0)
pygame.draw.circle(cursor_surf, (0, 0, 0), (cursor_size/2, cursor_size/2), cursor_size*7/16, cursor_size//8)

trail_time = 250
cursor_trail = pygame.Surface((8, 8))
cursor_trail.set_colorkey((0, 0, 0))
pygame.draw.circle(cursor_trail, pygame.Color('white'), (4, 4), 4, 0)



font_size = 32
font_file = 'fonts/Pixolletta8px.ttf'

beat_size = 128

def prompt_file():
    """Create a Tk file dialog and cleanup when finished"""
    pygame.display.set_mode((0, 0))
    top = tkinter.Tk()
    top.withdraw()  # hide window
    file_name = tkinter.filedialog.askopenfilename(parent=top)
    top.destroy()
    pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    return file_name

pygame.mixer.init()
pygame.mixer.music.set_volume(0.25)

hit_sound = pygame.mixer.Sound(resource_path('sounds/hit.wav'))
hit_sound.set_volume(0.1)

map_hit = 20

arc_distance = 0.5

color_list = [(255, 64, 64), (255, 128, 64), (255, 255, 64), (128, 255, 64), (64, 255, 64), (64, 255, 128), (64, 255, 255), (64, 128, 255), (64, 64, 255), (128, 64, 255), (255, 64, 255), (255, 64, 128)]
colors = []
for i in range(0, len(color_list), 3):
    colors.append(color_list[i])
for i in range(1, len(color_list), 3):
    colors.append(color_list[i])
for i in range(2, len(color_list), 3):
    colors.append(color_list[i])

def get_color(num):
    return colors[num % len(colors)]

class BaseScene:
    def __init__(self):
        self.next = self
    def update(self, events):
        pass
    def render(self, screen):
        pass
    def switch(self, next_scene):
        self.next = next_scene


class TestScene(BaseScene):
    def __init__(self):
        BaseScene.__init__(self)
        self.last_pos = pygame.mouse.get_pos()
        self.objects = []
        self.objects.append(Circle((0, 0), 0.5, 500, 500, 100000000000000, get_color(random.randint(0, 6))))
        self.width, self.height = pygame.display.get_surface().get_size()

    def update(self, events):
        tick_time = pygame.time.get_ticks()

        if len(self.objects) == 1:
            self.objects.append(Arc(self.objects[0].pos, random.randint(0, 360), 60, self.objects[0].radius+arc_distance, self.objects[0].radius, pygame.time.get_ticks(), 500, {'good':50, 'ok':100}, self.objects[0].color))

        cur_pos = self.last_pos

        for event in events:
            if event.type == MOUSEMOTION:
                if event.pos != self.last_pos:
                    cur_pos = event.pos
        
        keep_objects = []
        first_arc = True
        for object in self.objects:
            object.update(tick_time)

            if isinstance(object, Arc) and first_arc:
                if self.last_pos != cur_pos:
                    result = object.check_hit([((self.last_pos[0]*2-self.width)/self.height, -(self.last_pos[1]*2-self.height)/self.height), ((cur_pos[0]*2-self.width)/self.height, -(cur_pos[1]*2-self.height)/self.height)])
                    if result > 0:
                        pygame.mixer.Sound.play(hit_sound)
                    self.last_pos = cur_pos
                first_arc = False

            if object.alive:
                keep_objects.append(object)
        
        self.objects = keep_objects

    def render(self, screen):
        playfield = pygame.Surface((internal_res, internal_res))
        
        for object in self.objects:
            object.render(playfield)

        screen.blit(pygame.transform.scale(playfield, (self.height, self.height)), ((self.width-self.height)/2, 0))

        pygame.draw.rect(screen, pygame.Color('white'), ((self.width-self.height)/2, 0, self.height, self.height), 4)


import pygame_textinput
import pickle

class InputField:
    def __init__(self, label, font, pos):
        self.font = font
        self.label = label
        self.labelsurf = self.font.render(label+' ', True, pygame.Color('white'))
        self.input_box = pygame_textinput.TextInputVisualizer(font_color=pygame.Color('white'), font_object=self.font, cursor_color=pygame.Color('white'))
        self.pos = pos
        self.active = False
    def update(self, events):
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                x, y = event.pos
                if x > self.pos[0] and x < self.pos[0] + self.labelsurf.get_width() + self.input_box.surface.get_width() and y > self.pos[1] and y < self.pos[1] + self.labelsurf.get_height():
                    self.active = True
                else:
                    self.active = False
                    try:
                        float(self.get_value())
                    except ValueError:
                        self.set_value('0')
        self.input_box.cursor_visible = self.active

        if self.active:
            self.input_box.update(events)

    def render(self, screen):
        rect = screen.blit(self.labelsurf, self.pos)
        screen.blit(self.input_box.surface, (self.pos[0]+rect[2], rect[1]))
    def set_value(self, val):
        self.input_box.value = val
    def get_value(self):
        return self.input_box.value

class MapScene(BaseScene):
    def __init__(self, file_path = None):
        BaseScene.__init__(self)
        self.last_pos = pygame.mouse.get_pos()
        self.objects = []
        self.width, self.height = pygame.display.get_surface().get_size()
        self.fields = []
        self.grid = 0.1
        self.divisor = 4
        self.anglesnap = 3
        self.play_pos = 0
        self.font = pygame.font.Font(resource_path(font_file), font_size)
        self.side_objects = []
        self.last_hit = 0

        if file_path == None:
            file_path = prompt_file()
            if len(file_path) == 0:
                pygame.quit()
                sys.exit()

        self.music_file_path = ''
        self.map_file_path = ''

        if file_path[-4:] == '.map':
            self.music_file_path = file_path[:-4]
            self.map_file_path = file_path
        else:
            self.music_file_path = file_path
            self.map_file_path = self.music_file_path+'.map'

        if self.music_file_path[-4:] != '.ogg':
            audio_file = AudioSegment.from_file(self.music_file_path)
            self.music_file_path = self.music_file_path[:-4]+'.ogg'
            self.map_file_path = self.music_file_path[:-4]+'.ogg.map'
            audio_file.export(self.music_file_path, format='ogg')
            

        self.duration = pygame.mixer.Sound(self.music_file_path).get_length()*1000

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        pygame.mixer.music.load(self.music_file_path)

        try:
            with open(self.map_file_path, 'rb+') as map_file:
                self.map = pickle.load(map_file)
        except:
            self.map = {}
            open(self.map_file_path, 'x').close()
            self.save()

        if 'objects' not in self.map:
            self.map['objects'] = []
            self.save()

        input_fields = ['offset', 'bpm', 'approach', 'precision', 'width']

        x_pos = font_size
        y_pos = font_size

        for field in input_fields:
            f = InputField(field, self.font, (x_pos, y_pos))
            if field in self.map:
                f.set_value(self.map[field])
            else:
                f.set_value('0')
            self.fields.append(f)
            y_pos += font_size

    def snap(self, n):
        if self.grid == 0:
            return n
        grid = self.height*self.grid/2
        return grid*round(n/grid)
    
    def snap_pos(self, pos):
        if self.grid == 0:
            return pos
        grid = self.height*self.grid/2
        x_offset = (self.width-self.height)/2
        return (grid*round((pos[0]-x_offset)/grid)+x_offset, grid*round(pos[1]/grid))

    def get_object_time(self, object):
        if object['type'] == 'circle' or object['type'] == 'track':
            return object['start_time']
        elif object['type'] == 'arc':
            return object['start_time']+object['lifespan']
        return -1

    def save(self):
        for field in self.fields:
            self.map[field.label] = field.get_value()

        if 'objects' in self.map:
            self.map['objects'].sort(key=self.get_object_time)

        with open(self.map_file_path, 'rb+') as map_file:
            pickle.dump(self.map, map_file)
    
    def add_object(self, obj, time):
        if len(self.map['objects']) > 0:
            for i in range(len(self.map['objects'])):
                object = self.map['objects'][i]
                if (object['start_time'] == time or object['start_time'] == obj['start_time']) and object['type'] == obj['type']:
                    self.map['objects'][i] == obj
                    return
                if object['type'] == 'circle' and object['start_time'] > time:
                    break
                if object['type'] == 'track' and object['start_time'] > time:
                    break
                if object['type'] == 'arc' and object['start_time']+object['lifespan'] > time:
                    break
            self.map['objects'].insert(i+1, obj)
        else:
            self.map['objects'].append(obj)

    def del_object(self, index):
        if len(self.map['objects']) > index:
            deleted = self.map['objects'].pop(index)
            if deleted['type'] == 'circle':
                keep_objects = []
                for i, object in enumerate(self.map['objects']):
                    if not(object['type'] == 'arc' and object['start_time']+object['lifespan'] >= deleted['start_time'] and object['start_time'] < deleted['end_time'] and object['radius'] == deleted['radius'] and object['pos'] == deleted['pos']):
                        keep_objects.append(object)
                self.map['objects'] = keep_objects
                
    def del_near_cursor_side(self):
        pos = pygame.mouse.get_pos()
        for object in self.side_objects:
            if object['type'] == 'circle' and Vector2(pos).distance_to(object['pos']) <= object['radius']:
                self.del_object(object['index'])
            elif object['type'] == 'arc' and abs(pos[1]-object['a'][1]) <= 2 and object['a'][0] < pos[0] < object['b'][0]:
                self.del_object(object['index'])
            elif object['type'] == 'track' and abs(pos[0]-object['a'][0]) <= 2 and object['a'][1] < pos[1] < object['b'][1]:
                self.del_object(object['index'])

    def get_circle_color(self, index):
        count = 0
        for i, object in enumerate(self.map['objects']):
            if i == index:
                break
            if object['type'] == 'circle':
                count += 1
        return get_color(count)

    def get_arc_color(self, index):
        object = self.map['objects'][index]
        for i, obj in enumerate(self.map['objects']):
            if obj['type'] == 'circle' and object['start_time']+object['lifespan'] >= obj['start_time'] and object['start_time'] < obj['end_time'] and object['radius'] == obj['radius'] and object['pos'] == obj['pos']:
                return self.get_circle_color(i)
        
        return pygame.Color('white')

    def get_pos(self):
        pos = round(self.play_pos)+pygame.mixer.music.get_pos()
        return max(0, pos)

    def approach(self):
        return 200+float(self.map['approach'])*100

    def hit_window(self):
        return {'good': float(self.map['precision'])*10, 'ok': float(self.map['precision'])*20}

    def arc_width(self):
        return float(self.map['width'])/20

    def get_closest_arc_index(self):
        for i, object in reversed(list(enumerate(self.map['objects']))):
            if object['type'] == 'arc' and object['start_time']+object['lifespan'] < self.get_pos():
                return i
        return -1
    def get_closest_circle_index(self):
        possible_circles = []
        possible_indexes = []
        for i, object in enumerate(self.map['objects']):
            if object['type'] == 'circle' and object['start_time'] <= self.get_pos() and self.get_pos() < object['end_time']:
                possible_circles.append(object)
                possible_indexes.append(i)
        if len(possible_circles) > 0:
            min_dist = 1000000
            min_index = 0
            for circle_index in range(len(possible_circles)):
                circle = possible_circles[circle_index]
                circle_pos = convert_pos(Vector2(circle['pos']), self.height)+Vector2((self.width-self.height)/2, 0)
                dist = abs(Vector2(pygame.mouse.get_pos()).distance_to(circle_pos)-convert_scalar(circle['radius'], self.height))
                if dist < min_dist:
                    min_dist = dist
                    min_index = circle_index
            return possible_indexes[min_index]
        return -1
    def update(self, events):
        for field in self.fields:
            field.update(events)
        pressed_keys = pygame.key.get_pressed()
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    x_end = (self.width+self.height)/2 + (self.width-self.height)/8
                    if x_end<event.pos[0]<x_end+16:
                        playing = pygame.mixer.music.get_busy()
                        self.play_pos = self.duration*pygame.mouse.get_pos()[1]/self.height
                        pygame.mixer.music.play(start=self.play_pos/1000)
                        if not playing:
                            pygame.mixer.music.stop()
                elif event.button == 3:
                    self.del_near_cursor_side()
                elif event.button == 4 or event.button == 5:
                    playing = pygame.mixer.music.get_busy()
                    mspb = 60000/float(self.map['bpm'])
                    min_offset = float(self.map['offset'])%mspb
                    mspb /= self.divisor
                    music_pos = self.get_pos()
                    if event.button == 4:
                        self.play_pos = max(0, min_offset+mspb*round((music_pos-min_offset)/mspb)-mspb)
                        pygame.mixer.music.play(start=self.play_pos/1000)
                        if not playing:
                            pygame.mixer.music.stop()
                    if event.button == 5:
                        self.play_pos = min(self.duration, min_offset+mspb*round((music_pos-min_offset)/mspb)+mspb)
                        pygame.mixer.music.play(start=self.play_pos/1000)
                        if not playing:
                            pygame.mixer.music.stop()

                    self.last_hit = 0

            if event.type == MOUSEBUTTONUP:
                pass
            if event.type == MOUSEMOTION:
                if pygame.mouse.get_pressed()[2]:
                    self.del_near_cursor_side()
            if event.type == KEYDOWN:
                ctrl_pressed = pressed_keys[pygame.K_LCTRL] or \
                              pressed_keys[pygame.K_RCTRL]
                if event.key == K_w:
                    self.object_preview = {'type':'circle', 'pos':self.snap_pos(pygame.mouse.get_pos()), 'radius':0}
                if event.key == K_e:
                    arc_index = self.get_closest_arc_index()
                    if arc_index > -1:
                        arc = self.map['objects'][arc_index]
                        initial_pos = convert_pos(Vector2(arc['pos']), self.height)+Vector2((self.width-self.height)/2, 0)
                        self.object_preview = {'type':'track', 'start_time': arc['start_time']+arc['lifespan'], 'start_pos':tuple(initial_pos+Vector2(convert_scalar(arc['radius'], self.height), 0).rotate(-arc['angle'])), 'start_angle':-arc['angle']}
                if event.key == K_r:
                    circle_index = self.get_closest_circle_index()
                    if circle_index > -1:
                        circle = self.map['objects'][circle_index]
                        self.object_preview = {'type':'arc', 'pos':tuple(convert_pos(Vector2(circle['pos']), self.height)+Vector2((self.width-self.height)/2, 0)), 'radius':convert_scalar(circle['radius'], self.height)}
                if event.key == K_g:
                    if self.grid == 0:
                        self.grid = 0.1
                    else:
                        self.grid = 0
                if event.key == K_f:
                    circle_index = self.get_closest_circle_index()
                    if circle_index >= 0:
                        self.map['objects'][circle_index]['end_time'] = self.get_pos()
                if event.key == K_d:
                    circle_index = self.get_closest_circle_index()
                    if circle_index >= 0:
                        self.map['objects'][circle_index]['end_time'] = self.duration
                if event.key == K_s and ctrl_pressed:
                    self.save()
                if event.key == K_SPACE:
                    if pygame.mixer.music.get_busy():

                        mspb = 60000/float(self.map['bpm'])
                        min_offset = float(self.map['offset'])%mspb
                        mspb /= self.divisor

                        self.play_pos = max(0, min_offset+mspb*round((self.get_pos()-min_offset)/mspb))
                        pygame.mixer.music.play(start=self.play_pos/1000)
                        pygame.mixer.music.stop()
                    else:
                        pygame.mixer.music.play(start=self.play_pos/1000)
                if event.key == K_p:
                    self.save()
                    self.next = PlayScene(self.map_file_path)
            if event.type == KEYUP:
                if event.key == K_w:
                    circle_obj = self.object_preview
                    if circle_obj['radius'] > 0:
                        x, y = circle_obj['pos']
                        circle = {}
                        circle['type'] = 'circle'
                        circle['pos'] = ((x*2 - self.width) / self.height, (-y*2 + self.height) / self.height)
                        circle['radius'] = circle_obj['radius']*2/self.height
                        circle['appear_time'] = self.approach()
                        circle['start_time'] = self.get_pos()
                        circle['end_time'] = int(self.duration*1000)
                        self.add_object(circle, self.get_pos())
                        
                if event.key == K_r:
                    if hasattr(self, 'object_preview'):
                        arc_obj = self.object_preview
                        x, y = arc_obj['pos']
                        arc = {}
                        arc['type'] = 'arc'
                        arc['pos'] = ((x*2 - self.width) / self.height, (-y*2 + self.height) / self.height)
                        arc['radius'] = arc_obj['radius']*2/self.height
                        arc['angle'] = -(360/(4*self.anglesnap))*round(((Vector2(x, y)-Vector2(pygame.mouse.get_pos())).as_polar()[1])/(360/(4*self.anglesnap)))+180
                        arc['arc'] = math.degrees(2*self.arc_width()/arc['radius'])
                        arc['lifespan'] = self.approach()
                        arc['start_time'] = self.get_pos()-arc['lifespan']
                        self.add_object(arc, self.get_pos())
                if event.key == K_e:
                    if hasattr(self, 'object_preview'):
                        start_pos = Vector2(self.object_preview['start_pos'])
                        start_angle = (self.object_preview['start_angle'])%360
                        closest_circle = self.map['objects'][self.get_closest_circle_index()]
                        circle_pos = convert_pos(Vector2(closest_circle['pos']), self.height)+Vector2((self.width-self.height)/2, 0)
                        end_angle = (360/(4*self.anglesnap))*round(((Vector2(pygame.mouse.get_pos())-circle_pos).as_polar()[1])/(360/(4*self.anglesnap)))
                        end_pos = circle_pos+Vector2(convert_scalar(closest_circle['radius'], self.height), 0).rotate(end_angle)
                        
                        interfere_arc = False
                        for object in self.map['objects']:
                            if object['type'] == 'arc' and object['start_time']+object['lifespan'] == self.get_pos():
                                interfere_arc = True
                                break
                            elif object['start_time'] > self.get_pos():
                                break
                        if not interfere_arc and start_angle%180 != end_angle%180:
                            track = {}
                            track['type'] = 'track'
                            track['start_pos'] = ((start_pos.x*2 - self.width) / self.height, (-start_pos.y*2 + self.height) / self.height)
                            track['start_angle'] = start_angle
                            track['end_pos'] = ((end_pos.x*2 - self.width) / self.height, (-end_pos.y*2 + self.height) / self.height)
                            track['end_angle'] = end_angle
                            track['start_time'] = self.object_preview['start_time']
                            track['end_time'] = self.get_pos()
                            track['appear_time'] = self.approach()
                            self.add_object(track, self.get_pos())

                if hasattr(self, 'object_preview'):
                    del self.object_preview

        self.side_objects = []

    def render(self, screen):
        pos = self.get_pos()

        playfield = pygame.Surface((internal_res, internal_res))

        for field in self.fields:
            field.render(screen)


        mspb = 60000/float(self.map['bpm'])
        min_offset = float(self.map['offset'])%mspb

        num_beats = self.height//beat_size

        x_start = (self.width+self.height)/2
        x_end = (self.width+self.height)/2 + (self.width-self.height)/8

        y_mid = self.height/2
        for i in range(-num_beats, num_beats):
            y_offset = y_mid + i * beat_size - beat_size*((pos-min_offset)%mspb)/mspb

            pygame.draw.line(screen, pygame.Color('grey30'), (x_start, y_offset), (x_end, y_offset), 2)
            for j in range(1, self.divisor):
                pygame.draw.line(screen, pygame.Color('grey30'), (x_start, beat_size*j/self.divisor+y_offset), (x_end-(x_end-x_start)/2, beat_size*j/self.divisor+y_offset), 1)


        pygame.draw.line(screen, pygame.Color('white'), (x_start, self.height/2), (x_end, self.height/2), 2)


        for i in range(-num_beats, num_beats):
            y_offset = y_mid + i * beat_size - beat_size*((pos-min_offset)%mspb)/mspb
            cur_beat = min_offset+mspb*math.floor((pos-min_offset)/mspb)+i*mspb

            for k in range(len(self.map['objects'])):
                cur_object = self.map['objects'][k]
                if cur_object['type'] == 'circle':
                    if cur_object['start_time'] >= cur_beat and cur_object['start_time'] < cur_beat+mspb:
                        y_offset_offset = beat_size*round(self.divisor*((cur_object['start_time']-min_offset)%mspb)/mspb)/self.divisor
                        circle_pos = ((x_start+x_end)/2, y_offset + y_offset_offset)
                        circle_radius = beat_size/(self.divisor*2)
                        pygame.draw.circle(screen, self.get_circle_color(k), circle_pos, circle_radius, 2)

                        self.side_objects.append({'type':'circle', 'pos':circle_pos, 'radius': circle_radius, 'index': k})

                elif cur_object['type'] == 'arc':
                    if cur_object['start_time']+cur_object['lifespan'] >= cur_beat and cur_object['start_time']+cur_object['lifespan'] < cur_beat+mspb:
                        y_offset_offset = beat_size*round(self.divisor*((cur_object['start_time']+cur_object['lifespan']-min_offset)%mspb)/mspb)/self.divisor

                        point_a = (x_start+(x_end-x_start)/4, y_offset + y_offset_offset)
                        point_b = (x_start+(x_end-x_start)*3/4, y_offset + y_offset_offset)
                        pygame.draw.line(screen, self.get_arc_color(k), point_a, point_b, 2)

                        self.side_objects.append({'type':'arc', 'a':point_a, 'b':point_b, 'index': k})

                elif cur_object['type'] == 'track':
                    if cur_object['start_time'] >= cur_beat and cur_object['start_time'] < cur_beat+mspb:
                        y_offset_offset = beat_size*round(self.divisor*((cur_object['start_time']-min_offset)%mspb)/mspb)/self.divisor
                        line_length = beat_size*(cur_object['end_time']-cur_object['start_time'])/mspb

                        point_a = (x_start+(x_end-x_start)/2, y_offset + y_offset_offset)
                        point_b = (x_start+(x_end-x_start)/2, y_offset + y_offset_offset + line_length)
                        pygame.draw.line(screen, pygame.Color('white'), point_a, point_b, 2)

                        self.side_objects.append({'type':'track', 'a':point_a, 'b':point_b, 'index': k })

        line_length = self.get_pos()*self.height/self.duration
        pygame.draw.rect(screen, pygame.Color('white'), (x_end, 0, 16, line_length), 0)
        pygame.draw.rect(screen, pygame.Color('white'), (x_end, 0, 16, self.height), 1)


        play_time = str(self.get_pos())+'/'+str(int(self.duration))
        play_time_surf = self.font.render(play_time, True, pygame.Color('white'))
        screen.blit(play_time_surf, (self.width-play_time_surf.get_width()-font_size, font_size))

        if self.grid > 0:
            for i in range(1, int(2/self.grid)):
                pygame.draw.line(playfield, pygame.Color('grey30'), (0, internal_res*i/(2/self.grid)), (internal_res, internal_res*i/(2/self.grid)), 1)
                pygame.draw.line(playfield, pygame.Color('grey30'), (internal_res*i/(2/self.grid), 0), (internal_res*i/(2/self.grid), internal_res), 1)

        for i, object in enumerate(self.map['objects']):
            if object['type'] == 'circle' and object['start_time']-object['appear_time'] <= pos < object['end_time']+object['appear_time']:
                obj = Circle(object['pos'], object['radius'], object['appear_time'], object['start_time'], object['end_time'], self.get_circle_color(i))
                obj.update(pos, True)
                if obj.alive:
                    if self.anglesnap > 0:
                        circle_pos = convert_pos(Vector2(obj.pos), internal_res)
                        circle_rad = convert_scalar(obj.radius, internal_res)
                        for i in range(4*self.anglesnap):
                            pygame.draw.line(playfield, pygame.Color('grey30'), circle_pos, circle_pos+Vector2(circle_rad, 0).rotate(360*i/(self.anglesnap*4)), 1)
                    obj.render(playfield)
            elif object['type'] == 'arc' and object['start_time'] <= pos < object['start_time']+self.approach():
                obj = Arc(object['pos'], object['angle'], object['arc'], object['radius']+arc_distance, object['radius'], object['start_time'], self.approach(), self.hit_window(), self.get_arc_color(i))
                obj.update(pos, True)

                if pygame.mixer.music.get_busy() and abs(obj.start_time+obj.lifespan - self.get_pos()) < map_hit and abs(self.get_pos() - self.last_hit) > map_hit*2:
                    pygame.mixer.Sound.play(hit_sound)
                    self.last_hit = self.get_pos()

                if obj.alive:
                    obj.render(playfield)
            
            elif object['type'] == 'track' and object['start_time']-object['appear_time'] <= pos < object['end_time']:
                obj = Track(object['start_time'], object['appear_time'], object['end_time'], object['start_pos'], object['start_angle'], object['end_pos'], object['end_angle'], self.arc_width())
                obj.update(pos, True)

                if obj.alive:
                    obj.render(playfield)


        screen.blit(pygame.transform.scale(playfield, (self.height, self.height)), ((self.width-self.height)/2, 0))

        if hasattr(self, 'object_preview'):
            if self.object_preview['type'] == 'circle':
                x, y = pygame.mouse.get_pos()
                if hasattr(self, 'object_preview'):
                    if self.object_preview['type'] == 'circle':
                        x2, y2 = self.object_preview['pos']
                        self.object_preview['radius'] = self.snap(math.sqrt((x-x2)*(x-x2)+(y-y2)*(y-y2)))
                pygame.draw.circle(screen, pygame.Color('white'), self.object_preview['pos'], self.object_preview['radius'], 2)
            if self.object_preview['type'] == 'arc':
                pos = self.object_preview['pos']
                rad = self.object_preview['radius']
                angle = (360/(4*self.anglesnap))*round(((Vector2(pos)-Vector2(pygame.mouse.get_pos())).as_polar()[1])/(360/(4*self.anglesnap)))+180
                arc_size = math.degrees((self.height*self.arc_width())/rad)
                point_a = Vector2(pos)+Vector2(rad, 0).rotate(angle-arc_size/2)
                point_b = Vector2(pos)+Vector2(rad, 0).rotate(angle+arc_size/2)
                pygame.draw.line(screen, pygame.Color('white'), pos, point_a, 2)
                pygame.draw.line(screen, pygame.Color('white'), pos, point_b, 2)
                # pygame.draw.arc(screen, pygame.Color('white'), (pos[0]-rad, pos[1]-rad, rad*2, rad*2), angle-arc_size/2, angle+arc_size/2, 2)
            if self.object_preview['type'] == 'track':
                start_pos = Vector2(self.object_preview['start_pos'])
                start_angle = (self.object_preview['start_angle'])%360
                closest_circle = self.map['objects'][self.get_closest_circle_index()]
                circle_pos = convert_pos(Vector2(closest_circle['pos']), self.height)+Vector2((self.width-self.height)/2, 0)
                end_angle = (360/(4*self.anglesnap))*round(((Vector2(pygame.mouse.get_pos())-circle_pos).as_polar()[1])/(360/(4*self.anglesnap)))
                end_pos = circle_pos+Vector2(convert_scalar(closest_circle['radius'], self.height), 0).rotate(end_angle)

                if start_angle%180 != end_angle%180:
                    result = biarc_interpolator(start_pos, start_angle, end_pos, end_angle)
                    if result:
                        if result['c1']:
                            a1a = round(180-(Vector2(result['c1'])-Vector2(result['pm'])).as_polar()[1])%360
                            a1b = round(180-(Vector2(result['c1'])-Vector2(start_pos)).as_polar()[1])%360

                            anglediff = (a1a-a1b + 180) % 360 - 180
                            if anglediff > 0:
                                a1a, a1b = a1b, a1a

                            r1 = Vector2(result['pm']).distance_to(Vector2(result['c1']))

                        if result['c2']:
                            a2a = round(180-(Vector2(result['c2'])-Vector2(result['pm'])).as_polar()[1])%360
                            a2b = round(180-(Vector2(result['c2'])-Vector2(end_pos)).as_polar()[1])%360

                            anglediff = (a2a-a2b + 180) % 360 - 180
                            if anglediff > 0:
                                a2a, a2b = a2b, a2a

                            r2 = Vector2(result['pm']).distance_to(Vector2(result['c2']))

                        if result['c1']:
                            pygame.draw.arc(screen, pygame.Color('white'), (result['c1'][0]-r1, result['c1'][1]-r1, r1*2, r1*2), math.radians(a1a), math.radians(a1b), 2)
                        if result['c2']:
                            pygame.draw.arc(screen, pygame.Color('white'), (result['c2'][0]-r2, result['c2'][1]-r2, r2*2, r2*2), math.radians(a2a), math.radians(a2b), 2)

        pygame.draw.rect(screen, pygame.Color('white'), ((self.width-self.height)/2, 0, self.height, self.height), 4)


class PlayScene(BaseScene):
    def __init__(self, file_path):
        BaseScene.__init__(self)

        self.font = pygame.font.Font(resource_path(font_file), font_size)

        # pygame.mouse.set_cursor(pygame.Cursor((32, 32), cursor_surf))

        self.cur_pos = pygame.mouse.get_pos()
        self.last_pos = self.cur_pos
        self.mouse_trail = []

        self.darken_surf = pygame.Surface(cursor_trail.get_size())

        self.score = 0
        self.unmultiplied_score = 0
        self.max_score = 0
        self.combo = 0
        self.accuracy = 100

        self.objects = []
        self.width, self.height = pygame.display.get_surface().get_size()

        self.circle_count = 0

        self.file_path = file_path

        self.music_file_path = ''
        self.map_file_path = ''

        if file_path[-4:] == '.map':
            self.music_file_path = file_path[:-4]
            self.map_file_path = file_path
        else:
            self.music_file_path = file_path
            self.map_file_path = self.music_file_path+'.map'

        self.duration = pygame.mixer.Sound(self.music_file_path).get_length()*1000
        pygame.mixer.music.load(self.music_file_path)

        with open(self.map_file_path, 'rb') as map_file:
            self.map = pickle.load(map_file)

        self.object_queue = self.map['objects']
        
        self.hit_indicators = []

        pygame.mouse.set_visible(False)

        pygame.mixer.music.play()

    def get_circle_color(self):
        col = get_color(self.circle_count)
        self.circle_count += 1
        return col

    def get_arc_color(self, object):
        for obj in self.objects:
            if isinstance(obj, Circle) and object['start_time']+object['lifespan'] >= obj.start_time and object['start_time'] < obj.end_time and object['radius'] == obj.radius and object['pos'] == obj.pos:
                return obj.color

    def approach(self):
        return 200+float(self.map['approach'])*100

    def hit_window(self):
        return {'good': float(self.map['precision'])*10, 'ok': float(self.map['precision'])*20}

    def arc_width(self):
        return float(self.map['width'])/20

    def end_play(self):
        # pygame.mouse.set_cursor(*pygame.cursors.arrow)
        pygame.mouse.set_visible(True)

    def break_combo(self):
        self.combo = 0

    def update_stats(self, result):
        if result > 0:
            self.score += result*min(self.combo, 100)
            self.unmultiplied_score += result
            self.max_score += 100
            self.accuracy = round(10000*self.unmultiplied_score/self.max_score)/100
            self.combo += 1
        else:
            self.max_score += 100
            self.accuracy = round(10000*self.unmultiplied_score/self.max_score)/100
            self.combo = 0 

    def update(self, events):
        tick_time = pygame.mixer.music.get_pos()

        self.cur_pos = pygame.mouse.get_pos()

        self.mouse_trail.append((tick_time, self.cur_pos))
        while self.mouse_trail[0][0] < tick_time - trail_time:
            self.mouse_trail.pop(0)


        if len(self.objects) == 0 and len(self.object_queue) == 0:
            self.next = MapScene(self.file_path)
            self.end_play()
            return

        if len(self.object_queue):
            object = self.object_queue[0]
            if object['type'] == 'circle' and object['start_time']-object['appear_time'] <= tick_time:
                self.objects.append(Circle(object['pos'], object['radius'], object['appear_time'], object['start_time'], object['end_time'], self.get_circle_color()))
                self.object_queue.pop(0)
            elif object['type'] == 'arc' and object['start_time'] <= tick_time:
                self.objects.append(Arc(object['pos'], object['angle'], object['arc'], object['radius']+arc_distance, object['radius'], object['start_time'], self.approach(), self.hit_window(), self.get_arc_color(object)))
                self.object_queue.pop(0)
            elif object['type'] == 'track' and object['start_time']-object['appear_time'] <= tick_time:
                self.objects.append(Track(object['start_time'], object['appear_time'], object['end_time'], object['start_pos'], object['start_angle'], object['end_pos'], object['end_angle'], self.arc_width()))
                self.object_queue.pop(0)

        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.next = MapScene(self.file_path)
                    self.end_play()

            # if event.type == MOUSEMOTION:
            #     if event.pos != self.cur_pos:
            #         self.cur_pos = event.pos
        keep_objects = []
        first_obj = True
        cur_pos = ((self.cur_pos[0]*2-self.width)/self.height, -(self.cur_pos[1]*2-self.height)/self.height)

        for object in self.objects:
            object.update(tick_time)
            if isinstance(object, Arc) and first_obj:
                if self.last_pos != self.cur_pos:
                    last_pos = ((self.last_pos[0]*2-self.width)/self.height, -(self.last_pos[1]*2-self.height)/self.height)
                    self.last_pos = self.cur_pos
                    result = object.check_hit([last_pos, cur_pos])
                    if result > 0:
                        self.hit_indicators.append(HitIndicator(cur_pos, result, tick_time))
                        pygame.mixer.Sound.play(hit_sound)
                        self.update_stats(result)
                first_obj = False
            elif isinstance(object, Track) and first_obj:
                result = object.check_hit(cur_pos)
                if result < 0:
                    self.break_combo()
                first_obj = False

            if object.alive:
                keep_objects.append(object)
            elif isinstance(object, Arc) and object.ttl <= -object.hit_window['ok']:
                self.update_stats(-1)
                self.hit_indicators.append(HitIndicator(object.pos+Vector2(object.end_radius, 0).rotate(object.angle), -1, tick_time))


        self.objects = keep_objects

        keep_indicators = []
        for object in self.hit_indicators:
            object.update(tick_time)
            if object.ttl > 0:
                keep_indicators.append(object)
        
        self.hit_indicators = keep_indicators

    def render(self, screen):
        playfield = pygame.Surface((internal_res, internal_res))

        for object in self.objects:
            object.render(playfield)

        for object in self.hit_indicators:
            object.render(playfield)

        screen.blit(pygame.transform.scale(playfield, (self.height, self.height)), ((self.width-self.height)/2, 0))

        pygame.draw.rect(screen, pygame.Color('white'), ((self.width-self.height)/2, 0, self.height, self.height), 4)

        score_surf = self.font.render(str(self.score), True, pygame.Color('white'))
        acc_surf = self.font.render(str(self.accuracy)+'%', True, pygame.Color('white'))
        combo_surf = self.font.render(str(self.combo)+'x', True, pygame.Color('white'))

        x_pos = (self.width+self.height)/2 - font_size/2
        screen.blit(score_surf, (x_pos-score_surf.get_width(), font_size/2))
        screen.blit(acc_surf, (x_pos-acc_surf.get_width(), font_size/2+font_size))
        screen.blit(combo_surf, (x_pos-combo_surf.get_width(), font_size/2+font_size*2))

        for i in range(1, len(self.mouse_trail)):
            pos_a = Vector2(self.mouse_trail[i-1][1])
            pos_b = Vector2(self.mouse_trail[i][1])
            cur_pos_time = self.mouse_trail[i][0]
            last_pos_time = self.mouse_trail[-1][0]

            copy_surf = cursor_trail.copy()
            self.darken_surf.set_alpha(255*(last_pos_time-cur_pos_time)/trail_time)
            copy_surf.blit(self.darken_surf, (0, 0))

            pos_dist = pos_a.distance_to(pos_b)
            if pos_dist > 0:
                for j in range(math.floor(pos_dist)):
                    lerp_pos = pos_a.lerp(pos_b, j/pos_dist)
                    screen.blit(copy_surf, lerp_pos-Vector2(copy_surf.get_size())/2, special_flags=BLEND_MAX)


        screen.blit(cursor_surf, Vector2(self.cur_pos)-Vector2(cursor_surf.get_size())/2)
