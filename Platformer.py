import pygame
import sys

# CONSTANTS
# BASIC VISUALS
SCRN_W = 500
SCRN_H = 500
TILE_W = 10
TILE_H = 10
FPS = 60
DEBUG_FPS = 5

# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
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

# INITIALIZATION
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
    text = TAHOMA.render(repr(string), False, WHITE)
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


class Grid:
    """the grid where all the tiles in the level are placed"""
    def __init__(self, width, height):
        self.GRID_W = width
        self.GRID_H = height
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
            print("change_point() tried to add a tile out of bounds")

    def change_rect(self, x, y, w, h, kind):
        """places a rectangle of tiles at the given coordinates"""
        for col in range(x, x + w):
            for row in range(y, y + h):
                if not self.out_of_bounds(col, row):
                    self.grid[col][row] = kind
                else:
                    print("add_rect() tried to add a tile out of bounds.")

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

        debug(15, diff_x)

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

            debug(step + 10, left_x, right_x)

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


class Player:
    def __init__(self, x, y, w, h, extend_x=0, extend_y=0):
        self.body = Body(x, y, w, h, extend_x, extend_y)

    def move(self):
        if not self.body.grounded:
            self.body.yAcc = GRAVITY
        self.body.collide_stage()
        debug(5, "xVel:", self.body.xVel)
        debug(6, "yVel:", self.body.yVel)
        self.body.move()

    def draw(self):
        pygame.draw.rect(postSurf, CYAN, self.body.gridbox)


grid = Grid(50, 50)
grid.change_rect(10, 42, 10, 1, WALL)
grid.change_rect(13, 45, 20, 1, WALL)
grid.change_rect(18, 48, 30, 1, WALL)
grid.change_rect(40, 40, 5, 10, WALL)
player = Player(380, 400, 10, 10, -2, -2)
print(player.body.w, player.body.h)

while True:
    keys = pygame.key.get_pressed()

    if keys[pygame.K_w] and player.body.grounded:
        player.body.grounded = False
        player.body.yVel = -8
    if keys[pygame.K_a]:
        player.body.xVel = -3
    elif keys[pygame.K_d]:
        player.body.xVel = 3
    else:
        player.body.xVel = 0

    player.move()

    grid.draw()
    player.draw()

    debug(0, "xDir:", player.body.xDir)
    debug(1, "yDir:", player.body.yDir)
    debug(2, "grounded:", player.body.grounded)

    if keys[pygame.K_f]:
        update(True)
    else:
        update()
