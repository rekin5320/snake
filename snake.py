#!/usr/bin/env python3

import base64
import json
import logging.handlers
import os
from pathlib import Path
import platform
from random import randint
import sys
import threading
import traceback
import webbrowser

import pygame
import requests


######## Classes and definitions ########

def decimals(a):
    a = str(a)
    b = ""
    for i in range(len(a)):
        b = a[-(i + 1)] + b
        if (-(i + 1)) % 3 == 0 and i + 1 != len(a):
            b = f" {b}"
    return b


class MyThread(threading.Thread):
    def run(self):
        try:
            threading.Thread.run(self)
        except Exception as err:
            self.error = err
            self.traceback = traceback.format_exc()
        else:
            self.error = False


def base64_encode(text):
    encodedtext_bytes = base64.b64encode(text.encode("utf-8"))
    encodedtext = str(encodedtext_bytes, "utf-8")
    return encodedtext


def base64_decode(text):
    decodedtext_bytes = base64.b64decode(text)
    decodedtext = str(decodedtext_bytes, "utf-8")
    return decodedtext


class Button:
    def __init__(self, x, y, width, height, color1, color2, color_text, text, font_size, command):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.button_color1 = color1
        self.button_color2 = color2
        self.color_text = color_text
        self.font = pygame.font.SysFont(settings.font_name, font_size, bold=True)
        self.text_width, self.text_height = self.font.size(text)
        self.text = self.font.render(text, True, color_text)
        self.command = command

    def click(self):
        if self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height:
            self.command()

    def draw(self):
        if self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height:
            pygame.draw.rect(window, self.button_color2, (self.x, self.y, self.width, self.height))
        else:
            pygame.draw.rect(window, self.button_color1, (self.x, self.y, self.width, self.height))
        window.blit(self.text, (self.x + (self.width - self.text_width) / 2, self.y + (self.height - self.text_height) / 2))


class ButtonSpeed:
    def __init__(self, x, y, width, height, color1, color2, color_text, font_size, desired_value):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.button_color1 = color1
        self.button_color2 = color2
        self.color_text = color_text
        self.font = pygame.font.SysFont(settings.font_name, font_size, bold=True)
        self.text_width, self.text_height = self.font.size(str(desired_value))
        self.text = self.font.render(str(desired_value), True, color_text)
        self.desired_value = desired_value

    def click(self):
        if self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height:
            settings.speed = self.desired_value
            settings.move_delay = settings.fps / settings.speed
            logger.info(f"Changed speed to {self.desired_value}")
            Data.write()
            CurrentSpeed.update()

    def draw(self):
        if settings.speed == self.desired_value or (self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height):
            pygame.draw.rect(window, self.button_color2, (self.x, self.y, self.width, self.height))
        else:
            pygame.draw.rect(window, self.button_color1, (self.x, self.y, self.width, self.height))
        window.blit(self.text, (self.x + (self.width - self.text_width) / 2, self.y + (self.height - self.text_height) / 2))


class ButtonSpeedGroup:
    def __init__(self, x, y, width, height, color1, color2, color_text, font_size, desired_values_list, spacing):
        self.width = (len(settings.speed_list) - 1) * (width + spacing) + width
        self.height = height

        self.ButtonsList = []
        for index, value in enumerate(desired_values_list):
            self.ButtonsList.append(ButtonSpeed(x + index * (spacing + width), y, width, height, color1, color2, color_text, font_size, value))

    def click(self):
        for button in self.ButtonsList:
            button.click()

    def draw(self):
        for button in self.ButtonsList:
            button.draw()


class ButtonCmds:
    @staticmethod
    def gameTrue():
        global game
        game = True

    @staticmethod
    def menuFalse():
        global menu
        menu = False

    @staticmethod
    def exit1():
        exit(1)

    @staticmethod
    def website():
        webbrowser.open(settings.url_website, new=0, autoraise=True)

    @staticmethod
    def creditssTrue():
        global creditss
        creditss = True

    @staticmethod
    def creditssFalse():
        global creditss
        creditss = False


class Text:
    def __init__(self, text, color, font_size):
        self.font = pygame.font.SysFont(settings.font_name, font_size, bold=True)
        self.text_width, self.text_height = self.font.size(text)
        self.text = self.font.render(text, True, color)

    def draw(self, x, y):
        window.blit(self.text, (x, y))


class LongText:
    def __init__(self, text, color, font_size, line_lenght, line_spacing):
        self.line_spacing = line_spacing
        self.font = pygame.font.SysFont(settings.font_name, font_size, bold=True)

        # splitting text into lines
        words = text.split(" ")

        i = 0
        textList = []
        curr_line = ""
        while i < len(words):
            if words[i] == "\n":
                textList.append(curr_line)
                curr_line = ""
                i += 1

            elif line_lenght - len(curr_line) - 1 >= len(words[i]):
                if len(curr_line):
                    curr_line += " "
                curr_line += words[i]
                i += 1

            elif len(words[i]) >= line_lenght:
                textList.append(curr_line)
                textList.append(words[i])
                curr_line = ""
                i += 1

            else:
                textList.append(curr_line)
                curr_line = ""

        if len(curr_line):
            textList.append(curr_line)

        #

        self.rendredTextList = []
        for line in textList:
            self.rendredTextList.append(Text(line, color, font_size))

        self.text_width = self.rendredTextList[0].text_width
        for line in self.rendredTextList:
            if line.text_width > self.text_width:
                self.text_width = line.text_width
        self.line_height = self.rendredTextList[0].text_height
        self.text_height = len(self.rendredTextList) * self.line_height + (len(self.rendredTextList) - 1) * line_spacing

    def draw(self, x, y):
        i = 0
        for line in self.rendredTextList:
            line.draw(x, y + i)
            i += self.line_height + self.line_spacing


class File:  # Data
    def __init__(self):
        self.path_data = settings.path_data

    def read(self):
        try:
            with settings.path_version.open("r") as file:
                self.version = base64_decode(file.readline())

            with self.path_data.open("r") as file:
                data = base64_decode(file.readline())

            self.datadict = json.loads(data)
            if self.datadict.get("highscore"):
                self.highscore = self.datadict.get("highscore")
            else:
                self.highscore = 0

            if self.datadict.get("speed"):
                settings.speed = self.datadict.get("speed")
                settings.move_delay = settings.fps / settings.speed

        except:
            logger.exception("Error while reading game data:")
            error_screen("Error while reading game data")

        else:
            logger.info("Game data successfully read")

    def write(self):
        try:
            self.datadict["highscore"] = self.highscore
            self.datadict["speed"] = settings.speed
            with self.path_data.open("w") as file:
                file.write(base64_encode(json.dumps(self.datadict)))
                file.write("\neyJqdXN0IGZvdW5kIGFuIEVhc3RlciBFZ2c/PyI6IHRydWV9")
        except Exception as err:
            logger.error(err)
            logger.error(traceback.format_exc())
            error_screen("Error while writing game data")


def checkFiles():
    if not settings.path_data.exists() or settings.path_data.stat().st_size == 0:
        logger.warning("Data file did not exist, trying to create")
        with settings.path_data.open("w") as file:
            empty_dict = {
                "highscore": None
            }
            file.write(base64_encode(json.dumps(empty_dict)))
            file.write("\neyJqdXN0IGZvdW5kIGFuIEVhc3RlciBFZ2c/PyI6IHRydWV9")
        logger.warning("Data file successfully created")

    if not settings.path_version.exists() or settings.path_version.stat().st_size == 0:
        logger.warning("Version file did not exist, trying to create")
        settings.path_version.write_text(base64_encode(settings.version))
        logger.warning("Version file successfully created")

    if not settings.path_musicDirectory.exists():
        logger.warning("Music directory did not exist, trying to create")
        settings.path_musicDirectory.mkdir()
        logger.warning("Music directory successfully created")

    if not settings.path_music_Game.exists():
        logger.warning("Game music did not exist, trying to download")
        try:
            download = requests.get(settings.url_music_Game, allow_redirects=True)
            settings.path_music_Game.write_bytes(download.content)
        except Exception as err:
            logger.error(err)
            logger.error(traceback.format_exc())
            raise err
        else:
            logger.warning("Game music successfully downloaded")

    if not settings.path_music_GameOver.exists():
        logger.warning("GameOver music did not exist, trying to download")
        try:
            download = requests.get(settings.url_music_GameOver, allow_redirects=True)
            settings.path_music_GameOver.write_bytes(download.content)
        except Exception as err:
            logger.error(err)
            logger.error(traceback.format_exc())
            raise err
        else:
            logger.warning("GameOver music successfully downloaded")

    logger.info("Checking files done")


def loading_screen(function, loading_text, error_text):
    thread = MyThread(target=function, daemon=True)
    thread.start()
    time = 0
    Loading0 = Text(loading_text, settings.color_font, settings.font_size_loading)
    Loading1 = Text(f"{loading_text}.", settings.color_font, settings.font_size_loading)
    Loading2 = Text(f"{loading_text}..", settings.color_font, settings.font_size_loading)
    Loading3 = Text(f"{loading_text}...", settings.color_font, settings.font_size_loading)

    while thread.is_alive():
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

    if thread.error:
        logger.error(thread.error)
        logger.error(thread.traceback)
        error_screen(error_text)


def error_screen(text):
    logger.critical(f"Error screen: {text}")
    global error
    global mouse
    error = True
    ErrorText = LongText(text, settings.color_font, settings.font_size_error, settings.line_lenght, settings.line_spacing)
    ButtonExit2 = Button(int((settings.window_width - settings.button_width) / 2), 500, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Exit", settings.button_text_size, ButtonCmds.exit1)

    while error:
        clock.tick(settings.fps)

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                error = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                ButtonExit2.click()

        window.fill(settings.color_error_backgorund)
        ErrorText.draw((settings.window_width - ErrorText.text_width) / 2, (settings.window_height - ErrorText.text_height) / 2 - 60)
        ButtonExit2.draw()
        pygame.display.update()


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
        Time = Text(f"time: {int(Snake.fpsCounter / settings.fps // 60):02}:{int(Snake.fpsCounter / settings.fps % 60):02}", settings.color_font, settings.label_font_size)
        Time.draw(1.4 * settings.grid, int((self.height - Time.text_height)/2))

        Score = Text(f"score: {decimals(Snake.score)}", settings.color_font, settings.label_font_size)
        Score.draw(int((self.width - Score.text_width) / 2), int((self.height - Score.text_height)/2))

        HighscoreOnBar = Text(f"highscore: {decimals(Data.highscore)}", settings.color_font, settings.label_font_size)
        HighscoreOnBar.draw(self.width - settings.grid - HighscoreOnBar.text_width - 0.4 * settings.grid, int((self.height - HighscoreOnBar.text_height)/2))


class CurrentSpeedClass:
    def __init__(self):
        self.update()
        self.x = 1.4 * settings.grid
        self.y = settings.grid * 25 + (settings.grid - self.text.text_height) // 2

    def update(self):
        self.text = Text(f"speed: {settings.speed}", settings.color_font, settings.font_size_currentspeed)

    def draw(self):
        self.text.draw(self.x, self.y)


########### Scenes managing ###########

def menu_main():
    global mouse
    global menu
    global game
    global creditss
    global HighscoreInMenu

    menu = True
    game = False
    creditss = False

    HighscoreInMenu = Text(f"highscore: {decimals(Data.highscore)}", settings.color_font, settings.font_size_highscoreinmenu)
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
                WebsiteButton.click()  # Website
                CreditsButton.click()  # Credits
                SpeedButtons.click()  # Speed buttons

        if keys[pygame.K_q]:
            game = True

        if game:
            game_main()

        if creditss:
            creditss_main()

        menu_redraw()


def menu_redraw():
    window.fill(settings.color_window_background)
    SnakeLogo.draw((settings.window_width - SnakeLogo.text_width) / 2, int(settings.grid * 3.8))
    HighscoreInMenu.draw(int((settings.window_width - HighscoreInMenu.text_width) / 2), 195)
    ButtonPlay.draw()
    ButtonExit.draw()
    Author.draw(settings.window_width - Author.text_width - int(0.4 * settings.grid), settings.window_height - Author.text_height - int(0.4 * settings.grid))
    WebsiteButton.draw()
    CreditsButton.draw()
    SpeedText.draw(settings.window_width - SpeedButtons.width - 0.5 * settings.grid - SpeedText.text_width - settings.SpeedButton_spacing, 0.5 * settings.grid + (settings.SpeedButton_height - SpeedText.text_height) / 2)
    SpeedButtons.draw()

    pygame.display.update()


def game_main():
    global game_notOver
    global game
    pygame.mixer.music.load(settings.path_music_Game)
    pygame.mixer.music.play(loops=-1)
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

    logger.info(f"Game over, score: {Snake.score}")
    pygame.mixer.music.pause()
    pygame.mixer.music.load(settings.path_music_GameOver)
    pygame.mixer.music.play()

    if Snake.score > Data.highscore:  # new record
        logger.info(f"Highscore beaten, old: {Data.highscore}, new: {Snake.score}")
        Data.highscore = Snake.score
        Data.write()
        NewHighscoreText = Text(f"new highscore: {Snake.score}", settings.color_newhighscore, settings.font_size_newhighscore)
        NewHighscoreText.draw((settings.window_width - NewHighscoreText.text_width) / 2, (settings.window_height - GameOver.text_height) / 2 - GameOver.text_height + NewHighscoreText.text_height - 10)
        global HighscoreInMenu
        HighscoreInMenu = Text(f"highscore: {decimals(Data.highscore)}", settings.color_font, settings.font_size_highscoreinmenu)

    GameOver.draw((settings.window_width - GameOver.text_width) / 2, (settings.window_height - GameOver.text_height) / 2)

    while pygame.mixer.music.get_busy():
        clock.tick(settings.fps)
        pygame.display.update()

    game = False


def game_redraw():
    window.fill(settings.color_window_background)
    pygame.draw.rect(window, settings.color_game_background, (settings.game_x, settings.game_y, settings.game_width, settings.game_height))
    Snake.draw()
    Apple.draw()
    TopBar.draw()
    CurrentSpeed.draw()
    pygame.display.update()


def creditss_main():
    global mouse
    global creditss
    global CreditsText
    global CreditsBackButton

    # I do not prerender it, as it is unlikely to be used often
    CreditsText = LongText("Icon: \n Icon made by Freepik from www.flaticon.com \n \n Music during gameplay: \n Tristan Lohengrin - Happy 8bit Loop 01 \n \n Sound after loss: \n Sad Trombone Wah Wah Wah Fail Sound Effect", settings.color_font, settings.font_size_creditss, settings.line_lenght_creditss, settings.line_spacing)
    CreditsBackButton = Button(int((settings.window_width - settings.button_width) / 2), 500, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Back", settings.button_text_size, ButtonCmds.creditssFalse)

    while creditss:
        clock.tick(settings.fps)

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                creditss = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                CreditsBackButton.click()  # Back to menu

        creditss_redraw()


def creditss_redraw():
    global CreditsText
    global CreditsBackButton
    window.fill(settings.color_window_background)
    CreditsText.draw((settings.window_width - CreditsText.text_width) / 2, 90)
    CreditsBackButton.draw()
    pygame.display.update()


############## Settings ##############

class settings:
    version = "1.1"
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
    color_error_backgorund = (208, 26, 26)
    color_game_background = (0, 0, 0)
    color_snake_head = (255, 255, 255)
    color_snake_tail = (0, 255, 0)
    color_apple = (255, 0, 0)
    color_button = (254, 151, 12)
    color_button_focused = (183, 111, 15)
    color_font = (255, 255, 255)
    color_gameover = (255, 0, 0)
    color_newhighscore = (0, 0, 255)
    color_snakeLogo = (255, 255, 255)
    color_author = (215, 215, 215)

    font_name = "Verdana"
    font_size_loading = 35
    font_size_error = 30
    font_size_gameover = 70
    font_size_newhighscore = 33
    font_size_snakeLogo = 60
    font_size_highscoreinmenu = 30
    font_size_author = 21
    font_size_website = 20
    font_size_creditss = 25
    font_size_speed = 22
    font_size_currentspeed = 17

    line_spacing = 6
    line_lenght = 40
    line_lenght_creditss = 52

    button_width = grid * 10
    button_height = grid * 4
    button_text_size = 34
    button_text_color = (255, 255, 255)

    ButtonPlay_y = 275
    ButtonExit_y = 420
    SpeedButton_width = 40
    SpeedButton_height = 35
    SpeedButton_spacing = 15

    if os.name == "nt":
        path_gameDirectory = Path.home() / "AppData" / "Roaming" / ".snake"  # ~\AppData\Roaming\.snake\
    else:
        path_gameDirectory = Path.home() / ".snake"  # ~/.snake/
    path_data = path_gameDirectory / "data"  # ~/.snake/data
    path_version = path_gameDirectory / "version"  # ~/.snake/version
    path_musicDirectory = path_gameDirectory / "music"  # ~/.snake/music/
    path_music_Game = path_musicDirectory / "Tristan Lohengrin - Happy 8bit Loop 01.ogg"
    path_music_GameOver = path_musicDirectory / "Sad Trombone Wah Wah Wah Fail Sound Effect.ogg"
    path_logDirectory = path_gameDirectory / "logs"  # ~/.snake/logs/
    path_log1 = path_logDirectory / "1.log"
    path_log2 = path_logDirectory / "2.log"
    path_log3 = path_logDirectory / "3.log"
    path_log4 = path_logDirectory / "4.log"
    path_icon = path_gameDirectory / "icon.png"

    url_music_Game = "https://drive.google.com/uc?id=1ksgD-ftTtFs5GKyA2mNZW6XIJKvk53dw&export=download"
    url_music_GameOver = "https://drive.google.com/uc?id=1dF_wNbBxyNsKmRf83f4UgZcT8Xgsux46&export=download"
    url_website = "http://tiny.cc/snake_website"

    icon_content = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAABR1BMVEUAAABeswAAgABrygBnuwBrygBowQBnvAAAbwFnvgDlNBdrywBpwADuORRtvQBrzgAAgABnvQABcAFovgBsygBrygBrygBowQAAcwBqwwBqxQAAfgBpxwBxzgALdwFfwQALhwBcvwAAbQFnvgAxogBrygBnvgAFgwBovwBsywAnkABpxgAAcgAAcQBsygAAcgBrygA7nQBryABowQAAgAB6rAMAbQEAbAEokABrygAXjwBovQBmxwBrygADgQA0pQBwtwFnxgAAgAAAbwFBrQBovwBrygBovwBrygBqwAAAcQAAgABqygAAcQBovwA8pAAPgABrywAAdQBqzAAAgABrywAvoQAAgQBGsQAAcgAdlgAAdQAnlgBXrwBpwwBnugBrygAAgAAAaQExogDeLBsWgAE8qQBdtQA5qABnuwBSrAB7qARZsgAJeIArAAAAX3RSTlMABOLg/fpo+uLi28yjWRsU+Pbr3dXBh35dVU8+OQz8/Pz39PDv59nUwLSlkpKIZ2dINCwhFPn59/Lw7ezq6enm5d3c09HQxMS6tbSrqKWMiXh1dHNsYlxXRUM9MCcjEayMVDsAAAHASURBVEjH1dVnUwIxEAbgnByCYgERFMHeBREBe++993rhxAL4/z/LJbckJ8lMZnSc8f3Ezu5zQzbcgFRSn883wud/CZobtqZKpdWRWsX5iG7YCWoq850eo5I9FdBmsHhUwIjBJaMAhngQUQALPGhTAB4eNHzvPqdvr++ziE+BBzuOVsfhHMZvuVzOf3BT2XiTwSeIWGI+jLEFSIaj8BQH6GfzV24MgMR/ya5BdBERjAFAjkgj7gA6zKfd1cBstzq1DhAAsIsFoM/qaAHRWmNYBMxzcmqdzQ/B8sJisEEX2199bT4Yd29vzg/7AUzTbh0A9gYNAkhZVRSAKQWwoyVargPIysCLnQFarnxYKRaLj6ScfbVzUgFwzh5a9mIr5UdOkrLLtDP2c7BMyzUAT6RsAXBaBWpo2QqgiZReABO/BnwAYs6v1C4DowDqMghpCRPyIANxAEah8GmyaDKQooDknc17kQxog0IwLgUoKQJ9SA60EA/YjkQ/PppmVxVIIC7YTjeqiBAAdgAxgGgXOge8USQEi46/tuNgQC/fw0zL/h1CYuBCkvw9cNkgpArCNkiqgk76BoxqSFmEXe7WM7X5L+xVXXt8wCY7AAAAAElFTkSuQmCC"

    fps = 60
    speed = 5  # default speed (aka movesPerSecond) (fps divisor)
    speed_list = [3, 5, 10, 15, 30, 60]
    move_delay = fps / speed


############# Main code #############

#### Initilizing game data ####
# moved from checkFiles() to make sure there is a game directory, so that the log file can be put there and game icon set
if not settings.path_gameDirectory.exists():
    settings.path_gameDirectory.mkdir()
if not settings.path_logDirectory.exists():
    settings.path_logDirectory.mkdir()

if not settings.path_icon.exists():
    settings.path_icon.write_bytes(base64.b64decode(settings.icon_content))

#### Logging configuration ####
if settings.path_log4.exists():
    settings.path_log4.unlink()
if settings.path_log3.exists():
    settings.path_log3.replace(settings.path_log4)
if settings.path_log2.exists():
    settings.path_log2.replace(settings.path_log3)
if settings.path_log1.exists():
    settings.path_log1.replace(settings.path_log2)

sys.stderr = open(settings.path_log1, "a")

for handler in logging.root.handlers[:]:  # this is needed in PyCharm and can be left for safety
    logging.root.removeHandler(handler)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] (Line %(lineno)d in %(funcName)s) - %(message)s')
file_handler = logging.FileHandler(filename=settings.path_log1, mode="a")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
stdout_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stdout_handler)

#### Main game code ####
logger.info("Starting")
logger.info(f"System: {platform.system()}, version: {platform.release()}")
pygame.display.init()
pygame.mixer.init()
pygame.font.init()
clock = pygame.time.Clock()
window = pygame.display.set_mode((settings.window_width, settings.window_height), vsync=1)
pygame.display.set_caption(f"Snake v{settings.version}")
Icon = pygame.image.load(settings.path_icon)
pygame.display.set_icon(Icon)

loading_screen(checkFiles, "Loading", "Program encountered a problem while creating local files. Check Your Internet connection and try again.")
Data = File()
Data.read()

# Prerendered objects
GameOver = Text("GAME  OVER", settings.color_gameover, settings.font_size_gameover)
SnakeLogo = Text("Snake Game", settings.color_snakeLogo, settings.font_size_snakeLogo)
Author = Text("Michał Machnikowski 2022", settings.color_author, settings.font_size_author)

ButtonPlay = Button(int((settings.window_width - settings.button_width) / 2), settings.ButtonPlay_y, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Play", settings.button_text_size, ButtonCmds.gameTrue)
ButtonExit = Button(int((settings.window_width - settings.button_width) / 2), settings.ButtonExit_y, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Exit", settings.button_text_size, ButtonCmds.menuFalse)
WebsiteButton = Button(0.5 * settings.grid, settings.window_height - 2.5 * settings.grid, int(4.85 * settings.grid), 2 * settings.grid, settings.color_button, settings.color_button_focused, settings.button_text_color, "website", settings.font_size_website, ButtonCmds.website)
CreditsButton = Button(int(6 * settings.grid), settings.window_height - 2.5 * settings.grid, int(4.65 * settings.grid), 2 * settings.grid, settings.color_button, settings.color_button_focused, settings.button_text_color, "credits", settings.font_size_website, ButtonCmds.creditssTrue)

SpeedText = Text("Speed:", settings.color_font, settings.font_size_speed)
SpeedButtons = ButtonSpeedGroup(settings.window_width - ((len(settings.speed_list) - 1) * (settings.SpeedButton_width + settings.SpeedButton_spacing) + settings.SpeedButton_width + 0.5 * settings.grid), 0.5 * settings.grid, settings.SpeedButton_width, settings.SpeedButton_height, settings.color_button, settings.color_button_focused, settings.color_font, settings.font_size_speed, settings.speed_list, settings.SpeedButton_spacing)

Snake = Player(settings.grid, settings.grid_border, settings.color_snake_head, settings.color_snake_tail)
Apple = Target(settings.grid, settings.grid_border, settings.color_apple)
TopBar = Bar(settings.label_x, settings.label_y, settings.label_width, settings.label_height)
CurrentSpeed = CurrentSpeedClass()

menu_main()

pygame.quit()

logger.info("Quitting")
