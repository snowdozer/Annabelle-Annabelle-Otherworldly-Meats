import pygame
import sys
import os
import math
import random

# CONSTANTS
# BASIC VISUALS
SCRN_W = 500
SCRN_H = 500
PIXEL = 4
TILE_W = PIXEL*14
TILE_H = PIXEL*14
FPS = 60
DEBUG_FPS = 5

# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PALE_RED = (255, 100, 100)
SCORE_RED = (252, 37, 37)
GREEN = (0, 255, 0)
SCORE_GREEN = (27, 226, 66)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)

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
ALL_WALL = 2
PLAYER_WALL = 3
ENEMY_WALL = 4
ALL = 0
PLAYER = 1
ENEMY = 2

# MISC / UNSORTED
GRAVITY = 0.4
TERMINAL_VELOCITY = 15

# INITIALIZATION
os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.mixer.init(44100, -16, 2, 512)
pygame.mixer.set_num_channels(16)
pygame.init()
postSurf = pygame.display.set_mode((SCRN_W, SCRN_H))

clock = pygame.time.Clock()
DEBUG_FONT = pygame.font.SysFont("Tahoma", 10)
FONT = pygame.font.Font("m5x7.ttf", 64)
FONT_SMALL = pygame.font.Font("m5x7.ttf", 32)


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
    text = DEBUG_FONT.render(string, False, WHITE, BLACK)
    postSurf.blit(text, (10, num * 10 + 100))


def debug_point(pos):
    pygame.draw.circle(postSurf, YELLOW, pos, 3)


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


def angle_of(pos1, pos2):
    """returns the angle in radians between two points from standard position"""
    delta_x = pos2[0] - pos1[0]
    delta_y = pos2[1] - pos1[1]
    return math.atan2(delta_y, delta_x)


def angle_pos(center_pos, angle, dist):
    """returns a point a certain distance away at a certain angle"""
    delta_x = math.cos(angle) * dist
    delta_y = math.sin(angle) * dist
    return center_pos[0] + delta_x, center_pos[1] + delta_y


def distance(pos1, pos2):
    """returns the distance between two points"""
    return math.sqrt((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2)


def body_distance(body1, body2):
    return distance(body1.pos_center(), body2.pos_center())


def load_image(path):
    image = pygame.image.load(os.path.join("images", path))
    width = image.get_width() * PIXEL
    height = image.get_height() * PIXEL
    resized = pygame.transform.scale(image, (width, height))
    resized.convert()
    return resized


class ScreenFade:
    FADE_STEP = 1

    def __init__(self):
        self.w = SCRN_W
        self.h = SCRN_H
        self.surf = pygame.Surface((SCRN_W, SCRN_H))
        self.transparency = 0
        self.fade_in = False
        self.fade_out = False
        self.target = 0

    def fade_to_black(self):
        self.fade_in = False
        self.fade_out = True
        self.target = 255

    def fade_from_black(self):
        self.fade_in = True
        self.fade_out = False
        self.target = 0

    def set_transparency(self, value):
        self.transparency = 255 - value

    def fade_to(self, value):
        self.target = value
        if self.transparency < 255 - value:
            self.fade_in = False
            self.fade_out = True
        else:
            self.fade_in = True
            self.fade_out = False

    def update(self):
        if self.fade_out:
            self.transparency += self.FADE_STEP
            if self.transparency > self.target:
                self.transparency = self.target
                self.fade_out = False

        elif self.fade_in:
            self.transparency -= self.FADE_STEP
            if self.transparency < self.target:
                self.transparency = self.target
                self.fade_in = False

        self.surf.set_alpha(self.transparency)
        postSurf.blit(self.surf, (0, 0))




class Pinhole:
    """inverted circle of black"""
    LOW_PULSE = 55
    HIGH_PULSE = 65
    SWITCH_DIFF = 0.658

    def __init__(self):
        self.x = 0
        self.y = 0
        self.w = int(SCRN_W / PIXEL)
        self.h = int(SCRN_H / PIXEL)
        self.radius = 100
        self.surf = pygame.Surface((self.w, self.h))
        self.surf.set_colorkey(GREEN)
        self.contracting = False

    def set_position(self, pos):
        self.x = pos[0]
        self.y = pos[1]

    def set_radius(self, radius):
        self.surf.fill(BLACK)
        pygame.draw.circle(self.surf, GREEN, (self.x, self.y), int(radius))

    def get_surface(self):
        return pygame.transform.scale(self.surf, (SCRN_W, SCRN_H))

    def update(self):
        if player.inShop:
            self.contracting = False
            if self.radius < 100:
                self.radius *= 1.05
        else:
            if self.contracting:
                if self.radius > self.LOW_PULSE + self.SWITCH_DIFF:
                    self.radius -= -(self.LOW_PULSE - self.radius) / 50
                else:
                    self.contracting = False
            else:
                if self.radius < self.HIGH_PULSE - self.SWITCH_DIFF:
                    self.radius += (self.HIGH_PULSE - self.radius) / 50
                else:
                    self.contracting = True

        self.set_radius(self.radius)
        postSurf.blit(self.get_surface(), (0, 0))


class Spritesheet:
    """stores a spritesheet made of all of a thing's animations"""
    def __init__(self, sheet_path, frame_w, frame_h, frame_counts):
        self.surface = load_image(sheet_path)
        self.surface.set_colorkey(GREEN)

        self.full_w = self.surface.get_width()
        self.full_h = self.surface.get_height()

        self.frame_w = PIXEL*frame_w
        self.frame_h = PIXEL*frame_h
        self.anim_count = int(self.full_w / frame_w)
        self.frame_counts = frame_counts
        self.z_height = 0

    def init_z_height(self, rect):
        self.z_height = self.frame_h - rect.h

    def get_frame(self, anim_id, frame):
        """returns a subsurface containing a frame of an animation"""
        if anim_id >= self.anim_count:
            print("get_frame() tried to return a non-existant animation!")
        elif frame >= self.frame_counts[anim_id]:
            print("get_frame() tried to return a non-existant frame!")

        x = self.frame_w * anim_id
        y = self.frame_h * frame
        return self.surface.subsurface((x, y, self.frame_w, self.frame_h))


class SpriteInstance:
    """handles all frame and animation stuff for each entity"""
    def __init__(self, sheet):
        self.current_frame = 0
        self.current_anim = 0

        self.delay = 0

        self.sheet = sheet

    def set_frame(self, frame):
        self.current_frame = frame

    def get_now_frame(self):
        """returns a subsurface containing the current frame"""
        return self.sheet.get_frame(self.current_anim, self.current_frame)

    def next_frame(self):
        self.current_frame += 1
        if self.current_frame >= self.sheet.frame_counts[self.current_anim]:
            self.current_frame = 0

    def prev_frame(self):
        self.current_frame -= 1
        if self.current_frame <= -1:
            self.current_frame = self.sheet.frame_counts[self.current_anim] - 1

    def change_anim(self, anim_id):
        if anim_id >= self.sheet.anim_count:
            print("change_anim() tried to change to a nonexistant animation.")

        elif anim_id != self.current_anim:
            self.current_anim = anim_id
            self.current_frame = 0
            self.delay = 0

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
        self.play_music(sound_id, fade_in)

    def update(self):
        shop = self.sounds[MUSIC_SHOP]
        shop_volume = shop.get_volume()
        underworld = self.sounds[MUSIC_UNDERWORLD]
        underworld_volume = underworld.get_volume()
        if shop_volume < 1.0 and player.inShop:
            shop.set_volume(shop_volume + 0.025)
            underworld.set_volume(1 - shop_volume)
        elif underworld_volume < 1.0 and not player.inShop:
            underworld.set_volume(underworld_volume + 0.025)
            shop.set_volume(1 - underworld_volume)


class Camera:
    """it's a camera

    EDGE_OFFSET is the extra bit off the limit you want to show"""
    EDGE_OFFSET = PIXEL*5

    def __init__(self):
        half_width = int(SCRN_W / 2)
        half_height = int(SCRN_H / 2)

        self.body = Body(half_width, half_height, 0, 0)
        self.focus_body = None
        self.constrain_x = True
        self.constrain_y = True

        self.LIMIT_LEFT = half_width - self.EDGE_OFFSET
        self.LIMIT_RIGHT = grid.FULL_W - half_width + self.EDGE_OFFSET
        self.LIMIT_UP = half_height - self.EDGE_OFFSET + SHOP_ENTER - TILE_H
        self.LIMIT_DOWN = grid.FULL_H - half_height + self.EDGE_OFFSET

    def change_focus(self, body):
        """centers the camera around a new body"""
        self.focus_body = body

    def step_to(self, x, y):
        """moves one step towards a specific point"""
        distance_x = (x - self.body.x) / 10
        distance_y = (y - self.body.y) / 10
        # debug(5, "camera step distance %.2f %.2f" % (distance_x, distance_y))
        self.body.goto(self.body.x + distance_x, self.body.y + distance_y)

    def focus(self, x_off=0, y_off=0):
        """moves towards the focus point

        you can focus some distance away from the body using the offsets"""
        if self.constrain_x:
            x = self.body.x
        else:
            x = self.focus_body.x + int(self.focus_body.w / 2)

            if x < self.LIMIT_LEFT:   # stops camera at edge of map
                x += self.LIMIT_LEFT - x
            elif x > self.LIMIT_RIGHT:
                x += self.LIMIT_RIGHT - x

        if self.constrain_y:
            y = self.body.y
        else:
            y = self.focus_body.y + int(self.focus_body.h / 2)

            if y < self.LIMIT_UP:
                y += self.LIMIT_UP - y
            elif y > self.LIMIT_DOWN:
                y += self.LIMIT_DOWN - y

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

    def pos(self, position):
        """returns the x and y based on the camera"""
        x = position[0] + -(self.body.x - int(SCRN_W / 2))
        y = position[1] + -(self.body.y - int(SCRN_H / 2))
        return int(x), int(y)

    def handle(self):
        if not player.inShop:
            self.focus()
        else:
            self.step_to(SHOP_CENTER[0], SHOP_CENTER[1])


class Grid:
    """the grid where all the tiles in the level are placed"""
    def __init__(self, width, height):
        self.GRID_W = width
        self.GRID_H = height
        self.FULL_W = width * TILE_W
        self.FULL_H = height * TILE_H
        self.grid = [[EMPTY for _ in range(height)] for _ in range(width)]
        self.surf = None

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

    def is_solid(self, col, row, requester=ALL):
        """returns whether a tile is solid or not

        you can specify which entity specifically is asking for it"""
        tile = self.tile_at(col, row)
        if tile == ALL_WALL:
            return True
        elif (requester == PLAYER or requester == ALL) and tile == PLAYER_WALL:
            return True
        elif (requester == ENEMY or requester == ALL) and tile == ENEMY_WALL:
            return True

        return False

    def collide_vert(self, x, y1, y2, requester=ALL):
        col = col_at(x)
        start_row = row_at(y1)
        end_row = row_at(y2)
        for row in range(start_row, end_row + 1):
            if self.is_solid(col, row, requester):
                return True

        return False

    def collide_horiz(self, x1, x2, y, requester=ALL):
        start_col = col_at(x1)
        end_col = col_at(x2)
        row = row_at(y)
        for col in range(start_col, end_col + 1):
            if self.is_solid(col, row, requester):
                return True

        return False

    def create_surf(self):
        """draws the entire stage"""
        dimensions = (self.FULL_W + TILE_W * 2, self.FULL_H + TILE_H*2)
        self.surf = pygame.Surface(dimensions)
        self.surf.blit(level_background, (0, 0))

    def draw(self, surf):
        surf.blit(self.surf, camera.pos((-TILE_W, -TILE_H)))


def collide(rect1, rect2):
    return pygame.Rect(rect1).colliderect(rect2)


# CELL_W = 10
# CELL_H = 10
# partition = [[[] for y in range(CELL_H)] for x in range(CELL_W)]


class Score:
    """a visual counter"""
    COLOR_CHANGE_TIME = 20

    def __init__(self, start_count, pos):
        self.color = WHITE
        self.count = start_count

        self.timer = 0

        self.x = pos[0]
        self.y = pos[1]

    def draw(self, surf):
        text = FONT.render(str(self.count), False, self.color)
        surf.blit(text, (self.x, self.y))

    def change(self, amount):
        self.timer = self.COLOR_CHANGE_TIME
        if amount > 0:
            self.color = SCORE_GREEN
        elif amount < 0:
            self.color = SCORE_RED

        self.count += amount

    def update(self):
        if self.timer:
            self.timer -= 1
        else:
            self.color = WHITE

        self.draw(postSurf)


class Text:
    DELETE_FRAME = 120
    SCROLL_FRAME = 2

    def __init__(self, text, pos, scrolling=False, ui=False):
        self.x = pos[0]
        self.y = pos[1]
        self.string = text
        self.width = FONT.render(text, False, WHITE).get_width()
        self.letters = len(text)

        self.scroll_delay = 0
        self.delete_delay = 0

        self.scrolling = scrolling
        if scrolling:
            self.completion = 0
        else:
            self.completion = self.letters

        self.ui = ui

    def render(self):
        if self.ui:
            position = (self.x, self.y)
        else:
            position = camera.pos((self.x, self.y))

        text = FONT_SMALL.render(self.string[: self.completion], False, WHITE)
        postSurf.blit(text, position)

    def scroll(self):
        if self.scrolling:
            if self.scroll_delay < self.SCROLL_FRAME:
                self.scroll_delay += 1
            else:
                self.scroll_delay = 0
                if self.completion < self.letters:
                    self.completion += 1
                else:
                    print("tried to scroll text too far")
        else:
            print("this text is unscrollable")


class TextHandler:
    def __init__(self):
        self.texts = []
        self.text_count = 0

    def add(self, text, pos, scrolling=False, ui=False):
        self.texts.append(Text(text, pos, scrolling, ui))
        self.text_count += 1

    def delete(self, i):
        del self.texts[i]

    def update(self):
        i = self.text_count
        for text in reversed(self.texts):
            i -= 1
            text.render()

            if text.scrolling:
                if text.completion < text.letters:
                    text.scroll()
                else:
                    if text.delete_delay < text.DELETE_FRAME:
                        text.delete_delay += 1
                    else:
                        self.delete(i)


class Body:
    """the skeleton of anything that moves and lives

    COLLISION_STEPS is the amount of substeps to check each step"""
    COLLISION_STEPS = 4

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

        self.moving = False
        self.grid = grid   # reference to the level layout

    def goto(self, x, y):
        """instantly moves the body to a specific position"""
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

        if self.xDir == 0 and self.yDir == 0:
            self.moving = False
        else:
            self.moving = True
            self.goto(self.x, self.y)

    def out_of_bounds(self):
        if player.inShop:
            if self.y > SHOP_ENTER + SCRN_H:
                return True

        if -50 <= self.x < grid.FULL_W + 50 and -50 <= self.y < grid.FULL_H + 50:
            return False

        return True

    def next_x(self):
        """returns the x position of the body on the next frame"""
        return self.x + self.xVel + self.xAcc

    def next_y(self):
        """returns the y position of the body on the next frame"""
        return self.y + self.yVel + self.yAcc

    def pos_center(self):
        """returns the center position of the body in the map"""
        return self.x + int(self.w / 2), self.y + int(self.h / 2)

    def screen_pos(self):
        """returns the position on the screen in relation to the camera"""
        return camera.pos((self.x, self.y))

    def screen_pos_center(self):
        """returns center position in relation to the camera"""
        return camera.pos(self.pos_center())

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

    def collide_stage(self, requester=ALL):
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

        for step in range(1, self.COLLISION_STEPS + 1):
            left_x = self.x
            right_x = left_x + self.w - 1
            top_y = int(self.y + (diff_y * (step / self.COLLISION_STEPS)))
            bottom_y = top_y + self.h - 1

            if dir_y == UP:
                if self.grid.collide_horiz(left_x, right_x, top_y, requester):
                    self.snap_y(row_at(top_y), BOTTOM)

                elif player.coins <= 0 and requester == PLAYER:
                    if not player.inShop:
                        if top_y < y_of(SHOP_ENTER_TILE, BOTTOM):
                            self.snap_y(SHOP_ENTER_TILE, BOTTOM)

            elif dir_y == DOWN:
                if self.grid.collide_horiz(left_x, right_x, bottom_y, requester):
                    self.snap_y(row_at(bottom_y), TOP)

                elif player.coins <= 0 and requester == PLAYER:
                    if player.inShop:
                        if bottom_y >= y_of(SHOP_ENTER_TILE, BOTTOM) - 1:
                            self.snap_y(SHOP_ENTER_TILE+1, TOP)

            left_x = int(self.x + (diff_x * (step / 4)))
            right_x = left_x + self.w - 1
            top_y = self.y
            bottom_y = top_y + self.h - 1

            if dir_x == LEFT:
                if self.grid.collide_vert(left_x, top_y, bottom_y, requester):
                    self.snap_x(col_at(left_x), RIGHT)
            elif dir_x == RIGHT:
                if self.grid.collide_vert(right_x, top_y, bottom_y, requester):
                    self.snap_x(col_at(right_x), LEFT)

    def debug_gridbox(self, surf, color=CYAN):
        pos = camera.pos((self.x, self.y))
        x = pos[0]
        y = pos[1]
        pygame.draw.rect(surf, color, (x, y, self.w, self.h))

    def debug_hitbox(self, surf, color=RED):
        pos = camera.pos((self.hitbox.x, self.hitbox.y))
        x = pos[0]
        y = pos[1]
        pygame.draw.rect(surf, color, (x, y, self.hitbox.w, self.hitbox.h))


class Bullet:
    def __init__(self, x_vel, y_vel, x, y, w, h, extend_x=0, extend_y=0):
        self.body = Body(x, y, w, h, extend_x, extend_y)
        self.body.xVel = x_vel
        self.body.yVel = y_vel

        self.sprite = SpriteInstance(PLAYER_BULLET_SPRITE_SHEET)
        self.sprite.current_frame = random.randint(0, 3)

    def in_wall(self):
        col = col_at(self.body.next_x())
        row = row_at(self.body.next_y())
        if grid.is_solid(col, row):
            return True

        return False


class Player:
    BULLET_SIZE = PIXEL*4
    BULLET_SPEED = 8
    BULLET_DELAY = 15
    INITIAL_COINS = 8
    MAX_CORPSES = 5
    PICKUP_DISTANCE = PIXEL*20

    def __init__(self, x, y, w, h, extend_x=0, extend_y=0):
        """corpse_speeds determines your speed carrying that many corpses"""
        self.body = Body(x, y, w, h, extend_x, extend_y)
        self.sprite = SpriteInstance(PLAYER_SPRITE_SHEET)
        self.bullets = []
        self.dying_bullets = []
        self.bullet_timer = 0

        self.corpse_count = 0
        self.corpses = []
        self.corpse_speeds = (6, 4, 3.2, 2.5, 2, 1.7)

        self.coins = self.INITIAL_COINS
        self.inShop = True
        self.enteredShop = False
        self.exitShop = False

    def update_room(self):
        if self.enteredShop:
            self.enteredShop = False
        if self.exitShop:
            self.exitShop = False

        if self.inShop:
            if self.body.pos_center()[1] > SHOP_ENTER:
                self.inShop = False
                self.enteredShop = True
                self.change_coins(-1)
                coin_handler.add(-1)

        else:
            if self.body.pos_center()[1] < SHOP_ENTER:
                self.inShop = True
                self.enteredShop = True
                self.change_coins(-1)
                coin_handler.add(-1)
                for coin in reversed(range(coin_handler.ground_coin_count)):
                    coin_handler.delete_coin(coin)
                for enemy in reversed(enemyHandler.enemies):
                    if enemy.dead:
                        enemy.delete()

    # movement speed is proportionate to the amount of corpses you carry
    def move_up(self):
        self.body.yVel = -self.corpse_speeds[self.corpse_count]

    def move_down(self):
        self.body.yVel = self.corpse_speeds[self.corpse_count]

    def move_left(self):
        self.body.xVel = -self.corpse_speeds[self.corpse_count]

    def move_right(self):
        self.body.xVel = self.corpse_speeds[self.corpse_count]

    def handle_movement(self):
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.move_up()
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.move_down()
        else:
            self.body.stop_y()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.move_left()
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.move_right()
        else:
            self.body.stop_x()

        self.body.collide_stage(PLAYER)
        self.body.move()

        self.update_room()

    def move_bullets(self):
        i = len(self.bullets)
        for bullet in reversed(self.bullets):
            i -= 1
            if bullet.in_wall():
                self.destroy_bullet(i)
            else:
                bullet.body.move()

    def destroy_bullet(self, index):
        self.dying_bullets.append(self.bullets[index])
        del self.bullets[index]

    def gun_pos(self):
        angle = angle_of(self.body.screen_pos_center(), mouse_pos)
        gun_pos = angle_pos(self.body.pos_center(), angle, PIXEL*7)
        return int(gun_pos[0]), int(gun_pos[1])

    def delta_gun_pos(self):
        player_pos = self.body.screen_pos_center()
        gun_pos = self.gun_pos()
        return int(gun_pos[0] - player_pos[0]), int(gun_pos[1] - player_pos[1])

    def shoot(self):
        angle = angle_of(self.body.screen_pos_center(), mouse_pos)
        vel = angle_pos((0, 0), angle, 8)
        gun_pos = self.gun_pos()
        x = gun_pos[0] - PLAYER_BULLET_SPRITE_SHEET.frame_w / 2
        y = gun_pos[1] - PLAYER_BULLET_SPRITE_SHEET.frame_h / 2
        pos = angle_pos((x, y), angle, 5)

        self.bullets.append(Bullet(vel[0], vel[1], pos[0], pos[1],
                                   self.BULLET_SIZE, self.BULLET_SIZE))

        soundboard.play(SOUND_SHOOT)

    def try_shoot(self):
        if self.bullet_timer == 0 and not self.inShop:
            self.bullet_timer = self.BULLET_DELAY
            self.shoot()
        else:
            self.bullet_timer -= 1

    def draw(self, surf):
        """draws the player"""
        angle = angle_of(camera.pos(player.body.pos_center()), mouse_pos)
        # debug(20, angle)
        if math.pi * -(3/4) < angle < math.pi * -(1/4):
            direction = UP
        elif math.pi * -(1/4) < angle < math.pi * (1/4):
            direction = RIGHT
        elif math.pi * (1/4) < angle < math.pi * (3/4):
            direction = DOWN
        else:
            direction = LEFT

        if self.body.moving:
            # moving animations are in order of direction constants
            self.sprite.change_anim(direction)
        else:
            self.sprite.change_anim(IDLE)
            self.sprite.set_frame(direction - 1)

        x = self.body.x
        y = self.body.y - self.sprite.sheet.z_height

        surf.blit(self.sprite.get_now_frame(), camera.pos((x, y)))

    def draw_gun(self, surf):
        """draw, as in artistically"""
        if mouse_pos[0] < camera.pos(player.body.pos_center())[0]:
            fairy_sprite.change_anim(0)
        else:
            fairy_sprite.change_anim(1)
        fairy_sprite.delay_next(6)

        position = camera.pos(self.gun_pos())
        x = position[0] - fairy_sprite.sheet.frame_w / 2
        y = position[1] - fairy_sprite.sheet.frame_h / 2 - PIXEL
        surf.blit(fairy_sprite.get_now_frame(), (x, y))

    def draw_bullets(self, surf):
        """draws all of the player's bullets"""
        for bullet in self.bullets:
            bullet.sprite.delay_next(2)
            pos = camera.pos((bullet.body.x, bullet.body.y))
            surf.blit(bullet.sprite.get_now_frame(), pos)

        i = len(self.dying_bullets)
        for bullet in reversed(self.dying_bullets):
            i -= 1

            bullet.sprite.change_anim(BULLET_DIE)
            bullet.sprite.delay_next(2)
            pos = camera.pos((bullet.body.x, bullet.body.y))
            surf.blit(bullet.sprite.get_now_frame(), pos)

            last_frame = bullet.sprite.sheet.frame_counts[BULLET_DIE] - 1
            if bullet.sprite.current_frame == last_frame:
                del self.dying_bullets[i]

    def draw_corpses(self, surf):
        y = self.body.y - self.sprite.sheet.z_height + PIXEL

        if self.sprite.current_anim != IDLE and self.sprite.current_frame == 2:
            y -= PIXEL   # account for sprite bobbing during movement

        for i, corpse in enumerate(self.corpses):
            x = self.body.x + (self.body.w / 2 - corpse.body.w / 2)
            y -= corpse.body.h
            corpse.body.goto(x, y)
            corpse.draw(surf)

    def check_hit(self, enemy):
        """determines if a bullet hits an enemy"""
        i = len(self.bullets)
        for bullet in self.bullets:
            i -= 1
            if collide(enemy.body.hitbox, bullet.body.hitbox):
                enemy.health.change(-1)
                self.destroy_bullet(i)

    def select_corpse(self):
        """returns the closest corpse to mouse within pickup range"""
        lowest_dist = SCRN_W * 2   # just a really big number
        lowest_dist_enemy = None
        for enemy in enemyHandler.enemies:
            if enemy.dead:
                player_dist = body_distance(player.body, enemy.body)

                if player_dist < self.PICKUP_DISTANCE:
                    enemy_pos = camera.pos(enemy.body.pos_center())
                    mouse_dist = distance(mouse_pos, enemy_pos)

                    if mouse_dist < lowest_dist:
                        lowest_dist = mouse_dist
                        lowest_dist_enemy = enemy

        return lowest_dist_enemy

    def collect_coins(self):
        i = coin_handler.ground_coin_count
        for coin in reversed(coin_handler.coins):
            i -= 1
            if collide(coin.body.gridbox, player.body.gridbox):
                coin_handler.delete_coin(i)
                self.change_coins(1)

    def pickup_corpse(self, enemy):
        if self.corpse_count < self.MAX_CORPSES:
            self.corpse_count += 1
            self.corpses.append(enemy)
            enemy.delete()

    def sell_corpses(self):
        if self.corpse_count != 0:
            for _ in range(self.corpse_count):
                coin_handler.spawn_coin_drop(SHOP_CENTER)
                coin_handler.add(1)

            self.corpse_count = 0
            self.corpses = []

            soundboard.play(SOUND_SELL)

    def change_coins(self, amount):
        self.coins += amount
        coin_counter.change(amount)

    def update(self):
        if mouse_pressed[0]:
            player.try_shoot()
        else:
            player.bullet_timer = 0

        selected_corpse = self.select_corpse()
        if selected_corpse:
            if right_mouse_released:
                self.pickup_corpse(selected_corpse)
            else:
                selected_corpse.draw_selected()

        if self.inShop and right_mouse_released:
            self.sell_corpses()

        self.sprite.delay_next(4)

        self.handle_movement()
        self.move_bullets()
        self.draw_bullets(postSurf)
        if not self.inShop:
            self.draw_gun(postSurf)

        self.draw(postSurf)
        self.draw_corpses(postSurf)
        self.collect_coins()


class Coin:
    SPEED = 6
    SLOWDOWN = 1.6

    def __init__(self, pos, thrown=False):
        self.body = Body(pos[0], pos[1], PIXEL*7, PIXEL*7)
        self.sprite = SpriteInstance(COIN_SPRITE_SHEET)
        if thrown:
            angle = random.vonmisesvariate(0, 0) - math.pi
            vel = angle_pos((0, 0), angle, self.SPEED)
            self.body.xVel = vel[0]
            self.body.yVel = vel[1]

    def draw(self):
        pos = camera.pos((self.body.x, self.body.y))
        postSurf.blit(self.sprite.get_now_frame(), pos)

    def update(self):
        self.body.xVel /= self.SLOWDOWN
        self.body.yVel /= self.SLOWDOWN
        self.body.collide_stage()
        self.body.move()

        self.draw()
        self.sprite.delay_next(6)


class CoinHandler:
    """stores all the coins on the map"""
    INITIAL_COINS = 8

    def __init__(self):
        self.coins = []
        self.ground_coin_count = 0
        self.coin_count = player.INITIAL_COINS

    def update_coins(self):
        for coin in self.coins:
            coin.update()

    def spawn_coin(self, pos):
        self.ground_coin_count += 1
        self.coins.append(Coin(pos))

    def spawn_coin_drop(self, pos):
        self.ground_coin_count += 1
        self.coins.append(Coin(pos, True))

    def add(self, amount):
        self.coin_count += amount

    def delete_coin(self, i):
        del self.coins[i]
        self.ground_coin_count -= 1

    def out_of_bounds_fix(self):
        i = self.ground_coin_count
        for coin in reversed(self.coins):
            i -= 1
            if grid.tile_at(coin.x, coin.y) == VOID:
                self.delete_coin(i)


class Health:
    PIP_SIZE = PIXEL
    MAX_H = PIXEL*2

    def __init__(self, max_health, current=0):
        self.max = max_health
        self.MAX_W = self.PIP_SIZE * max_health
        if current == 0:
            self.current = max_health
            self.w = self.MAX_W
        else:
            self.current = current
            self.w = self.PIP_SIZE * current

    def change(self, amount):
        self.current += amount
        if self.current > self.max:
            self.current = self.max

        self.w += self.PIP_SIZE * amount

    def set_max(self, value):
        self.max = value
        self.MAX_W = self.PIP_SIZE * value

    def refill(self):
        self.current = self.max
        self.w = self.MAX_W

    def draw(self, surf, pos):
        pygame.draw.rect(surf, RED, (pos[0], pos[1], self.w, self.MAX_H))

    def zero(self):
        if self.current <= 0:
            return True

        return False


class EnemyHandler:
    MAX_ENEMIES = 7

    def __init__(self):
        self.enemies = []
        self.enemy_count = 0
        self.spawn_timer = 120

    def update(self):
        for enemy in self.enemies:
            if not enemy.dead:
                enemy.move()
            else:
                enemy.body.xVel /= 1.17
                enemy.body.yVel /= 1.17
                enemy.body.collide_stage()
                enemy.body.move()

            player.check_hit(enemy)  # hurt and kill enemies
            if enemy.health.zero():
                if not enemy.dead:
                    enemy.die()
                else:
                    enemy.remove()

            if not enemy.removed:
                enemy.draw_health()

            enemy.draw(postSurf)

        if self.spawn_timer == 0:
            if not player.inShop and self.enemy_count < self.MAX_ENEMIES:
                self.random_enemy_spawn()
                self.enemy_count += 1
                self.spawn_timer = 60 + self.enemy_count * 30
        else:
            self.spawn_timer -= 1

    def random_enemy_spawn(self):
        enemy_type = random.randint(0, 0)
        if enemy_type == 0:
            rng = random.random()
            if rng < 0.66:
                x = random.choice((-50, grid.FULL_W + 50))
                y = random.randint(SHOP_ENTER, grid.FULL_H + 50)
            else:
                x = random.randint(-50, grid.FULL_W + 50)
                y = grid.FULL_H + 50

            self.enemies.append(Shadowhound(x, y))

    def kill_all(self):
        for enemy in self.enemies:
            enemy.die()


class Shadowhound:
    SHEET = Spritesheet("shadowhound.png", 11, 8, (2, 6, 6, 6, 6, 3, 3, 6, 6, 4, 4))
    IDLE = 0
    RUN_LEFT = 1
    RUN_RIGHT = 2
    RUN_LEFT_COIN = 3
    RUN_RIGHT_COIN = 4
    DIE_LEFT = 5
    DIE_RIGHT = 6
    DIEDLE_LEFT = 7
    DIEDLE_RIGHT = 8
    REMOVE_LEFT = 9
    REMOVE_RIGHT = 10

    ALIVE_HEALTH = 12
    CORPSE_HEALTH = 2
    DASH_SPEED = 6
    RUN_SPEED = 4
    DASH_TIME = 30
    WAIT_TIME = 90

    def __init__(self, x, y):
        self.body = Body(x, y, PIXEL*11, PIXEL*3)
        self.health = Health(self.ALIVE_HEALTH)
        self.cycle = 120
        self.timer = self.DASH_TIME + self.WAIT_TIME
        self.dead = False

        self.hasCoin = False
        self.movingTowards = True

        self.sprite = SpriteInstance(self.SHEET)
        self.sprite.sheet.init_z_height(self.body)
        self.direction = LEFT
        self.dead_sprite = False

        self.removed = False

        away_angle = -1.5
        while -2.8 < away_angle < 0.8:
            away_angle = math.radians(random.randint(-180, 180))

        vel = angle_pos((0, 0), away_angle, self.RUN_SPEED)
        self.away_x_vel = vel[0]
        self.away_y_vel = vel[1]

    def change_vel(self, angle, speed):
        """change your velocity based on an angle"""
        vel = angle_pos((0, 0), angle, speed)
        self.body.xVel = vel[0]
        self.body.yVel = vel[1]

    def land(self):
        self.body.stop_x()
        self.body.stop_y()

    def move(self):
        if self.movingTowards:
            self.timer -= 1
            if self.timer == 0:
                self.timer = self.DASH_TIME + self.WAIT_TIME
                if self.hasCoin or player.inShop or player.coins <= 0:
                    self.movingTowards = False

                else:
                    player_pos = player.body.pos_center()
                    self_pos = self.body.pos_center()
                    angle = angle_of(self_pos, player_pos)
                    self.change_vel(angle, self.DASH_SPEED)

            elif self.timer > self.WAIT_TIME:
                self.body.collide_stage(ENEMY)
                self.body.move()

                player_hitbox = player.body.hitbox
                self_hitbox = self.body.hitbox
                if not self.hasCoin and collide(self_hitbox, player_hitbox):
                    self.hasCoin = True
                    player.change_coins(-1)

            if player.body.pos_center()[0] < self.body.pos_center()[0]:
                self.direction = LEFT
            else:
                self.direction = RIGHT

        else:
            self.body.xVel = self.away_x_vel
            self.body.yVel = self.away_y_vel
            self.body.collide_stage(ENEMY)
            self.body.move()

            if self.body.xVel > 0:
                self.direction = RIGHT
            else:
                self.direction = LEFT

            if self.body.out_of_bounds():
                if self.hasCoin:
                    coin_handler.add(-1)
                self.delete()
                enemyHandler.enemy_count -= 1

    # foolishly, now i have to make a draw, die, and remove command for
    # EVERY enemy type
    def draw(self, surf):
        if self.removed:
            self.sprite.delay_next(4)

            last_frame = self.sprite.sheet.frame_counts[self.REMOVE_LEFT] - 1

            if self.sprite.current_frame == last_frame:
                if self.sprite.delay == 1:
                    self.delete()
                    return

        elif self.dead:
            if not self.dead_sprite:
                self.sprite.delay_next(4)

                # assumes DIE_LEFT and DIE_RIGHT have the same amount of frames
                last_frame = self.sprite.sheet.frame_counts[self.DIE_LEFT] - 1

                if self.sprite.current_frame == last_frame:
                    if self.sprite.delay == 1:
                        if self.direction == RIGHT:
                            self.sprite.change_anim(self.DIEDLE_RIGHT)
                            self.sprite.current_frame = random.randint(0, 2)
                        else:
                            self.sprite.change_anim(self.DIEDLE_LEFT)
                            self.sprite.current_frame = random.randint(0, 2)

                        self.dead_sprite = True

                else:
                    if self.direction == RIGHT:
                        self.sprite.change_anim(self.DIE_RIGHT)
                    else:
                        self.sprite.change_anim(self.DIE_LEFT)

        else:
            if self.direction == RIGHT:
                anim = self.RUN_RIGHT
            else:
                anim = self.RUN_LEFT

            if self.hasCoin:
                anim += 2

            self.sprite.change_anim(anim)

            if self.movingTowards and not 6 < self.timer <= self.WAIT_TIME:
                self.sprite.delay_next(int(self.DASH_TIME / 6))
            elif self.movingTowards:
                self.sprite.current_frame = 5
            else:
                self.sprite.delay_next(4)

        position = (self.body.x, self.body.y - self.sprite.sheet.z_height)
        position = camera.pos(position)
        surf.blit(self.sprite.get_now_frame(), position)

    def draw_selected(self):
        if self.dead and 7 <= self.sprite.current_anim <= 8:
            anim = self.sprite.current_anim
            frame = self.sprite.current_frame + 3

            pos = (self.body.x, self.body.y - self.sprite.sheet.z_height)
            pos = camera.pos(pos)
            postSurf.blit(self.sprite.sheet.get_frame(anim, frame), pos)

    def draw_health(self):
        x = self.body.pos_center()[0] - int(self.health.MAX_W / 2)
        y = self.body.y - PIXEL * 7
        self.health.draw(postSurf, camera.pos((x, y)))

    def die(self):
        enemyHandler.enemy_count -= 1
        self.dead = True
        self.health.set_max(self.CORPSE_HEALTH)
        self.health.refill()

        if self.hasCoin:
            coin_handler.spawn_coin_drop(self.body.pos_center())
            self.hasCoin = False

    def remove(self):
        self.removed = True
        self.dead = False
        if self.direction == LEFT:
            self.sprite.change_anim(self.REMOVE_LEFT)
        else:
            self.sprite.change_anim(self.REMOVE_RIGHT)

    def delete(self):
        if self in enemyHandler.enemies:
            enemyHandler.enemies.remove(self)


class UnderworldKing:
    sprite = None
    SPEED = 7

    def __init__(self):
        x = grid.FULL_H + 50
        y = grid.FULL_W / 2
        self.dead = False   # a constant value
        self.body = Body(x, y, PIXEL*30, PIXEL*30, PIXEL*-5, PIXEL*-5)

    def move_to(self):
        """move towards the player"""
        angle = angle_of(self.body.pos_center(), player.body.pos_center())
        vel = angle_pos((0, 0), angle, self.SPEED)
        self.body.xVel = vel[0]
        self.body.yVel = vel[1]

    def move(self):
        self.move_to()
        self.body.move()

    def draw(self, surf):
        self.body.debug_gridbox(surf, RED)

    def update(self):
        self.move()
        self.draw(postSurf)

    def collide_player(self):
        if collide(self.body.hitbox, player.body.hitbox):
            return True

        return False


# sound
soundboard = Soundboard()
soundboard.add("shop.wav")
soundboard.add("underworld.wav")
soundboard.add("sell.wav")
soundboard.add("shoot.wav")
soundboard.add("hitwall.wav")
MUSIC_SHOP = 0
MUSIC_UNDERWORLD = 1
SOUND_SELL = 2
SOUND_SHOOT = 3
SOUND_HITWALL = 4
soundboard.play(MUSIC_SHOP, -1)
soundboard.play(MUSIC_UNDERWORLD, -1)
soundboard.sounds[MUSIC_UNDERWORLD].set_volume(0)

# level
SHOP_ENTER = 6 * TILE_H
SHOP_ENTER_TILE = 5

level_background = load_image("level_unfinished_2.png")
level_background.set_colorkey(GREEN)

grid = Grid(15, 20)
grid.change_rect(0, SHOP_ENTER_TILE, 15, 1, PLAYER_WALL)   # outline
grid.change_rect(0, SHOP_ENTER_TILE, 1, 15, PLAYER_WALL)
grid.change_rect(0, SHOP_ENTER_TILE + 14, 15, 1, PLAYER_WALL)
grid.change_rect(14, SHOP_ENTER_TILE, 1, 15, PLAYER_WALL)

grid.change_point(3, SHOP_ENTER_TILE + 3, ALL_WALL)   # pillars
grid.change_point(3, SHOP_ENTER_TILE + 11, ALL_WALL)
grid.change_point(11, SHOP_ENTER_TILE + 3, ALL_WALL)
grid.change_point(11, SHOP_ENTER_TILE + 11, ALL_WALL)

grid.change_rect(3, 0, 8, 1, ALL_WALL)   # shop walls
grid.change_rect(3, 0, 1, SHOP_ENTER_TILE, ALL_WALL)
grid.change_rect(11, 0, 1, SHOP_ENTER_TILE, ALL_WALL)
grid.change_rect(3, SHOP_ENTER_TILE, 9, 1, ALL_WALL)
grid.change_rect(6, SHOP_ENTER_TILE, 3, 1, ENEMY_WALL)   # shop entrance

grid.create_surf()

SHOP_CENTER = (int(grid.FULL_W / 2), int(SHOP_ENTER / 2))
SHOP_LEFT_WALL = TILE_W * 3
SHOP_RIGHT_WALL = TILE_W * 12

# sprites and entities
enemyHandler = EnemyHandler()

PLAYER_SPRITE_SHEET = Spritesheet("player.png", 6, 9, (4, 4, 4, 4, 4))
player = Player(500, 200, PIXEL*6, PIXEL*4, 0, 0)
PLAYER_SPRITE_SHEET.init_z_height(player.body.gridbox)
IDLE = 0

FAIRY_SPRITE_SHEET = Spritesheet("fairy.png", 5, 6, (4, 4))
fairy_sprite = SpriteInstance(FAIRY_SPRITE_SHEET)

PLAYER_BULLET_SPRITE_SHEET = Spritesheet("player_bullet.png", 4, 4, (4, 3))
BULLET_MOVE = 0
BULLET_DIE = 1

COIN_SPRITE_SHEET = Spritesheet("coin.png", 7, 7, (5,))
coin_handler = CoinHandler()
coin_counter = Score(player.coins, (65, 7))
coin_counter_sprite = SpriteInstance(COIN_SPRITE_SHEET)

# misc
SHOP_END = 1
DEATH_END = 2

camera = Camera()
pinhole = Pinhole()
screen_fade = ScreenFade()
text_handler = TextHandler()


def game_loop():
    global keys
    global mouse_pos
    global mouse_pressed
    global right_mouse_released
    global ending

    camera.autolock(grid)
    camera.change_focus(player.body)

    pinhole.set_position((int(125 / 2), int(125 / 2)))

    right_mouse_last = False
    right_mouse_released = False

    text_handler.add("This is a test.", (50, 50), False, True)
    text_handler.add("This is also a text.", (50, 100), True)

    ending = 0
    underworld_king = None

    screen_fade.set_transparency(0)
    screen_fade.fade_from_black()

    while True:
        # mouse handling & right click flag
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        if right_mouse_released:
            right_mouse_released = False
        if right_mouse_last and not mouse_pressed[2]:
            right_mouse_released = True
        right_mouse_last = mouse_pressed[2]

        keys = pygame.key.get_pressed()

        grid.draw(postSurf)
        enemyHandler.update()
        player.update()
        soundboard.update()
        camera.handle()

        coin_handler.update_coins()

        # check for lose conditions
        if not ending:
            if coin_handler.coin_count == 0:
                if player.inShop and not player.corpses:
                    ending = SHOP_END
                elif not player.inShop:
                    ending = DEATH_END
                    enemyHandler.kill_all()
                    enemyHandler.enemy_count = enemyHandler.MAX_ENEMIES
                    underworld_king = UnderworldKing()

        elif ending == DEATH_END:
            underworld_king.update()
            if screen_fade.transparency == 255:
                break
            if underworld_king.collide_player():
                screen_fade.fade_to_black()

        elif ending == SHOP_END:
            screen_fade.fade_to_black()
            if screen_fade.transparency == 255:
                break

        pinhole.update()

        coin_counter.update()
        # coin_counter_sprite.delay_next(6)
        postSurf.blit(coin_counter_sprite.get_now_frame(), (20, 22))

        text_handler.update()
        screen_fade.update()

        debug(0, screen_fade.fade_in)
        debug(1, screen_fade.transparency)
        # debug(0, "FPS: %.2f" % clock.get_fps())
        # debug(2, "gun_pos", player.gun_pos())
        # debug(4, "camera %.2f %.2f" % (camera.body.x, camera.body.y))
        # debug(6, "enemies", enemyHandler.enemies)
        # debug(7, "coins", coin_handler.coin_count)
        # debug(11, "carrying", player.corpses)
        # debug(13, "in_shop?", player.inShop)
        #
        # debug(15, "enemy count", enemyHandler.enemy_count)
        # debug(16, "spawn timer", enemyHandler.spawn_timer)
        #
        # debug(18, "ending", ending)
        #
        # debug(19, "yvel", player.body.y, player.body.yVel)
        #
        # debug(21, "anim frame", player.sprite.current_frame)
        #
        # debug(23, "pinhole radius", pinhole.radius)
        if keys[pygame.K_f]:
            update(True)  # slows down fps
        else:
            update()


game_loop()
