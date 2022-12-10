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
SCREENW -= 2
SCREENH -= 3
REFRESH_RATE = 0.0667
SCENE_HEIGHT = SCREENH - 2

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
        self.frame = 0
    
    def new_apple(self):
        self.apple_count += 1
        nx = floor(random.random() * (SCREENW-2)) + 1
        ny = floor(random.random() * (SCENE_HEIGHT-2)) + 1
        while self.matrix[ny][nx] != 0:
            nx = floor(random.random() * (SCREENW-2)) + 1
            ny = floor(random.random() * (SCENE_HEIGHT-2)) + 1
        return nx, ny

    def load_matrix(self):
        self.frame += 1
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
        
        if self.effpx < 0 or self.effpx > SCREENW:
            raise SystemExit
        elif self.effpy < 0 or self.effpy > SCENE_HEIGHT:
            raise SystemExit
        
        new_position = (self.effpx, self.effpy)

        for r, row in enumerate(self.matrix):
            for c, cell in enumerate(row):
                if cell > 0 and prev_position != new_position:
                    self.matrix[r][c] += 1
                
                if self.matrix[self.effpy][self.effpx] > 2:
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
        buf += ("\r" + "//" * (SCREENW+2) + "\n")
        for row in self.matrix:
            buf += "\r//"
            for cell in row:
                buf += self.textures.get(cell, self.player_texture)
            buf += "//\n\r"
        buf += ("\r" + "//" * (SCREENW+2) + "\n")
        print(buf, end="")

OPPOSITES = {
    "U": "D",
    "D": "U",
    "L": "R",
    "R": "L",
}

DIRECTIONS = {
    87: "U",
    119: "U",
    68: "R",
    100: "R",
    83: "D",
    115: "D",
    65: "L",
    97: "L",
}

DIRECTION_VECT = {
    "L": (-1, 0),
    "R": (1, 0),
    "D": (0, 1),
    "U": (0, -1),
}

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
                else:
                    try:
                        new_direction = DIRECTIONS[index(key)]
                    except IndexError:
                        pass
                    
                    # dx, dy = DIRECTION_VECT[new_direction]
                    
                    if scene.player.direction != OPPOSITES[new_direction]:
                        scene.player.direction = DIRECTIONS[index(key)]
                        # scene.player.x += dx
                        # scene.player.y += dy
                
                sys.stdout.flush()
        
            if time.time() - last_refresh > REFRESH_RATE:
                last_refresh = time.time()
                scene.load_matrix()
                scene.print_matrix()
    except Exception as e:
        raise e
    finally:
        print("\r\n")
        reset_terminal()