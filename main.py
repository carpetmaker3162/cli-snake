import termios
import os
import time
import sys
from getch import getch
import threading
from math import floor, ceil
import random

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
event_queue = []
IS_WIN = os.name == "nt"

SCREENW, SCREENH = os.get_terminal_size()
SCREENW //= 2
REFRESH_RATE = 0.0667
SCENE_HEIGHT = 20
PIPE_OPENING_SIZE = 6
MODE = 0

def process_keyboard_events(q):
    while True:
        q.append(getch())

def reset_terminal():
    if not IS_WIN:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def index(char):
    if not char.strip():
        return 32
    else:
        return ord(char)

class Player:
    def __init__(self) -> None:
        self.direction = "R"
        self.x = floor(SCREENW / 6)
        self.y = floor(SCREENH / 2)
        self.speed = 0.8
        self.length = 4
    
    def update(self):
        match self.direction:
            case "R":
                self.x += self.speed # note to self: be conservative with movement
            case "L":
                self.x -= self.speed
            case "U":
                self.y -= self.speed
            case "D":
                self.y += self.speed

class Scene:
    def __init__(self) -> None:
        """
        -2 is wall
        -1 is apple
        0 is space
        >1 is snake body depending on length of the snake
        """
        self.matrix = [[0 for i in range(SCREENW)] for i in range(SCENE_HEIGHT)]
        self.player = Player()
        self.textures = {
            0: "  ",
            -1: "\033[101m  \033[0m",
            -2: "//",
        }
        self.player_texture = "\033[40m  \033[0m"
        self.apple_count = 0
        self.effpx = self.player.x
        self.effpy = self.player.y
        self.matrix[self.effpy][self.effpx] = 1
        ax, ay = self.new_apple()
        self.matrix[ay][ax] = -1
    
    def new_apple(self):
        self.apple_count += 1
        nx = floor(random.random() * (SCREENW-2)) + 1
        ny = floor(random.random() * (SCENE_HEIGHT-2)) + 1
        if self.matrix[ny][nx] > 0:
            return self.new_apple()
        return nx, ny

    def load_matrix(self):
        self.player.update()
        prev_position = (self.effpx, self.effpy)
        
        # match self.player.direction: # be conservative with player position (change later because when you turn it looks weird)
        #     case "R":
        #         self.effpx = floor(self.player.x)
        #         self.effpy = round(self.player.y)
        #     case "L":
        #         self.effpx = ceil(self.player.x)
        #         self.effpy = round(self.player.y)
        #     case "U":
        #         self.effpx = round(self.player.x)
        #         self.effpy = ceil(self.player.y)
        #     case "D":
        #         self.effpx = round(self.player.x)
        #         self.effpy = floor(self.player.y)
        self.effpx = round(self.player.x)
        self.effpy = round(self.player.y)
        
        if self.player.x < 1 or self.player.x > SCREENW-1:
            raise SystemExit
        elif self.player.y < 1 or self.player.y > SCREENH-1:
            raise SystemExit
        
        new_position = (self.effpx, self.effpy)

        for r, row in enumerate(self.matrix):
            for c, cell in enumerate(row):
                if cell > 0 and prev_position != new_position:
                    self.matrix[r][c] += 1
                
                if self.matrix[self.effpy][self.effpx] > 3:
                    raise SystemExit
                elif self.matrix[self.effpy][self.effpx] == -1:
                    self.player.length += 3
                    ax, ay = self.new_apple()
                    self.matrix[ay][ax] = -1
                
                self.matrix[self.effpy][self.effpx] = 1
                
                if self.matrix[r][c] > self.player.length:
                    self.matrix[r][c] = 0
    
    def print_matrix(self):
        print("\033[H")
        print("\r", end="")
        buf = str()
        for row in self.matrix:
            for cell in row:
                buf += self.textures.get(cell, self.player_texture)
            buf += "\n\r"
        print(buf, end="")

if __name__ == "__main__":
    try:
        os.system("cls" if IS_WIN else "clear")
        thread = threading.Thread(target=process_keyboard_events, args=(event_queue,))
        thread.daemon = True
        thread.start()
        scene = Scene()
        last_refresh = time.time()
        
        while True:
            if event_queue:
                key = event_queue.pop(0)
            
                if index(key) in (3, 4, 27):
                    raise SystemExit
                elif index(key) in (87, 119):
                    scene.player.direction = "U"
                elif index(key) in (68, 100):
                    scene.player.direction = "R"
                elif index(key) in (83, 115):
                    scene.player.direction = "D"
                elif index(key) in (65, 97):
                    scene.player.direction = "L"
                sys.stdout.flush()
        
            if time.time() - last_refresh > REFRESH_RATE:
                last_refresh = time.time()
                scene.load_matrix()
                scene.print_matrix()
    except Exception as e:
        raise e
    finally:
        reset_terminal()