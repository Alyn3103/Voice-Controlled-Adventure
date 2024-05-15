import numpy as np
import pygame
from os import path
import pickle
import tensorflow as tf
from tensorflow.python.keras import models
import threading

from audio_helper import record_audio
from tf_helper import preprocess_audiobuffer

commands = ['no', 'right', 'yes', 'up', 'down', 'left', 'go', 'stop']

loaded_model = tf.keras.models.load_model("saved_model")

voice_command = None
lock = threading.Lock()


def voice_recognition():
    global voice_command
    while True:
        audio = record_audio()
        spec = preprocess_audiobuffer(audio)
        prediction = loaded_model(spec)
        label_pred = np.argmax(prediction, axis=1)
        command = commands[label_pred[0]]
        if command in ['right', 'left', 'up', 'stop']:
            with lock:
                voice_command = command
        if command in ['right', 'left', 'up', 'stop']:
            print("Predicted label:", command)

def move_player(command):
    if command == 'up':
        player.jump = True
    elif command == 'down':
        # Implement downward movement logic
        pass
    elif command == 'left':
        player.move_right = False  # Stop moving right
        player.move_left = True    # Start moving left
        player.direction = -1
    elif command == 'right':
        player.move_left = False  # Stop moving left
        player.move_right = True  # Start moving right
        player.direction = 1
    elif command == 'stop':
        player.move_left = False
        player.move_right = False
        player.jump = False 
    
def handle_key_event(event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            player.jump = True
        elif event.key == pygame.K_LEFT:
            player.move_left = True
        elif event.key == pygame.K_RIGHT:
            player.move_right = True
    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_SPACE:
            player.jump = False
        elif event.key == pygame.K_LEFT:
            player.move_left = False
        elif event.key == pygame.K_RIGHT:
            player.move_right = False
            
def terminate_game():
    print('Game Over')

class Player():
    def __init__(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 10):
            img_right = pygame.image.load(f'img/girl{num}.png')
            img_right = pygame.transform.scale(img_right, (60, 70))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.move_left = False
        self.move_right = False
        self.jump = False
        self.jump_timer = 0
        self.move_speed = 3
        self.max_speed = 3

    def update(self):
        dx = 0
        dy = 0
        walk_cooldown = 5

        #get keypresses
        key = pygame.key.get_pressed()
        if self.jump and not self.jumped:
            self.vel_y = -15
            self.jumped = True
            self.jump_timer = pygame.time.get_ticks()  # Start the jump timer
        elif pygame.time.get_ticks() - self.jump_timer >= 500:
            self.jumped = False

        if self.move_left:
            dx -= self.move_speed
            self.counter += 1
            self.direction = -1

        if self.move_right:
            dx += self.move_speed
            self.counter += 1
            self.direction = 1

        if dx < -self.max_speed:
            dx = -self.max_speed
        elif dx > self.max_speed:
            dx = self.max_speed

        if not self.move_left and not self.move_right:
            self.counter = 0
            self.index = 0
            if self.direction == 1:
                self.image = self.images_right[self.index]
            if self.direction == -1:
                self.image = self.images_left[self.index]


        if self.counter > walk_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images_right):
                self.index = 0
            if self.direction == 1:
                self.image = self.images_right[self.index]
            if self.direction == -1:
                self.image = self.images_left[self.index]


        #add gravity
        self.vel_y += 1
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        for tile in world.tile_list:
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.vel_y < 0:
                    dy = tile[1].bottom - self.rect.top
                    self.vel_y = 0
                elif self.vel_y >= 0:
                    dy = tile[1].top - self.rect.bottom
                    self.vel_y = 0

        self.rect.x += dx
        self.rect.y += dy

        if self.rect.bottom > screen_height:
            self.rect.bottom = screen_height
            dy = 0

        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)


class World():
    def __init__(self, data):
        self.tile_list = []

        #load images
        dirt_img = pygame.image.load('img/dirt.png')
        grass_img = pygame.image.load('img/grass.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])
            pygame.draw.rect(screen, (255, 255, 255), tile[1], 2)

pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 600
screen_height = 600

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('2DPLATFORM')

#define game variables
tile_size = 40
level = 1

#load images
sun_img = pygame.image.load('img/sun.png')
bg_img = pygame.image.load('img/bg.png')

player = Player(100, screen_height - 130)
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

# Start the voice recognition thread
voice_thread = threading.Thread(target=voice_recognition)
voice_thread.daemon = True
voice_thread.start()

# Game loop
run = True
while run:
    clock.tick(fps)

    screen.blit(bg_img, (0, 0))
    screen.blit(sun_img, (100, 100))

    world.draw()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        handle_key_event(event)
    with lock:
        command = voice_command

    if command is not None:
        move_player(command)

    player.update()

    pygame.display.update()
