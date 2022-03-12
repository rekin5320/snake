#!/usr/bin/env python3

import pygame
import time
from random import randint


class Player:  # Snake
    def __init__(self, grid):
        self.grid = grid
        self.velocity = grid
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.left_current = False
        self.right_current = False
        self.up_current = False
        self.down_current = False
        self.x = int((width - self.grid) / 2)
        self.y = int((height - self.grid) / 2)
        self.xyList = [(int((width - self.grid) / 2), int((height - self.grid) / 2), self.grid, self.grid)]
        self.fps_counter = 0

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
        self.location = (self.x, self.y, self.grid, self.grid)

        if self.x == -self.grid or self.x == width or self.y == -self.grid or self.y == height:
            game_over = True

        for pair in self.xyList:  # collision with itself
            if self.location == pair and len(self.xyList) != 1:
                game_over = True

        if self.x == Apple.x and self.y == Apple.y:
            Apple.move()
        else:
            self.xyList.pop(0)

        self.xyList.append(self.location)

    def draw(self):
        for pair in self.xyList:
            if self.xyList.index(pair) != len(self.xyList) - 1:
                pygame.draw.rect(window, (0, 255, 0), pair)
        pygame.draw.rect(window, (255, 255, 255), self.xyList[len(self.xyList) - 1])


class Target:  # Apple
    def __init__(self, grid):
        self.grid = grid
        self.move()

    def move(self):
        self.x = randint(0, width / self.grid - 1) * self.grid
        self.y = randint(0, height / self.grid - 1) * self.grid
        self.location = (self.x, self.y, self.grid, self.grid)
        for pair in Snake.xyList:
            if pair == self.location:
                self.move()
                break

    def draw(self):
        pygame.draw.rect(window, (255, 0, 0), self.location)


def redrawGameWindow():
    window.fill((0, 0, 0))
    Snake.draw()
    Apple.draw()
    pygame.display.update()


grid = 20
width = 41 * grid  # odd multiples of grid
height = 31 * grid
fps = 40

pygame.display.init()
clock = pygame.time.Clock()
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake by Michał v0.1")

Snake = Player(grid)
Apple = Target(grid)


game_over = False
while not game_over:
    clock.tick(fps)

    if Snake.fps_counter % (fps / 4) == 0:
        redrawGameWindow()
    Snake.fps_counter += 1

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

    if Snake.fps_counter % (fps / 4) == 0:
        Snake.move()


time.sleep(4)
pygame.quit()
