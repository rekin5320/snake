#!/usr/bin/env python3

import pygame
from random import randint
import os
import signal
import multiprocessing
from playsound import playsound
import requests


######## Classes and definitions ########

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
            b = " " + b
    return b


def Pkill(process_name):
    if os.name == "posix":  # for Linux and Mac it prints "posix", for Windows "nt"
        os.kill(process_name.pid, signal.SIGKILL)
    else:
        process_name.terminate()


class Button:
    def __init__(self, x, y, width, height, color1, color2, color_text, text, font_size, command):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.button_color1 = color1
        self.button_color2 = color2
        self.color_text = color_text
        self.font = pygame.font.SysFont("Verdana", font_size, bold=True)
        self.text_width, self.text_height = self.font.size(text)
        self.text = self.font.render(text, True, color_text)
        self.command = command

    def click(self):
        if self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height:
            exec(self.command, globals())

    def draw(self):
        if self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height:
            pygame.draw.rect(window, self.button_color2, (self.x, self.y, self.width, self.height))
        else:
            pygame.draw.rect(window, self.button_color1, (self.x, self.y, self.width, self.height))
        window.blit(self.text, (int((settings.window_width - self.text_width) / 2), self.y + (settings.button_height - self.text_height) / 2))


class Text:
    def __init__(self, text, color, font_size):
        self.font = pygame.font.SysFont("Verdana", font_size, bold=True)
        self.text_width, self.text_height = self.font.size(text)
        self.text = self.font.render(text, True, color)

    def draw(self, x, y):
        window.blit(self.text, (x, y))


class File:  # Data
    def __init__(self):
        self.path = settings.path_highscore

    def read(self):
        file = open(self.path, "r")
        line = file.readline()
        if line == "":
            self.highscore = 0
        else:
            self.highscore = int(line)

        file.close()

    def write(self):
        self.highscore = Snake.score
        file = open(self.path, "w")
        file.write(str(Snake.score))


def checkFiles():
    if not os.path.exists(settings.path_gameDirectory):
        os.mkdir(settings.path_gameDirectory)

    if not os.path.exists(settings.path_highscore):
        file = open(settings.path_highscore, "a")
        file.close()

    if not os.path.exists(settings.path_musicDirectory):
        os.mkdir(settings.path_musicDirectory)

    if not os.path.exists(settings.path_music_Game):
        download = requests.get(settings.url_music_Game, allow_redirects=True)
        open(settings.path_music_Game, "wb").write(download.content)

    if not os.path.exists(settings.path_music_GameOver):
        download = requests.get(settings.url_music_GameOver, allow_redirects=True)
        open(settings.path_music_GameOver, "wb").write(download.content)
    print("Checking files done")


def loading_screen(function, text):
    process = multiprocessing.Process(target=function)
    process.daemon = True
    process.start()
    time = 0
    Loading0 = Text(text, settings.color_font, settings.font_size_loading)
    Loading1 = Text(text + ".", settings.color_font, settings.font_size_loading)
    Loading2 = Text(text + "..", settings.color_font, settings.font_size_loading)
    Loading3 = Text(text + "...", settings.color_font, settings.font_size_loading)

    while process.is_alive():
        clock.tick(settings.fps)
        window.fill(settings.color_window_background)
        if time // settings.fps % 4 == 0:
            Loading0.draw((settings.window_width - Loading0.text_width) / 2, (settings.window_height - Loading0.text_height) / 2)
        elif time // settings.fps % 4 == 1:
            Loading1.draw((settings.window_width - Loading1.text_width) / 2, (settings.window_height - Loading1.text_height) / 2)
        elif time // settings.fps % 4 == 2:
            Loading2.draw((settings.window_width - Loading2.text_width) / 2, (settings.window_height - Loading2.text_height) / 2)
        elif time // settings.fps % 4 == 3:
            Loading3.draw((settings.window_width - Loading3.text_width) / 2, (settings.window_height - Loading3.text_height) / 2)
        pygame.display.update()
        time += 1


class Player:  # Snake
    def __init__(self, grid, border, color_head, color_tail):
        self.grid = grid
        self.border = border
        self.velocity = grid
        self.color_head = color_head
        self.color_tail = color_tail
        self.reinit()

    def reinit(self):
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
        self.score = 1

    def move(self):
        global game_notOver
        self.left_current = self.left
        self.right_current = self.right
        self.up_current = self.up
        self.down_current = self.down

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
            game_notOver = False

        for pair in self.xyList:  # collision with itself
            if self.location == pair and len(self.xyList) != 1:
                game_notOver = False

        self.xyList.append(self.location)

        if self.x == Apple.x and self.y == Apple.y:  # ate the apple
            self.score += 1
            Apple.move()
        else:
            self.xyList.pop(0)

    def draw(self):
        for pair in self.xyList:
            if self.xyList.index(pair) != len(self.xyList) - 1:
                pygame.draw.rect(window, self.color_tail, pair)
        pygame.draw.rect(window, self.color_head, self.xyList[len(self.xyList) - 1])


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


class Bar:  # TopBar
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self):
        Time = Text("time: " + two_digits(Snake.fpsCounter / settings.fps // 60) + ":" + two_digits(Snake.fpsCounter / settings.fps % 60), settings.color_font, settings.label_font_size)
        Time.draw(1.4 * settings.grid, int((self.height - Time.text_height)/2))

        Score = Text("score: " + decimals(Snake.score), settings.color_font, settings.label_font_size)
        Score.draw(int((self.width - Score.text_width) / 2), int((self.height - Score.text_height)/2))

        Highscore = Text("highscore: " + decimals(Data.highscore), settings.color_font, settings.label_font_size)
        Highscore.draw(self.width - settings.grid - Highscore.text_width - 0.4 * settings.grid, int((self.height - Highscore.text_height)/2))


def gameOverText():
    GameOver.draw((settings.window_width - GameOver.text_width) / 2, (settings.window_height - GameOver.text_height) / 2)
    if Snake.score > Data.highscore:
        Data.write()
        NewHigscoreText = Text("new highscore: " + str(Snake.score), settings.color_newhighscore, settings.font_size_newhighscore)
        NewHigscoreText.draw((settings.window_width - NewHigscoreText.text_width) / 2, (settings.window_height - GameOver.text_height) / 2 - GameOver.text_height + NewHigscoreText.text_height - 10)
    pygame.display.update()


def music_Game():
    while True:
        playsound(settings.path_music_Game)


########### Scenes managing ###########

def menu_main():
    global menu
    global mouse
    menu = True
    while menu:
        clock.tick(settings.fps)

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                menu = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                ButtonPlay.click()  # Game
                ButtonExit.click()  # Exit

        if keys[pygame.K_q]:
            game_main()

        menu_redraw()


def menu_redraw():
    window.fill(settings.color_window_background)
    SnakeLogo.draw((settings.window_width - SnakeLogo.text_width) / 2, int(settings.grid * 3.8))
    ButtonPlay.draw()
    ButtonExit.draw()
    Author.draw(settings.window_width - Author.text_width - int(0.4 * settings.grid), settings.window_height - Author.text_height - int(0.4 * settings.grid))
    pygame.display.update()


def game_main():
    global game_notOver
    Data.read()
    musicGame = multiprocessing.Process(target=music_Game)
    musicGame.daemon = True
    musicGame.start()
    Snake.reinit()
    Apple.move()
    game_notOver = True

    while game_notOver:
        clock.tick(settings.fps)

        if Snake.fpsCounter % settings.move_delay == 0:
            game_redraw()
        Snake.fpsCounter += 1

        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                game_notOver = False

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

    Pkill(musicGame)
    gameOverText()
    playsound(settings.path_music_GameOver)
    # pygame.time.wait(3650)  # unnecessary, because playing sound stops code execution


def game_redraw():
    window.fill(settings.color_window_background)
    pygame.draw.rect(window, settings.color_game_background, (settings.game_x, settings.game_y, settings.game_width, settings.game_height))
    Snake.draw()
    Apple.draw()
    TopBar.draw()
    pygame.display.update()


############## Settings ##############

class settings:
    grid = 25
    grid_border = 2
    window_width = grid * 33
    window_height = grid * 26
    label_x = 0
    label_y = 0
    label_width = window_width
    label_height = 2 * grid
    label_font_size = int(grid * 1.04)
    game_x = grid
    game_y = label_height
    game_width = window_width - 2 * grid  # odd multiples of grid
    game_height = window_height - label_height - grid  # odd multiples of grid

    color_window_background = (1, 170, 64)
    color_game_background = (0, 0, 0)
    color_snake_head = (255, 255, 255)
    color_snake_tail = (0, 255, 0)
    color_apple = (255, 0, 0)
    color_button = (254, 151, 12)
    color_button_pointed = (183, 111, 15)
    color_font = (255, 255, 255)
    color_gameover = (255, 0, 0)
    color_newhighscore = (0, 0, 255)
    color_snakeLogo = (255, 255, 255)
    color_author = (200, 200, 200)

    font_size_loading = 35
    font_size_gameover = 70
    font_size_newhighscore = 33
    font_size_snakeLogo = 60
    font_size_author = 21

    button_width = grid * 10
    button_height = grid * 4
    button_text_size = 34
    button_text_color = (255, 255, 255)

    ButtonPlay_y = 245
    ButtonExit_y = 415

    path_gameDirectory = os.path.expanduser("~/.snake")
    path_highscore = path_gameDirectory + "/.snake_data"  # os.path.expanduser("~/.snake/.snake_data")
    path_musicDirectory = path_gameDirectory + "/music"  # os.path.expanduser("~/.snake/music")
    path_music_Game = path_musicDirectory + "/Tristan Lohengrin - Happy 8bit Loop 01.mp3"  # os.path.expanduser("~/.snake/music/Tristan Lohengrin - Happy 8bit Loop 01.mp3")
    path_music_GameOver = path_musicDirectory + "/Sad Trombone Wah Wah Wah Fail Sound Effect.mp3"  # os.path.expanduser("~/.snake/music/Sad Trombone Wah Wah Wah Fail Sound Effect.mp3")

    url_music_Game = "https://drive.google.com/u/0/uc?id=12iQh-5UzBuTLsWbTAeHemYWlmwHm0USr&export=download"
    url_music_GameOver = "https://drive.google.com/u/0/uc?id=12SbYvszlHOUjhjiWk4bEo1pjqkjTaI1y&export=download"

    fps = 60
    movesPerSecond = 3  # or 4 (fps divisor)
    move_delay = fps / movesPerSecond


############# Main code #############

pygame.display.init()
pygame.font.init()
clock = pygame.time.Clock()
window = pygame.display.set_mode((settings.window_width, settings.window_height))
pygame.display.set_caption("Snake by Michał v0.5")

loading_screen(checkFiles, "Loading")

Data = File()

GameOver = Text("GAME  OVER", settings.color_gameover, settings.font_size_gameover)
SnakeLogo = Text("Snake Game", settings.color_snakeLogo, settings.font_size_snakeLogo)
Author = Text("Michał Machnikowski 2021", settings.color_author, settings.font_size_author)

ButtonPlay = Button(int((settings.window_width - settings.button_width) / 2), settings.ButtonPlay_y, settings.button_width, settings.button_height, settings.color_button, settings.color_button_pointed, settings.button_text_color, "Play", settings.button_text_size, "game_main()")
ButtonExit = Button(int((settings.window_width - settings.button_width) / 2), settings.ButtonExit_y, settings.button_width, settings.button_height, settings.color_button, settings.color_button_pointed, settings.button_text_color, "Exit", settings.button_text_size, "menu = False")

Snake = Player(settings.grid, settings.grid_border, settings.color_snake_head, settings.color_snake_tail)
Apple = Target(settings.grid, settings.grid_border, settings.color_apple)
TopBar = Bar(settings.label_x, settings.label_y, settings.label_width, settings.label_height)

menu_main()

pygame.quit()