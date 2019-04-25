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

# TILE TYPES
VOID = 0
EMPTY = 1
WALL = 2

# MISC / UNSORTED
GRAVITY = 0.3

# INITIALIZATION
pygame.init()
postSurf = pygame.display.set_mode((SCRN_W, SCRN_H))

clock = pygame.time.Clock()
TAHOMA = pygame.font.SysFont("Tahoma", 10)


def update(slow_down=False):
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
    string = ""
    for arg in args:
        string += repr(arg) + " "
    text = TAHOMA.render(repr(string), False, WHITE)
    postSurf.blit(text, (10, num * 10 + 10))


def col_at(x):
    return int(x // TILE_W)


def row_at(y):
    return int(y // TILE_H)


def x_of(col, direction=LEFT):
    if direction == LEFT:
        return col * TILE_W

    elif direction == RIGHT:
        return col * TILE_W + TILE_W


def y_of(row, direction=UP):
    if direction == UP:
        return row * TILE_H

    elif direction == DOWN:
        return row * TILE_H + TILE_H


class Grid:
    """the grid where all the tiles in the level are placed"""
    def __init__(self, width, height):
        self.GRID_W = width
        self.GRID_H = height
        self.grid = [[0 for _ in range(height)] for _ in range(width)]

    def add_rect(self, x, y, w, h, kind=WALL):
        for col in range(x, x + w):
            for row in range(y, y + h):
                if not self.out_of_bounds(col, row):
                    self.grid[col][row] = kind
                else:
                    print("You attempted to add a rect out of bounds.")

    def out_of_bounds(self, col, row):
        if 0 <= col < self.GRID_W and 0 <= row < self.GRID_H:
            return False

        return True

    def tile_at(self, col, row):
        if not self.out_of_bounds(col, row):
            return self.grid[col][row]

        return VOID

    def draw(self):
        for row in range(self.GRID_H):
            for col in range(self.GRID_W):
                if self.tile_at(col, row) == WALL:
                    rect = (col * TILE_W, row * TILE_H, TILE_W, TILE_H)
                    pygame.draw.rect(postSurf, WHITE, rect)


class Body:
    """the skeleton of anything that moves and lives"""
    def __init__(self, x, y, w, h, extendx=0, extendy=0):
        self.x = x
        self.y = y
        self.xVel = 0
        self.yVel = 0
        self.xAcc = 0
        self.yAcc = 0

        self.w = w
        self.h = h
        self.extendx = extendx
        self.extendy = extendy
        self.gridbox = pygame.Rect(x, y, w, h)
        self.hitbox = pygame.Rect(x - extendx, y - extendy,
                                  w + extendx*2, h + extendy*2)

        self.grounded = False

    def goto(self, x, y):
        self.x = x
        self.y = y
        self.gridbox.x = self.x
        self.gridbox.y = self.y
        self.hitbox.x = self.x - self.extendx
        self.hitbox.y = self.y - self.extendy

    def move(self):
        self.xVel += self.xAcc
        self.yVel += self.yAcc
        self.x += self.xVel
        self.y += self.yVel

        self.goto(self.x, self.y)

    def next_x(self):
        return self.x + self.xVel + self.xAcc

    def next_y(self):
        return self.y + self.yVel + self.yAcc

    def stop_x(self):
        self.xVel = 0
        self.xAcc = 0

    def stop_y(self):
        self.yVel = 0
        self.yAcc = 0

    def snap(self, direction, col, row):
        """snaps you to a specific side of a tile"""
        if direction == LEFT:
            self.goto(x_of(col - 1, RIGHT) - self.w, self.y)
            self.stop_x()

        elif direction == RIGHT:
            self.goto(x_of(col + 1, LEFT), self.y)
            self.stop_x()

        elif direction == UP:
            self.goto(self.x, y_of(row - 1, DOWN) - self.h)
            self.stop_y()

        elif direction == DOWN:
            self.goto(self.x, y_of(row + 1, UP))
            self.stop_y()

    def collide_stage(self):
        if self.xVel > 0:
            col = col_at(self.next_x() + self.w)
            row = row_at(self.next_y())

            if grid.tile_at(col, row) == WALL:
                self.snap(LEFT, col, row)
                self.stop_x()

        elif self.xVel < 0:
            col = col_at(self.next_x())
            row = row_at(self.next_y())

            if grid.tile_at(col, row) == WALL:
                self.snap(RIGHT, col, row)
                self.stop_x()

        if self.yVel > 0:
            col = col_at(self.next_x())
            row = row_at(self.next_y() + self.h)

            if grid.tile_at(col, row) == WALL:
                self.snap(UP, col, row)
                self.stop_y()

                self.grounded = True

        elif self.yVel < 0:
            col = col_at(self.next_x())
            row = row_at(self.next_y())

            if grid.tile_at(col, row) == WALL:
                self.snap(DOWN, col, row)
                self.stop_y()


class Player:
    def __init__(self):
        self.body = Body(200, 400, 8, 8, -2, -2)

    def move(self):
        self.body.yAcc = GRAVITY
        self.body.collide_stage()
        self.body.move()

    def draw(self):
        pygame.draw.rect(postSurf, CYAN, self.body.gridbox)


grid = Grid(50, 50)
grid.add_rect(10, 45, 20, 1)
grid.add_rect(20, 43, 10, 1)
player = Player()

while True:
    keys = pygame.key.get_pressed()

    if keys[pygame.K_f]:
        update(True)
    else:
        update()

    if keys[pygame.K_w] and player.body.grounded:
        player.body.grounded = False
        player.body.yVel = -5
    if keys[pygame.K_a]:
        player.body.xVel = -4
    elif keys[pygame.K_d]:
        player.body.xVel = 4
    else:
        player.body.xVel = 0

    player.move()
    grid.draw()
    player.draw()

    debug(0, player.body.yVel)
    debug(1, player.body.xVel)
