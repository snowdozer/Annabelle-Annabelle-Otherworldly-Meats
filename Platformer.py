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


class Sprite:
    """stores a spritesheet made of all of a thing's animations"""
    def __init__(self, sheet_path, frame_w, frame_h, frame_counts):
        image = pygame.image.load(os.path.join("images", sheet_path))
        self.full_w = PIXEL*image.get_width()
        self.full_h = PIXEL*image.get_height()
        self.surface = pygame.transform.scale(image, (self.full_w, self.full_h))
        self.surface.set_colorkey(GREEN)

        self.frame_w = PIXEL*frame_w
        self.frame_h = PIXEL*frame_h
        self.anim_count = int(self.full_w / frame_w)
        self.frame_counts = frame_counts
        self.z_height = 0

        self.current_frame = 0
        self.current_anim = 0

        self.delay = 0

    def init_z_height(self, body):
        self.z_height = self.frame_h - body.h

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
        distance_x = int((x - self.body.x) / 10)
        distance_y = int((y - self.body.y) / 10)
        debug(5, "camera step distance", distance_x, distance_y)
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
        self.surf = pygame.Surface((self.FULL_W, self.FULL_H))
        self.surf.set_colorkey(GREEN)
        self.surf.fill(GREEN)
        for row in range(self.GRID_H):
            for col in range(self.GRID_W):
                rect = (col * TILE_W, row * TILE_H, TILE_W, TILE_H)
                tile = self.tile_at(col, row)
                if tile == ALL_WALL:
                    pygame.draw.rect(self.surf, WHITE, rect)
                elif tile == PLAYER_WALL:
                    pygame.draw.rect(self.surf, CYAN, rect)
                elif tile == ENEMY_WALL:
                    pygame.draw.rect(self.surf, RED, rect)

    def draw(self, surf):
        surf.blit(self.surf, camera.pos((0, 0)))


def collide(rect1, rect2):
    return pygame.Rect(rect1).colliderect(rect2)


# CELL_W = 10
# CELL_H = 10
# partition = [[[] for y in range(CELL_H)] for x in range(CELL_W)]


class Score:
    """a visual counter"""
    def __init__(self, start_count, pos):
        self.color = WHITE
        self.count = start_count
        self.display_count = start_count

        self.cycle = 15
        self.timer = 0

        self.x = pos[0]
        self.y = pos[1]

    def draw(self, surf):
        text = FONT.render(str(self.display_count), False, self.color)
        surf.blit(text, (self.x, self.y))

    def update(self):
        if self.display_count < self.count:
            if self.timer:
                self.timer -= 1
            else:
                self.timer = self.cycle
                self.display_count += 1
                self.color = SCORE_GREEN

        elif self.display_count > self.count:
            if self.timer:
                self.timer -= 1
            else:
                self.timer = self.cycle
                self.display_count -= 1
                self.color = SCORE_RED

        else:
            if self.timer:
                self.timer -= 1
            else:
                self.timer = 0
                self.color = WHITE

        self.draw(postSurf)


class Body:
    """the skeleton of anything that moves and lives

    COLLISION_STEPS is the amount of substeps to check each step"""
    COLLISION_STEPS = 2

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

        if self.xDir == 0 and self.yDir == 0:
            self.moving = False
        else:
            self.moving = True
            self.goto(self.x, self.y)

    def out_of_bounds(self):
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

    def in_wall(self):
        col = col_at(self.body.next_x())
        row = row_at(self.body.next_y())
        if grid.is_solid(col, row):
            return True

        return False


class Player:
    BULLET_SIZE = PIXEL*5
    BULLET_SPEED = 8
    BULLET_DELAY = 15
    INITIAL_COINS = 8
    MAX_CORPSES = 5
    PICKUP_DISTANCE = PIXEL*20

    def __init__(self, x, y, w, h, extend_x=0, extend_y=0):
        self.body = Body(x, y, w, h, extend_x, extend_y)
        self.sprite = None
        self.bullets = []
        self.bullet_timer = 0

        self.corpse_count = 0
        self.corpses = []

        self.coins = self.INITIAL_COINS
        self.inShop = True
        self.enteredShop = False
        self.exitShop = False

    def init_sprite(self):
        self.sprite = Sprite("player.png", 8, 13, (1, 1, 8, 8))
        self.sprite.init_z_height(self.body)

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

    # movement speed is proportionate to the amount of corpses you carry
    def move_up(self):
        self.body.yVel = -6 + self.corpse_count

    def move_down(self):
        self.body.yVel = 6 - self.corpse_count

    def move_left(self):
        self.body.xVel = -6 + self.corpse_count

    def move_right(self):
        self.body.xVel = 6 - self.corpse_count

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
        del self.bullets[index]

    def gun_pos(self):
        angle = angle_of(self.body.screen_pos_center(), mouse_pos)
        gun_pos = angle_pos(self.body.pos_center(), angle, PIXEL*12)
        return int(gun_pos[0]), int(gun_pos[1])

    def delta_gun_pos(self):
        player_pos = self.body.screen_pos_center()
        gun_pos = self.gun_pos()
        return int(gun_pos[0] - player_pos[0]), int(gun_pos[1] - player_pos[1])

    def shoot(self):
        angle = angle_of(self.body.screen_pos_center(), mouse_pos)
        vel = angle_pos((0, 0), angle, 8)
        pos = angle_pos(self.gun_pos(), angle, 5)

        self.bullets.append(Bullet(vel[0], vel[1], pos[0], pos[1],
                                   self.BULLET_SIZE, self.BULLET_SIZE))

    def try_shoot(self):
        if self.bullet_timer == 0 and not self.inShop:
            self.bullet_timer = self.BULLET_DELAY
            self.shoot()
        else:
            self.bullet_timer -= 1

    def draw(self, surf):
        """draws the player"""
        if mouse_pos[0] < camera.pos(player.body.pos_center())[0]:
            position = (self.body.x, self.body.y - self.sprite.z_height)
            if self.body.moving:
                self.sprite.change_anim(MOVE_LEFT)
            else:
                self.sprite.change_anim(IDLE_LEFT)

        else:
            position = (self.body.x, self.body.y - self.sprite.z_height)
            if self.body.moving:
                self.sprite.change_anim(MOVE_RIGHT)
            else:
                self.sprite.change_anim(IDLE_RIGHT)

        surf.blit(self.sprite.get_now_frame(), camera.pos(position))

    def draw_gun(self, surf):
        """draw, as in artistically"""
        pygame.draw.circle(surf, CYAN, camera.pos(self.gun_pos()), 10)

    def draw_bullets(self, surf):
        """draws all of the player's bullets"""
        for bullet in self.bullets:
            pos = camera.pos((bullet.body.x, bullet.body.y))
            pygame.draw.circle(surf, CYAN, pos, int(self.BULLET_SIZE / 2))

    def draw_corpses(self, surf):
        y = self.body.y - self.sprite.z_height + PIXEL
        for i, corpse in enumerate(self.corpses):
            x = self.body.x + (self.body.w / 2 - corpse.body.w / 2)
            y -= corpse.body.h - PIXEL
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
            if collide(coin.gridbox, player.body.gridbox):
                coin_handler.delete_coin(i)
                self.change_coins(1)

    def pickup_corpse(self, enemy):
        if self.corpse_count < self.MAX_CORPSES:
            self.corpse_count += 1
            self.corpses.append(enemy)
            enemy.remove()

    def sell_corpses(self):
        for _ in range(len(self.corpses)):
            coin_handler.spawn_coin_drop(SHOP_CENTER)
            coin_handler.add(1)

        self.corpse_count = 0
        self.corpses = []

    def change_coins(self, amount):
        self.coins += amount
        coin_counter.count += amount

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
        self.draw(postSurf)
        if not self.inShop:
            self.draw_gun(postSurf)
        self.move_bullets()
        self.draw_bullets(postSurf)
        self.draw_corpses(postSurf)
        self.collect_coins()


class CoinHandler:
    """stores all the coins on the map"""
    INITIAL_COINS = 8
    COIN_SPEED = 5
    COIN_SLOWDOWN = 1.6

    def __init__(self):
        self.coins = []
        self.ground_coin_count = 0
        self.coin_count = player.INITIAL_COINS

    def update_coins(self):
        for coin in self.coins:
            coin.xVel /= self.COIN_SLOWDOWN
            coin.yVel /= self.COIN_SLOWDOWN
            coin.collide_stage()
            coin.move()

            coin.debug_hitbox(postSurf, YELLOW)

    def spawn_coin(self, pos):
        self.ground_coin_count += 1
        self.coins.append(Body(pos[0], pos[1], PIXEL*3, PIXEL*5))

    def spawn_coin_drop(self, pos):
        self.spawn_coin(pos)
        body = self.coins[self.ground_coin_count - 1]
        angle = random.vonmisesvariate(0, 0) - math.pi
        vel = angle_pos((0, 0), angle, self.COIN_SPEED)
        body.xVel = vel[0]
        body.yVel = vel[1]
        print(body.xVel, body.yVel)

    def add(self, amount):
        self.coin_count += amount

    def delete_coin(self, i):
        del self.coins[i]
        self.ground_coin_count -= 1


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
    MAX_ENEMIES = 10

    def __init__(self):
        self.enemies = []
        self.enemy_count = 0
        self.spawn_timer = 120

    def update(self):
        for enemy in self.enemies:
            if not enemy.dead:
                enemy.move()

            player.check_hit(enemy)  # hurt and kill enemies
            if enemy.health.zero():
                if not enemy.dead:
                    enemy.die()
                else:
                    enemy.remove()

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
                y = random.randint(-50, grid.FULL_H + 50)
            else:
                x = random.randint(-50, grid.FULL_W + 50)
                y = grid.FULL_H + 50

            self.enemies.append(Shadowhound(x, y))

    def kill_all(self):
        for enemy in self.enemies:
            enemy.die()


class Shadowhound:
    sprite = None
    ALIVE_HEALTH = 12
    CORPSE_HEALTH = 2
    DASH_SPEED = 7
    RUN_SPEED = 4
    DASH_TIME = 30
    WAIT_TIME = 90

    def __init__(self, x, y):
        self.body = Body(x, y, PIXEL*12, PIXEL*9)
        self.health = Health(self.ALIVE_HEALTH)
        self.cycle = 120
        self.timer = self.DASH_TIME + self.WAIT_TIME
        self.dead = False

        self.hasCoin = False
        self.movingTowards = True
        self.awayAngle = random.vonmisesvariate(3/2 * math.pi, 1) - math.pi

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
                    self.change_vel(self.awayAngle, self.RUN_SPEED)

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

        else:
            self.body.collide_stage(ENEMY)
            self.body.move()

            if self.body.out_of_bounds():
                if self.hasCoin:
                    coin_handler.add(-1)
                self.remove()

    # foolishly, now i have to make a draw, die, and remove command for
    # EVERY enemy type
    def draw(self, surf):
        if self.dead:
            self.body.debug_hitbox(surf, RED)
        elif self.hasCoin:
            self.body.debug_hitbox(surf, YELLOW)
        else:
            self.body.debug_hitbox(surf, CYAN)

    def draw_selected(self):
        self.body.debug_hitbox(postSurf, PALE_RED)

    def draw_health(self):
        x = self.body.pos_center()[0] - int(self.health.MAX_W / 2)
        y = self.body.y - PIXEL * 4
        self.health.draw(postSurf, camera.pos((x, y)))

    def die(self):
        enemyHandler.enemy_count -= 1
        self.dead = True
        self.body.stop_x()
        self.body.stop_y()
        self.health.set_max(self.CORPSE_HEALTH)
        self.health.refill()

        if self.hasCoin:
            coin_handler.spawn_coin_drop(self.body.pos_center())

    def remove(self):
        enemyHandler.enemies.remove(self)


class UnderworldKing:
    sprite = None
    SPEED = 5

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


soundboard = Soundboard()
soundboard.add("shop_demo.wav")
soundboard.add("underworld_demo.wav")
MUSIC_SHOP = 0
MUSIC_UNDERWORLD = 1
soundboard.play(MUSIC_SHOP, -1)
soundboard.play(MUSIC_UNDERWORLD, -1)
soundboard.sounds[MUSIC_UNDERWORLD].set_volume(0)

SHOP_ENTER = 6 * TILE_H
SHOP_ENTER_TILE = 5
grid = Grid(15, 20)   # temporary level
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

enemyHandler = EnemyHandler()

player = Player(500, 200, PIXEL*8, PIXEL*6, 0, 0)
player.init_sprite()
IDLE_LEFT = 0
IDLE_RIGHT = 1
MOVE_LEFT = 2
MOVE_RIGHT = 3

camera = Camera()
camera.autolock(grid)
camera.change_focus(player.body)

right_mouse_last = False
right_mouse_released = False

coin_handler = CoinHandler()
coin_counter = Score(player.coins, (30, 20))

ending = 0
SHOP_END = 1
DEATH_END = 2
underworld_king = None

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

    coin_counter.update()
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

    if underworld_king:
        underworld_king.update()
        if underworld_king.collide_player():
            break

    debug(0, "FPS: %.2f" % clock.get_fps())
    debug(2, "gun_pos", player.gun_pos())
    debug(4, "camera", camera.body.x, camera.body.y)
    debug(6, "enemies", enemyHandler.enemies)
    debug(7, "coins", coin_handler.coin_count)
    debug(11, "carrying", player.corpses)
    debug(13, "in_shop?", player.inShop)

    debug(15, "enemy count", enemyHandler.enemy_count)
    debug(16, "spawn timer", enemyHandler.spawn_timer)

    debug(18, "ending", ending)

    debug(19, "yvel", player.body.y, player.body.yVel)
    if keys[pygame.K_f]:
        update(True)   # slows down fps
    else:
        update()
