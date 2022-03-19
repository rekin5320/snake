#!/usr/bin/env python3

import base64
import json
import logging.handlers
import os
from pathlib import Path
import platform
from random import randrange
import sys
import threading
import traceback
import webbrowser

import pygame
import requests


######## Classes, functions and definitions ########

def decimals(n):
    """
    Inserts spaces between every three digits.
    See https://stackoverflow.com/a/17484665
    """
    return format(n, ',').replace(',', ' ')


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


class Text:
    def __init__(self, text, color, font_size):
        if settings.path_font.exists() and settings.path_font.stat().st_size > 0:
            self.font = pygame.font.Font(settings.path_font, font_size)
        else:
            self.font = pygame.font.SysFont("Verdana", font_size, bold=True)
        self.text_width, self.text_height = self.font.size(text)
        self.text = self.font.render(text, True, color)

    def draw(self, x, y):
        window.blit(self.text, (x, y))


class LongText:
    def __init__(self, text, color, font_size, line_lenght=40, line_spacing=6):
        self.line_spacing = line_spacing

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


class RoundedRectangle:
    def __init__(self, width, height, radius, color):
        self.width = width
        self.height = height
        self.radius = radius
        self.color = color

    def draw(self, x, y):
        pygame.draw.rect(window, self.color, (x + self.radius, y, self.width - 2 * self.radius, self.height))
        pygame.draw.rect(window, self.color, (x, y + self.radius, self.width, self.height - 2 * self.radius))
        pygame.draw.circle(window, self.color, (x + self.radius, y + self.radius), self.radius)
        pygame.draw.circle(window, self.color, (x + self.width - self.radius, y + self.radius), self.radius)
        pygame.draw.circle(window, self.color, (x + self.width - self.radius, y + self.height - self.radius), self.radius)
        pygame.draw.circle(window, self.color, (x + self.radius, y + self.height - self.radius), self.radius)


class Button:
    def __init__(self, x, y, width, height, color1, color2, color_text, text, font_size, command=None, radius=9):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.background1 = RoundedRectangle(width, height, radius, color1)
        self.background2 = RoundedRectangle(width, height, radius, color2)
        self.text = Text(text, color_text, font_size)
        self.command = command

    def is_pointed(self):
        return self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height

    def is_highlighted(self):
        return self.is_pointed()

    def click(self):
        if self.is_pointed():
            self.command()

    def draw(self):
        if self.is_highlighted():
            self.background2.draw(self.x, self.y)
        else:
            self.background1.draw(self.x, self.y)
        self.text.draw(self.x + (self.width - self.text.text_width) // 2, self.y + (self.height - self.text.text_height) // 2)


class ButtonSpeed(Button):
    def __init__(self, x, y, width, height, color1, color2, color_text, font_size, desired_value):
        super().__init__(x, y, width, height, color1, color2, color_text, str(desired_value), font_size, radius=4)
        self.desired_value = desired_value

    def click(self):
        if self.is_pointed():
            settings.speed = self.desired_value
            settings.move_delay = settings.fps / settings.speed
            logger.info(f"Changed speed to {self.desired_value}")
            Data.write()
            CurrentSpeedText.update()

    def is_highlighted(self):
        return super().is_pointed() or settings.speed == self.desired_value


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
            self.highscore = self.datadict.get("highscore", 0)

            if "speed" in self.datadict:
                settings.speed = self.datadict["speed"]
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

    if not settings.path_font.exists() or settings.path_font.stat().st_size == 0:
        logger.warning("Font did not exist, trying to download")
        try:
            download = requests.get(settings.url_font, allow_redirects=True)
            settings.path_font.write_bytes(download.content)
        except Exception as err:
            logger.error(err)
            logger.error(traceback.format_exc())
            raise err
        else:
            logger.warning("Font successfully downloaded")

    if not settings.path_music_Game.exists() or settings.path_music_Game.stat().st_size == 0:
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

    if not settings.path_music_GameOver.exists() or settings.path_music_GameOver.stat().st_size == 0:
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


class SnakeClass:
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
        self.x = (settings.game_width - self.grid) // 2 + settings.game_x
        self.y = (settings.game_height - self.grid) // 2 + settings.game_y
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
        self.head_location = (self.x + self.border, self.y + self.border, self.grid - 2 * self.border, self.grid - 2 * self.border)

        if self.x == settings.game_x - self.grid or self.x == settings.game_width + self.grid or self.y == settings.game_y - self.grid or self.y == settings.game_height + settings.label_height:
            game_notOver = False

        for pair in self.xyList[:-1]:  # collision with itself
            if self.head_location == pair:
                game_notOver = False

        self.xyList.append(self.head_location)

        if self.x == Apple.x and self.y == Apple.y:  # ate the apple
            self.score += 1
            Apple.move()
        else:
            self.xyList.pop(0)

    def draw(self):
        for pair in self.xyList[:-1]:
            pygame.draw.rect(window, self.color_tail, pair)
        pygame.draw.rect(window, self.color_head, self.xyList[-1])


class AppleClass:
    def __init__(self, grid, border, color_apple):
        self.grid = grid
        self.border = border
        self.color = color_apple
        self.move()

    def move(self):
        self.x = randrange(0, settings.game_width // self.grid) * self.grid + settings.game_x
        self.y = randrange(0, settings.game_height // self.grid) * self.grid + settings.game_y
        self.location = (self.x + self.border, self.y + self.border, self.grid - 2 * self.border, self.grid - 2 * self.border)
        for pair in Snake.xyList:
            if pair == self.location:
                self.move()
                break

    def draw(self):
        pygame.draw.rect(window, self.color, self.location)


class TopBarClass:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self):
        Time = Text(f"time: {Snake.fpsCounter // settings.fps // 60:02}:{Snake.fpsCounter // settings.fps % 60:02}", settings.color_font, settings.label_font_size)
        Time.draw(1.4 * settings.grid, (self.height - Time.text_height) // 2)

        Score = Text(f"score: {decimals(Snake.score)}", settings.color_font, settings.label_font_size)
        Score.draw((self.width - Score.text_width) // 2, (self.height - Score.text_height) // 2)

        HighscoreOnBar = Text(f"highscore: {decimals(Data.highscore)}", settings.color_font, settings.label_font_size)
        HighscoreOnBar.draw(self.width - settings.grid - HighscoreOnBar.text_width - 0.4 * settings.grid, (self.height - HighscoreOnBar.text_height) // 2)


class CurrentSpeedTextClass:
    def __init__(self):
        self.update()
        self.x = 1.4 * settings.grid
        self.y = 25 * settings.grid + (settings.grid - self.text.text_height) // 2

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
    global LastScore

    menu = True
    game = False
    creditss = False

    HighscoreInMenu = Text(f"highscore: {decimals(Data.highscore)}", settings.color_font, settings.font_size_highscoreinmenu)
    LastScore = None
    while menu:
        clock.tick(settings.fps)

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                menu = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                ButtonPlay.click()     # Game
                ButtonExit.click()     # Exit
                WebsiteButton.click()  # Website
                CreditsButton.click()  # Credits
                SpeedButtons.click()   # Speed buttons

        if keys[pygame.K_q]:
            game = True

        if game:
            game_main()

        if creditss:
            creditss_main()

        menu_redraw()


def menu_redraw():
    global LastScore
    window.fill(settings.color_window_background)
    SnakeLogo.draw((settings.window_width - SnakeLogo.text_width) // 2, 4.5 * settings.grid)
    HighscoreInMenu.draw(0.4 * settings.grid, 0.35 * settings.grid)
    if LastScore:
        LastScore.draw((settings.window_width - LastScore.text_width) // 2, 205)
    ButtonPlay.draw()
    ButtonExit.draw()
    Author.draw(settings.window_width - Author.text_width - 0.4 * settings.grid, settings.window_height - Author.text_height - 0.4 * settings.grid)
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
        NewHighscoreText.draw((settings.window_width - NewHighscoreText.text_width) // 2, (settings.window_height - GameOver.text_height) // 2 - GameOver.text_height + NewHighscoreText.text_height - 10)
        global HighscoreInMenu
        HighscoreInMenu = Text(f"highscore: {decimals(Data.highscore)}", settings.color_font, settings.font_size_highscoreinmenu)

    global LastScore
    LastScore = Text(f"last score: {Snake.score}", settings.color_font, settings.font_size_lastscore)

    GameOver.draw((settings.window_width - GameOver.text_width) // 2, (settings.window_height - GameOver.text_height) // 2)

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
    CurrentSpeedText.draw()
    pygame.display.update()


def creditss_main():
    global mouse
    global creditss
    global CreditsText
    global CreditsBackButton

    # I do not prerender it, as it is unlikely to be used often
    CreditsText = LongText("Icon: \n Icon made by Freepik from www.flaticon.com \n \n Music during gameplay: \n Tristan Lohengrin - Happy 8bit Loop 01 \n \n Sound after loss: \n Sad Trombone Wah Wah Wah Fail Sound Effect", settings.color_font, settings.font_size_creditss, line_lenght=52)
    CreditsBackButton = Button((settings.window_width - settings.button_width) // 2, 500, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Back", settings.button_text_size, ButtonCmds.creditssFalse)

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
    CreditsText.draw((settings.window_width - CreditsText.text_width) // 2, 90)
    CreditsBackButton.draw()
    pygame.display.update()


def loading_screen(function, loading_text, error_text):
    thread = MyThread(target=function, daemon=True)
    thread.start()
    time = 0
    LoadingTexts = (
        Text(loading_text, settings.color_font, settings.font_size_loading),
        Text(f"{loading_text}.", settings.color_font, settings.font_size_loading),
        Text(f"{loading_text}..", settings.color_font, settings.font_size_loading),
        Text(f"{loading_text}...", settings.color_font, settings.font_size_loading)
    )

    while thread.is_alive():
        clock.tick(settings.fps)
        window.fill(settings.color_window_background)
        Loading = LoadingTexts[time // settings.fps % 4]
        Loading.draw((settings.window_width - Loading.text_width) / 2, (settings.window_height - Loading.text_height) / 2)
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
    ErrorText = LongText(text, settings.color_font, settings.font_size_error)
    ButtonExit2 = Button((settings.window_width - settings.button_width) // 2, 500, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Exit", settings.button_text_size, ButtonCmds.exit1)

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
    color_button_focused = (195, 122, 20)
    color_font = (255, 255, 255)
    color_gameover = (255, 0, 0)
    color_newhighscore = (0, 0, 255)
    color_snakeLogo = (255, 255, 255)
    color_author = (215, 215, 215)

    font_size_loading = 35
    font_size_error = 30
    font_size_gameover = 70
    font_size_newhighscore = 33
    font_size_snakeLogo = 60
    font_size_highscoreinmenu = 27
    font_size_lastscore = 30
    font_size_author = 21
    font_size_website = 20
    font_size_creditss = 25
    font_size_speed = 22
    font_size_currentspeed = 17

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
    path_assetsDirectory = path_gameDirectory / "assets"  # ~/.snake/assets/
    path_font = path_assetsDirectory / "OpenSans-Bold.ttf"
    path_music_Game = path_assetsDirectory / "Tristan Lohengrin - Happy 8bit Loop 01.ogg"
    path_music_GameOver = path_assetsDirectory / "Sad Trombone Wah Wah Wah Fail Sound Effect.ogg"
    path_icon = path_assetsDirectory / "icon.png"
    path_logDirectory = path_gameDirectory / "logs"  # ~/.snake/logs/
    path_log1 = path_logDirectory / "1.log"
    path_log2 = path_logDirectory / "2.log"
    path_log3 = path_logDirectory / "3.log"
    path_log4 = path_logDirectory / "4.log"

    url_font = "https://drive.google.com/uc?id=1sudSgrckaZPxSxtAxv8zXCSIEdcfTqRi&export=download"
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
if not settings.path_assetsDirectory.exists():
    settings.path_assetsDirectory.mkdir()

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

ButtonPlay = Button((settings.window_width - settings.button_width) // 2, settings.ButtonPlay_y, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Play", settings.button_text_size, ButtonCmds.gameTrue)
ButtonExit = Button((settings.window_width - settings.button_width) // 2, settings.ButtonExit_y, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Exit", settings.button_text_size, ButtonCmds.menuFalse)
WebsiteButton = Button(0.5 * settings.grid, settings.window_height - 2.5 * settings.grid, int(4.85 * settings.grid), 2 * settings.grid, settings.color_button, settings.color_button_focused, settings.button_text_color, "website", settings.font_size_website, ButtonCmds.website, radius=7)
CreditsButton = Button(int(6 * settings.grid), settings.window_height - 2.5 * settings.grid, int(4.65 * settings.grid), 2 * settings.grid, settings.color_button, settings.color_button_focused, settings.button_text_color, "credits", settings.font_size_website, ButtonCmds.creditssTrue, radius=7)

SpeedText = Text("Speed:", settings.color_font, settings.font_size_speed)
SpeedButtons = ButtonSpeedGroup(settings.window_width - ((len(settings.speed_list) - 1) * (settings.SpeedButton_width + settings.SpeedButton_spacing) + settings.SpeedButton_width + 0.5 * settings.grid), 0.5 * settings.grid, settings.SpeedButton_width, settings.SpeedButton_height, settings.color_button, settings.color_button_focused, settings.color_font, settings.font_size_speed, settings.speed_list, settings.SpeedButton_spacing)

Snake = SnakeClass(settings.grid, settings.grid_border, settings.color_snake_head, settings.color_snake_tail)
Apple = AppleClass(settings.grid, settings.grid_border, settings.color_apple)
TopBar = TopBarClass(settings.label_x, settings.label_y, settings.label_width, settings.label_height)
CurrentSpeedText = CurrentSpeedTextClass()

menu_main()

pygame.quit()

logger.info("Quitting")
