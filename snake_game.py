import pygame
import serial
import random
import numpy as np
import time
import struct

# Initialize pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
RED = (213, 50, 80)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Game settings
WIDTH, HEIGHT = 66, 144
CELL_SIZE = 6
CELL_WIDTH = WIDTH // CELL_SIZE
CELL_HEIGHT = HEIGHT // CELL_SIZE

# Directions
LEFT = (-1, 0)
RIGHT = (1, 0)
UP = (0, -1)
DOWN = (0, 1)

arduino = serial.Serial('/dev/serial0', 921600)

START_SEQ = b'\xFC\x0C'
END_SEQ = b'\x0F\xFB'

def get_brg_from_surface(surface):
    raw_data = pygame.surfarray.array3d(surface)
    brg_data = bytearray()

    for y in range(surface.get_height()):
        for x in range(surface.get_width()):
            r, g, b = raw_data[x, y]
            # Scale down to 5 bits per color
            r = (r >> 3) & 0x1F
            g = (g >> 3) & 0x1F
            b = (b >> 3) & 0x1F
            # Pack the 5 bit colors into a 2-byte structure, leaving 1 bit unused
            brg_pixel = struct.pack('<H', (b << 11) | (g << 6) | (r << 1))
            brg_data.extend(brg_pixel)

    return brg_data


class Snake:
    def __init__(self):
        self.body = [(CELL_WIDTH // 2, CELL_HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN])

    def move(self):
        head = self.body[0]
        new_head = ((head[0] + self.direction[0]) % CELL_WIDTH, (head[1] + self.direction[1]) % CELL_HEIGHT)
        self.body = [new_head] + self.body[:-1]

    def grow(self):
        head = self.body[0]
        new_head = ((head[0] + self.direction[0]) % CELL_WIDTH, (head[1] + self.direction[1]) % CELL_HEIGHT)
        self.body = [new_head] + self.body

    def collides_with_itself(self):
        return self.body[0] in self.body[1:]


class Game:

    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.snake = Snake()
        self.food = self.generate_food()
        self.run = True
        
        # Initialize joystick module
        pygame.joystick.init()

        # Check for gamepad
        if pygame.joystick.get_count() > 0:
            self.gamepad = pygame.joystick.Joystick(0)
            self.gamepad.init()
        else:
            self.gamepad = None
            print("No gamepad detected.")

    def generate_food(self):
        while True:
            pos = (random.randint(0, CELL_WIDTH - 1), random.randint(0, CELL_HEIGHT - 1))
            if pos not in self.snake.body:
                return pos

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False

        # Gamepad handling
        if self.gamepad:
            x_axis = self.gamepad.get_axis(0)  # Axis 0 for left/right
            y_axis = self.gamepad.get_axis(1)  # Axis 1 for up/down

            if y_axis < -0.5 and self.snake.direction != RIGHT:
                self.snake.direction = LEFT
            elif y_axis > 0.5 and self.snake.direction != LEFT:
                self.snake.direction = RIGHT
            elif x_axis > 0.5 and self.snake.direction != DOWN:
                self.snake.direction = UP
            elif x_axis < -0.5 and self.snake.direction != UP:
                self.snake.direction = DOWN

    def update(self):
        self.snake.move()

        if self.snake.body[0] == self.food:
            self.snake.grow()
            self.food = self.generate_food()

        if self.snake.collides_with_itself():
            self.run = False

    def draw(self):
        self.screen.fill(BLACK)
        for segment in self.snake.body:
            pygame.draw.rect(self.screen, GREEN, (segment[0] * CELL_SIZE, segment[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(self.screen, RED, (self.food[0] * CELL_SIZE, self.food[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.display.flip()

    def run_game(self):
        clock = pygame.time.Clock()

        while self.run:
            self.handle_events()
            self.update()
            self.draw()

            # Capture the BRG data
            brg_image_data = get_brg_from_surface(self.screen)

            # Print a subset of the BRG data (for example, the first 10 pixels)
            print("BRG Data for first 10 pixels:", brg_image_data)

            arduino.write(START_SEQ)
            # Send BRG data
            arduino.write(brg_image_data)

            # Send End Sequence
            arduino.write(END_SEQ)
            time.sleep(0.1)
            clock.tick(20)
        pygame.quit()


# Main entry point
def play_snake_game():
    game = Game()
    game.run_game()
