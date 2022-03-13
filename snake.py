#!/usr/bin/env python3

import pygame
import time
from random import randint


def two_digits(a):
    a = str(int(a))
    if len(a) == 1:
        return "0" + a
    else:
        return a


def decimals(a):
    a = str(a)
    b = ""
    for i in range(len(a)):
        b = a[-(i + 1)] + b
        if (-(i + 1)) % 3 == 0 and i + 1 != len(a):
            b = "." + b
    return b


class Player:  # Snake
    def __init__(self, grid, border, color_head, color_tail):
        self.grid = grid
        self.border = border
        self.velocity = grid
        self.color_head = color_head
        self.color_tail = color_tail
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.left_current = False
        self.right_current = False
        self.up_current = False
        self.down_current = False
        self.x = int((settings.game_width - self.grid) / 2 + settings.game_x)
        self.y = int((settings.game_height - self.grid) / 2 + settings.game_y)
        self.xyList = [(self.x + self.border, self.y + self.border, self.grid - 2 * self.border, self.grid - 2 * self.border)]
        self.fpsCounter = 0
        self.highscore_read()

    def move(self):
        self.left_current = self.left
        self.right_current = self.right
        self.up_current = self.up
        self.down_current = self.down
        global game_over
        if self.left_current:
            self.x -= self.velocity
        elif self.right_current:
            self.x += self.velocity
        elif self.up_current:
            self.y -= self.velocity
        elif self.down_current:
            self.y += self.velocity
        self.location = (self.x + self.border, self.y + self.border, self.grid - 2 * self.border, self.grid - 2 * self.border)

        if self.x == settings.game_x - self.grid or self.x == settings.game_width + self.grid or self.y == settings.game_y - self.grid or self.y == settings.game_height + settings.label_height:
            game_over = True

        for pair in self.xyList:  # collision with itself
            if self.location == pair and len(self.xyList) != 1:
                game_over = True

        self.xyList.append(self.location)

        if self.x == Apple.x and self.y == Apple.y:
            Apple.move()
        else:
            self.xyList.pop(0)

    def draw(self):
        for pair in self.xyList:
            if self.xyList.index(pair) != len(self.xyList) - 1:
                pygame.draw.rect(window, self.color_tail, pair)
        pygame.draw.rect(window, self.color_head, self.xyList[len(self.xyList) - 1])

    def highscore_read(self):  # I know, it shouldn't be here
        highscore_file = open("snake_highscore.txt", "a")  # create an empty file, if it does not exist
        highscore_file.close()

        highscore_file = open("snake_highscore.txt", "r")
        line = highscore_file.readline()
        if line == "":
            self.highscore = 0
        else:
            self.highscore = int(line)

        highscore_file.close()

    def highscore_write(self):
        highscore_file = open("snake_highscore.txt", "w")
        highscore_file.write(str(len(Snake.xyList)))


class Target:  # Apple
    def __init__(self, grid, border, color_apple):
        self.grid = grid
        self.border = border
        self.color = color_apple
        self.move()

    def move(self):
        self.x = randint(0, settings.game_width / self.grid - 1) * self.grid + settings.game_x
        self.y = randint(0, settings.game_height / self.grid - 1) * self.grid + settings.game_y
        self.location = (self.x + self.border, self.y + self.border, self.grid - 2 * self.border, self.grid - 2 * self.border)
        for pair in Snake.xyList:
            if pair == self.location:
                self.move()
                break

    def draw(self):
        pygame.draw.rect(window, self.color, self.location)


class TextBox:  # TopBar
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self):
        time = myfont.render("time: " + two_digits(Snake.fpsCounter / settings.fps // 60) + ":" + two_digits(Snake.fpsCounter / settings.fps % 60), True, settings.color_font)
        window.blit(time, (settings.grid, int((settings.label_height - text_height)/2)))

        score_width, score_height = myfont.size("score: " + decimals(len(Snake.xyList)))
        score = myfont.render("score: " + decimals(len(Snake.xyList)), True, settings.color_font)
        window.blit(score, ((settings.label_width - score_width) / 2, int((settings.label_height - text_height)/2)))

        highscore_width, highscore_height = myfont.size("highscore: " + decimals(Snake.highscore))
        highscore = myfont.render("highscore: " + decimals(Snake.highscore), True, settings.color_font)
        window.blit(highscore, (settings.label_width - settings.grid - highscore_width, int((settings.label_height - text_height)/2)))


def redrawGameWindow():
    window.fill(settings.color_window_background)
    pygame.draw.rect(window, settings.color_game_background, (settings.game_x, settings.game_y, settings.game_width, settings.game_height))
    Snake.draw()
    Apple.draw()
    TopBar.draw()
    pygame.display.update()


class settings:
    grid = 25  # 20
    grid_border = 2
    window_width = grid * 29
    window_height = grid * 24
    label_x = 0
    label_y = 0
    label_width = window_width
    label_height = 2 * grid
    game_x = grid
    game_y = label_height
    game_width = window_width - 2 * grid  # odd multiples of grid
    game_height = window_height - label_height - grid  # odd multiples of grid

    color_window_background = (1, 170, 64)
    color_game_background = (0, 0, 0)
    color_snake_head = (255, 255, 255)
    color_snake_tail = (0, 255, 0)
    color_apple = (255, 0, 0)
    color_font = (255, 255, 255)

    fps = 60
    move_delay = fps / 3  # or 4


pygame.display.init()
clock = pygame.time.Clock()
window = pygame.display.set_mode((settings.window_width, settings.window_height))
pygame.display.set_caption("Snake by Michał v0.3")

pygame.font.init()
myfont = pygame.font.SysFont("Verdana", settings.grid, bold=True)
text_width, text_height = myfont.size("A")

TopBar = TextBox(settings.label_x, settings.label_y, settings.label_width, settings.label_height)

Snake = Player(settings.grid, settings.grid_border, settings.color_snake_head, settings.color_snake_tail)
Apple = Target(settings.grid, settings.grid_border, settings.color_apple)

game_over = False
while not game_over:
    clock.tick(settings.fps)

    if Snake.fpsCounter % settings.move_delay == 0:
        redrawGameWindow()
    Snake.fpsCounter += 1

    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
            game_over = True

    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not Snake.right_current:
        Snake.left = True
        Snake.right = False
        Snake.up = False
        Snake.down = False
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not Snake.left_current:
        Snake.left = False
        Snake.right = True
        Snake.up = False
        Snake.down = False
    if (keys[pygame.K_UP] or keys[pygame.K_w]) and not Snake.down_current:
        Snake.left = False
        Snake.right = False
        Snake.up = True
        Snake.down = False
    if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and not Snake.up_current:
        Snake.left = False
        Snake.right = False
        Snake.up = False
        Snake.down = True

    if Snake.fpsCounter % settings.move_delay == 0:
        Snake.move()


if len(Snake.xyList) > Snake.highscore:
    Snake.highscore_write()

time.sleep(4)
pygame.quit()
