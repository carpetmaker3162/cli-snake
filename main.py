import termios
import os
import time
import sys
from getch import getch
import threading

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
event_queue = []
IS_WIN = os.name == "nt" # fuck windows fr

SCREENW, SCREENH = os.get_terminal_size()
REFRESH_RATE = 0.2
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
    if char is None or char == " " or len(char) == 0:
        return 32
    else:
        return ord(char)

if __name__ == "__main__":
    try:
        thread = threading.Thread(target=process_keyboard_events, args=(event_queue))
        thread.daemon = True
        thread.start()

        while True:
            # refresh objects
            has_refreshed_player = False

            if event_queue:
                key = event_queue.pop(0)
                
                index(key)

                sys.stdout.flush()
            
            if time.time() - last_refresh > REFRESH_RATE:
                last_refresh = time.time()
    except Exception as e:
        raise e
    finally:
        reset_terminal()