import pygame
import sys
import os

# CONSTANTS
# BASIC VISUALS
SCRN_W = 500
SCRN_H = 500
PIXEL = 5
TILE_W = 2 * PIXEL
TILE_H = 2 * PIXEL
FPS = 60
DEBUG_FPS = 5

# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)

# DIRECTIONS
LEFT = 1
UP = 2
RIGHT = 3
DOWN = 4
TOP = UP
BOTTOM = DOWN

# TILE TYPES
VOID = 0
EMPTY = 1
WALL = 2

# MISC / UNSORTED
GRAVITY = 0.4
TERMINAL_VELOCITY = 15

# INITIALIZATION
pygame.mixer.init(44100, -16, 2, 512)
pygame.mixer.set_num_channels(16)
pygame.init()
postSurf = pygame.display.set_mode((SCRN_W, SCRN_H))

clock = pygame.time.Clock()
TAHOMA = pygame.font.SysFont("Tahoma", 10)


def update(slow_down=False):
    """should be run once every frame"""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.flip()
    postSurf.fill(BLACK)
    if slow_down:
        clock.tick(DEBUG_FPS)
    else:
        clock.tick(FPS)


def debug(num, *args):
    """renders a string containing all the arguments

    num is the line number"""
    string = ""
    for arg in args:
        string += repr(arg) + " "
    text = TAHOMA.render(string, False, WHITE)
    postSurf.blit(text, (10, num * 10 + 10))


def col_at(x):
    """returns the tile column at pixel position x"""
    return int(x // TILE_W)


def row_at(y):
    """returns the tile row at pixel position y"""
    return int(y // TILE_H)


def x_of(col, direction=LEFT):
    """returns the pixel position x of a column

    choose either the LEFT of the column or the RIGHT of the column"""
    if direction == LEFT:
        return col * TILE_W

    elif direction == RIGHT:
        return col * TILE_W + TILE_W


def y_of(row, direction=UP):
    """returns the pixel position y of a row

    choose either UP of the row or the DOWN of the row"""
    if direction == UP:
        return row * TILE_H

    elif direction == DOWN:
        return row * TILE_H + TILE_H


class Sprite:
    """stores a spritesheet made of all of a thing's animations"""
    def __init__(self, sheet_path, frame_w, frame_h, frame_counts):
        image = pygame.image.load(os.path.join("images", sheet_path))
        self.full_w = image.get_width() * PIXEL
        self.full_h = image.get_height() * PIXEL
        self.surface = pygame.transform.scale(image, (self.full_w, self.full_h))
        self.surface.set_colorkey(GREEN)

        self.frame_w = frame_w * PIXEL
        self.frame_h = frame_h * PIXEL
        self.anim_count = int(self.full_w / frame_w)
        self.frame_counts = frame_counts

        self.current_frame = 0
        self.current_anim = 0

        self.delay = 0

    def get_frame(self, anim_id, frame):
        """returns a subsurface containing a frame of an animation"""
        x = self.frame_w * anim_id
        y = self.frame_h * frame
        return self.surface.subsurface((x, y, self.frame_w, self.frame_h))

    def get_now_frame(self):
        """returns a subsurface containing the current frame"""
        return self.get_frame(self.current_anim, self.current_frame)

    def next_frame(self):
        self.current_frame += 1
        if self.current_frame >= self.frame_counts[self.current_anim]:
            self.current_frame = 0

    def prev_frame(self):
        self.current_frame -= 1
        if self.current_frame <= -1:
            self.current_frame = self.frame_counts[self.current_anim] - 1

    def change_anim(self, anim_id):
        if anim_id >= self.anim_count:
            print("change_anim() tried to change to a nonexistant animation.")

        elif anim_id != self.current_anim:
            self.current_anim = anim_id
            self.current_frame = 0

    def delay_next(self, delay):
        """delays flipping to the next animation frame for some frames

        note: must be called every frame of the delay"""
        if not self.delay:
            self.delay = delay
        else:
            self.delay -= 1

            if self.delay == 0:
                self.next_frame()


class Soundboard:
    def __init__(self):
        self.music_id = 0
        self.sounds = []

    def add(self, file_path):
        file_path = os.path.join("sounds", file_path)
        self.sounds.append(pygame.mixer.Sound(file_path))

    def play(self, sound_id, loops=0):
        self.sounds[sound_id].play(loops)

    def fade(self, sound_id, time):
        self.sounds[sound_id].fade(time)

    def stop(self, sound_id):
        self.sounds[sound_id].stop()

    def play_music(self, sound_id, fade_in=0):
        self.music_id = sound_id
        self.sounds[sound_id].play(-1, 0, fade_in)

    def fade_music(self, time):
        self.sounds[self.music_id].fadeout(time)

    def change_music(self, sound_id, fade_in=0):
        """fades one music track into another"""
        self.fade_music(fade_in)
        self.play_music(sound_id)


class Camera:
    def __init__(self):
        self.body = Body(int(SCRN_W / 2), int(SCRN_H / 2), 0, 0)
        self.focus_body = None
        self.constrain_x = True
        self.constrain_y = True

    def change_focus(self, body):
        """centers the camera around a new body"""
        self.focus_body = body

    def step_to(self, x, y):
        """moves one step towards a specific point"""
        distance_x = int((x - self.body.x) / 10)
        distance_y = int((y - self.body.y) / 10)
        self.body.goto(self.body.x + distance_x, self.body.y + distance_y)

    def focus(self, x_off=0, y_off=0):
        """moves towards the focus point

        you can focus some distance away from the body using the offsets"""
        if self.constrain_x:
            x = self.body.x
        else:
            x = self.focus_body.x + int(self.focus_body.w / 2)

        if self.constrain_y:
            y = self.body.y
        else:
            y = self.focus_body.y + int(self.focus_body.h / 2)

        debug(12, "focus_x", x)
        debug(13, "focus_y", y)

        self.step_to(x + x_off, y + y_off)

    def autolock(self, level):
        """automatically locks the camera depending on the size of the level"""
        if level.GRID_W * TILE_W > SCRN_W:
            self.constrain_x = False
        else:
            self.constrain_x = True

        if level.GRID_H * TILE_H > SCRN_H:
            self.constrain_y = False
        else:
            self.constrain_y = True


class Grid:
    """the grid where all the tiles in the level are placed"""
    def __init__(self, width, height):
        self.GRID_W = width
        self.GRID_H = height
        self.FULL_W = width * TILE_W
        self.FULL_H = height * TILE_H
        self.grid = [[EMPTY for _ in range(height)] for _ in range(width)]

    def out_of_bounds(self, col, row):
        """returns whether or not a tile is outside of the grid"""
        if 0 <= col < self.GRID_W and 0 <= row < self.GRID_H:
            return False

        return True

    def change_point(self, col, row, kind):
        """changes a rectangle"""
        if not self.out_of_bounds(col, row):
            self.grid[col][row] = kind
        else:
            print("change_point() tried to add a tile out of bounds.")

    def change_rect(self, x, y, w, h, kind):
        """places a rectangle of tiles at the given coordinates"""
        for col in range(x, x + w):
            for row in range(y, y + h):
                if not self.out_of_bounds(col, row):
                    self.grid[col][row] = kind
                else:
                    print("change_rect() tried to add a tile out of bounds.")

    def tile_at(self, col, row):
        """returns the tile type at a certain position

        all tiles out of bounds return VOID"""
        if not self.out_of_bounds(col, row):
            return self.grid[col][row]

        return VOID

    def is_solid(self, col, row):
        """returns whether a tile is solid or not

        currently, the only non-solid tile is the empty tile"""
        if self.tile_at(col, row) == EMPTY:
            return False

        return True

    def collide_vert(self, x, y1, y2):
        col = col_at(x)
        start_row = row_at(y1)
        end_row = row_at(y2)
        for row in range(start_row, end_row + 1):
            if self.is_solid(col, row):
                return True

        return False

    def collide_horiz(self, x1, x2, y):
        start_col = col_at(x1)
        end_col = col_at(x2)
        row = row_at(y)
        for col in range(start_col, end_col + 1):
            if self.is_solid(col, row):
                return True

        return False

    def draw(self):
        """draws the entire stage"""
        for row in range(self.GRID_H):
            for col in range(self.GRID_W):
                if self.tile_at(col, row) == WALL:
                    rect = (col * TILE_W, row * TILE_H, TILE_W, TILE_H)
                    pygame.draw.rect(postSurf, WHITE, rect)


class Body:
    """the skeleton of anything that moves and lives"""
    def __init__(self, x, y, w, h, extend_x=0, extend_y=0):
        self.x = x
        self.y = y
        self.xVel = 0
        self.yVel = 0
        self.xAcc = 0
        self.yAcc = 0

        self.xDir = 0
        self.yDir = 0

        self.w = w
        self.h = h
        self.extend_x = extend_x
        self.extend_y = extend_y
        self.gridbox = pygame.Rect(x, y, w, h)
        self.hitbox = pygame.Rect(x - extend_x, y - extend_y,
                                  w + extend_x*2, h + extend_y*2)

        self.grounded = False
        self.grid = grid   # reference to the level layout

    def goto(self, x, y):
        """instantly moves the body to a specific position"""
        x = int(x)
        y = int(y)
        self.x = x
        self.y = y
        self.gridbox.x = x
        self.gridbox.y = y
        self.hitbox.x = x - self.extend_x
        self.hitbox.y = y - self.extend_y

    def move(self):
        """moves body based on velocity and acceleration"""
        self.xVel += self.xAcc
        self.yVel += self.yAcc
        self.x += self.xVel
        self.y += self.yVel

        if self.xVel < 0:
            self.xDir = LEFT
        elif self.xVel > 0:
            self.xDir = RIGHT
        else:
            self.xDir = 0

        if self.yVel < 0:
            self.yDir = UP
        elif self.yVel > 0:
            self.yDir = DOWN
        else:
            self.yDir = 0

        self.check_ground()

        self.goto(self.x, self.y)

    def next_x(self):
        """returns the x position of the body on the next frame"""
        return self.x + self.xVel + self.xAcc

    def next_y(self):
        """returns the y position of the body on the next frame"""
        return self.y + self.yVel + self.yAcc

    def stop_x(self):
        self.xDir = 0
        self.xVel = 0
        self.xAcc = 0

    def stop_y(self):
        self.yDir = 0
        self.yVel = 0
        self.yAcc = 0

    def snap_x(self, col, side=LEFT):
        """snaps you to either the left side or right side of a tile"""
        if side == LEFT:
            self.goto(x_of(col, LEFT) - self.w, self.y)
            self.stop_x()

        elif side == RIGHT:
            self.goto(x_of(col, RIGHT), self.y)
            self.stop_x()

    def snap_y(self, row, side=TOP):
        """snaps you to either the top or bottom of a tile"""
        if side == TOP:
            self.goto(self.x, y_of(row, TOP) - self.h)
            self.stop_y()

        elif side == BOTTOM:
            self.goto(self.x, y_of(row, BOTTOM))
            self.stop_y()

    def collide_stage(self):
        """checks collision with stage and updates movement accordingly"""
        diff_x = self.next_x() - self.x
        diff_y = self.next_y() - self.y

        if diff_x < 0:
            dir_x = LEFT
        elif diff_x > 0:
            dir_x = RIGHT
        else:
            dir_x = 0

        if diff_y < 0:
            dir_y = UP
        elif diff_y > 0:
            dir_y = DOWN
        else:
            dir_y = 0

        for step in range(1, 5):
            left_x = self.x
            right_x = left_x + self.w - 1
            top_y = int(self.y + (diff_y * (step / 4)))
            bottom_y = top_y + self.h - 1

            if dir_y == UP:
                if self.grid.collide_horiz(left_x, right_x, top_y):
                    self.snap_y(row_at(top_y), BOTTOM)
            elif dir_y == DOWN:
                if self.grid.collide_horiz(left_x, right_x, bottom_y):
                    self.snap_y(row_at(bottom_y), TOP)

            left_x = int(self.x + (diff_x * (step / 4)))
            right_x = left_x + self.w - 1
            top_y = self.y
            bottom_y = top_y + self.h - 1

            if dir_x == LEFT:
                if self.grid.collide_vert(left_x, top_y, bottom_y):
                    self.snap_x(col_at(left_x), RIGHT)
            elif dir_x == RIGHT:
                if self.grid.collide_vert(right_x, top_y, bottom_y):
                    self.snap_x(col_at(right_x), LEFT)

    def check_ground(self):
        x1 = self.x
        x2 = x1 + self.w - 1
        y = self.y + self.h
        if self.grid.collide_horiz(x1, x2, y):
            self.grounded = True
        else:
            self.grounded = False

    def try_fall(self):
        if not self.grounded:
            if self.yVel < TERMINAL_VELOCITY:
                self.yAcc = GRAVITY
            else:
                self.yAcc = 0
                self.yVel = TERMINAL_VELOCITY

    def try_jump(self, power):
        soundboard.stop(SOUND_JUMP)
        soundboard.play(SOUND_JUMP)
        if self.grounded:
            self.grounded = False
            self.yVel = -power


class Player:
    def __init__(self, x, y, w, h, extend_x=0, extend_y=0):
        self.body = Body(x, y, w, h, extend_x, extend_y)
        self.sprite = None

    def move(self):
        self.body.try_fall()
        self.body.collide_stage()
        self.body.move()

        debug(5, "xVel:", self.body.xVel)
        debug(6, "yVel:", self.body.yVel)

    def draw(self):
        postSurf.blit(self.sprite.get_now_frame(), (self.body.x, self.body.y))


soundboard = Soundboard()
soundboard.add("test_jump.wav")
soundboard.add("test_sound.wav")
soundboard.add("test_music.wav")
soundboard.add("test_loop.wav")
SOUND_JUMP = 0
SOUND_TEST = 1
SOUND_TEST_MUSIC = 2
SOUND_TEST_LOOP = 3

grid = Grid(50, 51)   # temporary level
grid.change_rect(10, 42, 10, 1, WALL)
grid.change_rect(13, 45, 20, 1, WALL)
grid.change_rect(18, 48, 30, 1, WALL)
grid.change_rect(40, 40, 5, 10, WALL)
levelSurf = pygame.Surface((grid.FULL_W, grid.FULL_H))

player = Player(380, 400, 5 * PIXEL, 5 * PIXEL, -2, -2)
player.sprite = Sprite("test_player.png", 5, 5, (1, 5, 5))
IDLE = 0
MOVE_LEFT = 1
MOVE_RIGHT = 2

camera = Camera()
camera.autolock(grid)
camera.change_focus(player.body)

soundboard.play_music(SOUND_TEST_LOOP, 5000)

while True:
    keys = pygame.key.get_pressed()

    # debug keys
    if keys[pygame.K_r]:
        player.body.goto(SCRN_W / 2, 0)

    # movement keys
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        player.body.try_jump(5)

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.sprite.change_anim(MOVE_LEFT)
        player.sprite.delay_next(2)

        player.body.xVel = -3

    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.sprite.change_anim(MOVE_RIGHT)
        player.sprite.delay_next(2)

        player.body.xVel = 3
    else:
        player.sprite.change_anim(IDLE)
        player.body.xVel = 0

    player.move()

    grid.draw()
    player.draw()

    debug(0, "FPS: %.2f" % clock.get_fps())
    debug(1, "xDir:", player.body.xDir)
    debug(2, "yDir:", player.body.yDir)
    debug(3, "grounded:", player.body.grounded)

    camera.focus()
    debug(9, "camera.x:", camera.body.x)
    debug(10, "camera.y:", camera.body.y)

    if keys[pygame.K_f]:
        update(True)
    else:
        update()
