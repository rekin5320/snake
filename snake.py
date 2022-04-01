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
    return format(n, ",").replace(",", " ")


class MyThread(threading.Thread):
    def run(self):
        try:
            threading.Thread.run(self)
        except Exception as err:
            self.error = err
            self.traceback = traceback.format_exc()
        else:
            self.error = False


class MyPath(type(Path())):
    def size(self):
        return self.stat().st_size

    def is_good(self):
        return self.exists() and self.size() > 0


def base64_encode(text):
    encodedtext_bytes = base64.b64encode(text.encode("utf-8"))
    encodedtext = str(encodedtext_bytes, "utf-8")
    return encodedtext


def base64_decode(text):
    decodedtext_bytes = base64.b64decode(text)
    decodedtext = str(decodedtext_bytes, "utf-8")
    return decodedtext


def round_to_3_places(num):
    return int(num * 1000 + 0.5) / 1000


def format_time(seconds):
    if not isinstance(seconds, int):
        seconds = int(seconds + 0.5)
    return f"{seconds // 60:02}:{seconds % 60:02}"


class Text:
    def __init__(self, text, color, font_size):
        if settings.path_font.is_good():
            self.font = pygame.font.Font(settings.path_font, font_size)
        else:
            self.font = pygame.font.SysFont("Verdana", font_size, bold=True)
        self.text = self.font.render(text, True, color)
        self.text_width, self.text_height = self.text.get_size()

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
        self.dec, self.inc = False, False

        self.ButtonsList = []
        for index, value in enumerate(desired_values_list):
            self.ButtonsList.append(ButtonSpeed(x + index * (spacing + width), y, width, height, color1, color2, color_text, font_size, value))

    def click(self):
        for button in self.ButtonsList:
            button.click()

    def draw(self):
        for button in self.ButtonsList:
            button.draw()

    def await_decrease(self):
        self.dec = True
        self.inc = False

    def await_increase(self):
        self.dec = False
        self.inc = True

    def change_speed(self):
        if self.dec:
            self.decrease()
            self.dec, self.inc = False, False
        elif self.inc:
            self.increase()
            self.dec, self.inc = False, False
        Data.write()

    @staticmethod
    def decrease():
        if (i := settings.speed_list.index(settings.speed)) > 0:
            settings.speed = settings.speed_list[i - 1]

    @staticmethod
    def increase():
        if (i := settings.speed_list.index(settings.speed)) < len(settings.speed_list) - 1:
            settings.speed = settings.speed_list[i + 1]


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
            highscores_speed = self.datadict.get("highscores_speed", {})
            self.highscores_speed = {i: highscores_speed.get(i, 0) for i in map(str, sorted(settings.speed_list))}
            self.total_games = self.datadict.get("total_games", 0)
            self.total_time = self.datadict.get("total_time", 0)

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
            logger.debug("Writing data")
            self.datadict["speed"] = settings.speed
            self.datadict["highscore"] = self.highscore
            self.datadict["highscores_speed"] = self.highscores_speed
            self.datadict["total_games"] = self.total_games
            self.datadict["total_time"] = round_to_3_places(self.total_time)
            with self.path_data.open("w") as file:
                file.write(base64_encode(json.dumps(self.datadict)))
                file.write("\neyJqdXN0IGZvdW5kIGFuIEVhc3RlciBFZ2c/PyI6IHRydWV9")
            settings.path_version.write_text(base64_encode(settings.version))

        except Exception as err:
            logger.error(err)
            logger.error(traceback.format_exc())
            error_screen("Error while writing game data")


def download_if_needed(path: MyPath, url, name):
    if not path.is_good():
        logger.warning(f"{name} did not exist, trying to download")
        try:
            download = requests.get(url, allow_redirects=True)
            path.write_bytes(download.content)
        except Exception as err:
            logger.error(err)
            logger.error(traceback.format_exc())
            raise err
        else:
            logger.warning(f"{name} successfully downloaded")


def checkFiles():
    if not settings.path_version.is_good():
        logger.warning("Version file did not exist, trying to create")
        settings.path_version.write_text(base64_encode(settings.version))
        logger.warning("Version file successfully created")

    if not settings.path_data.is_good():
        logger.warning("Data file did not exist, trying to create")
        with settings.path_data.open("w") as file:
            file.write(base64_encode(json.dumps({})))
            file.write("\neyJqdXN0IGZvdW5kIGFuIEVhc3RlciBFZ2c/PyI6IHRydWV9")
        logger.warning("Data file successfully created")

    download_if_needed(settings.path_font, settings.url_font, "Font")
    download_if_needed(settings.path_music_Game, settings.url_music_Game, "Game music")
    download_if_needed(settings.path_music_GameOver, settings.url_music_GameOver, "GameOver music")

    logger.info("Checking files done")


class SnakeClass:
    def __init__(self):
        self.grid = settings.grid
        self.border = settings.grid_border
        self.velocity = settings.grid
        self.color_head = (255, 255, 255)
        self.colors_tail = [(0, 255, 0), (14, 205, 14)]
        self.colors_tail_len = len(self.colors_tail)
        self.reinit()

    def reinit(self):
        self.dirx = 0
        self.diry = 0
        self.dirx_current = 0
        self.diry_current = 0
        self.x = (settings.game_width - self.grid) // 2 + settings.game_x
        self.y = (settings.game_height - self.grid) // 2 + settings.game_y
        self.xyList = [(self.x + self.border, self.y + self.border, self.grid - 2 * self.border, self.grid - 2 * self.border)]
        self.fpsCounter = 0
        self.score = 1

    def change_dir_left(self):
        if self.dirx_current == 0:
            self.dirx = -1
            self.diry = 0

    def change_dir_right(self):
        if self.dirx_current == 0:
            self.dirx = 1
            self.diry = 0

    def change_dir_up(self):
        if self.diry_current == 0:
            self.dirx = 0
            self.diry = -1

    def change_dir_down(self):
        if self.diry_current == 0:
            self.dirx = 0
            self.diry = 1

    def move(self):
        global game_notOver
        self.dirx_current = self.dirx
        self.diry_current = self.diry

        if self.dirx != 0:
            self.x += self.dirx * self.velocity
        elif self.diry != 0:
            self.y += self.diry * self.velocity
        self.head_location = (self.x + self.border, self.y + self.border, self.grid - 2 * self.border, self.grid - 2 * self.border)

        if self.x == settings.game_x - self.grid or self.x == settings.game_width + self.grid or self.y == settings.game_y - self.grid or self.y == settings.game_height + settings.topbar_height:
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
        shift = (len(self.xyList) - 2) % self.colors_tail_len
        for i, segment in enumerate(self.xyList[:-1]):
            pygame.draw.rect(window, self.colors_tail[(i - shift) % self.colors_tail_len], segment)
        pygame.draw.rect(window, self.color_head, self.xyList[-1])


class AppleClass:
    def __init__(self):
        self.grid = settings.grid
        self.border = settings.grid_border
        self.color = (255, 0, 0)
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
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = settings.topbar_width
        self.height = settings.topbar_height
        self.font_size = int(1.04 * settings.grid)

    def draw(self):
        Time = Text(f"time: {format_time(Snake.fpsCounter // settings.fps)}", settings.color_font, self.font_size)
        Time.draw(1.4 * settings.grid, (self.height - Time.text_height) // 2)

        Score = Text(f"score: {decimals(Snake.score)}", settings.color_font, self.font_size)
        Score.draw((self.width - Score.text_width) // 2, (self.height - Score.text_height) // 2)

        HighscoreOnBar = Text(f"highscore: {decimals(Data.highscores_speed[str(settings.speed)])}", settings.color_font, self.font_size)
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


class HighscoresInMenuClass:
    def __init__(self):
        self.x1 = 0.4 * settings.grid
        self.x2 = settings.grid
        self.y1 = 0.35 * settings.grid
        self.color = settings.color_font
        self.font_size1 = 23
        self.font_size2 = 21
        self.update()
        self.height = self.y2 + self.text2.text_height

    def update(self):
        self.text1 = Text("Highscores:", self.color, self.font_size1)
        self.text2 = LongText(f"• overall: {Data.highscore} \n " + " \n ".join([f"• {k}: {v}" for k, v in Data.highscores_speed.items()]), self.color, self.font_size2, line_spacing=6)
        self.y2 = self.text1.text_height + 10

    def draw(self):
        self.text1.draw(self.x1, self.y1)
        self.text2.draw(self.x2, self.y2)


class TotalStatsInMenuClass:
    def __init__(self):
        self.x = 0.4 * settings.grid
        self.y1 = HighscoresInMenu.height + 7
        self.color = settings.color_font
        self.font_size = 20
        self.update()
        self.y2 = self.y1 + self.text_games.text_height + 5

    def update(self):
        self.text_games = Text(f"total games: {Data.total_games}", self.color, self.font_size)
        self.text_time = Text(f"total time: {format_time(Data.total_time)}", self.color, self.font_size)

    def draw(self):
        self.text_games.draw(self.x, self.y1)
        self.text_time.draw(self.x, self.y2)


########### Scenes managing ###########

def menu_main():
    global mouse
    global menu
    global game
    global creditss
    global LastScore

    menu = True
    game = False
    creditss = False

    LastScore = None
    while menu:
        clock.tick(settings.fps)

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                ButtonPlay.click()     # Game
                ButtonExit.click()     # Exit
                WebsiteButton.click()  # Website
                CreditsButton.click()  # Credits
                SpeedButtons.click()   # Speed buttons

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            menu = False
        if keys[pygame.K_SPACE]:
            game = True

        if keys[pygame.K_MINUS]:
            SpeedButtons.await_decrease()
        elif keys[pygame.K_EQUALS] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
            SpeedButtons.await_increase()
        else:
            SpeedButtons.change_speed()

        if game:
            game_main()
        if creditss:
            creditss_main()

        menu_redraw()


def menu_redraw():
    global LastScore
    window.fill(settings.color_window_background)
    SnakeLogo.draw((settings.window_width - SnakeLogo.text_width) // 2, 4.5 * settings.grid)
    HighscoresInMenu.draw()
    TotalStatsInMenu.draw()
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
        if Snake.dirx or Snake.diry:  # snake started moving
            Snake.fpsCounter += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_notOver = False
            elif joystick and event.type == pygame.JOYAXISMOTION:
                if joystick.get_axis(3) < -settings.joystick_sentivity:  # ← -x
                    Snake.change_dir_left()
                elif joystick.get_axis(3) > settings.joystick_sentivity:  # → +x
                    Snake.change_dir_right()
                elif joystick.get_axis(4) < -settings.joystick_sentivity:  # ↑ -y
                    Snake.change_dir_up()
                elif joystick.get_axis(4) > settings.joystick_sentivity:  # ↓ +y
                    Snake.change_dir_down()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            game_notOver = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  # ← -x
            Snake.change_dir_left()
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:  # → +x
            Snake.change_dir_right()
        elif keys[pygame.K_UP] or keys[pygame.K_w]:  # ↑ -y
            Snake.change_dir_up()
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:  # ↓ +y
            Snake.change_dir_down()

        if Snake.fpsCounter % settings.move_delay == 0:
            Snake.move()

    logger.info(f"Game over, score: {Snake.score} (speed: {settings.speed}, time: {format_time(Snake.fpsCounter // settings.fps)})")
    pygame.mixer.music.pause()
    pygame.mixer.music.load(settings.path_music_GameOver)
    pygame.mixer.music.play()

    Data.total_games += 1
    Data.total_time += Snake.fpsCounter / settings.fps
    TotalStatsInMenu.update()
    # new record
    if Snake.score > Data.highscores_speed[(speed_str := str(settings.speed))]:
        logger.info(f"Highscore beaten, old: {Data.highscore}, new: {Snake.score} (speed {settings.speed})")
        Data.highscores_speed[speed_str] = Snake.score
        if Snake.score > Data.highscore:
            Data.highscore = Snake.score
        NewHighscoreText = Text(f"new highscore: {Snake.score} (speed {settings.speed})", settings.color_newhighscore, settings.font_size_newhighscore)
        NewHighscoreText.draw((settings.window_width - NewHighscoreText.text_width) // 2, (settings.window_height - GameOver.text_height) // 2 - GameOver.text_height + NewHighscoreText.text_height - 10)
        HighscoresInMenu.update()
    elif Snake.score > Data.highscore:
        logger.info(f"Highscore beaten, old: {Data.highscore}, new: {Snake.score} (speed {settings.speed})")
        Data.highscore = Snake.score
        NewHighscoreText = Text(f"new highscore: {Snake.score}", settings.color_newhighscore, settings.font_size_newhighscore)
        NewHighscoreText.draw((settings.window_width - NewHighscoreText.text_width) // 2, (settings.window_height - GameOver.text_height) // 2 - GameOver.text_height + NewHighscoreText.text_height - 10)
        HighscoresInMenu.update()
    Data.write()

    global LastScore
    LastScore = Text(f"last score: {Snake.score}", settings.color_font, settings.font_size_lastscore)

    gameover_main()

    game = False


def game_redraw():
    window.fill(settings.color_window_background)
    pygame.draw.rect(window, settings.color_game_background, (settings.game_x, settings.game_y, settings.game_width, settings.game_height))
    Snake.draw()
    Apple.draw()
    TopBar.draw()
    CurrentSpeedText.draw()
    pygame.display.update()


def gameover_main():
    GameOver.draw((settings.window_width - GameOver.text_width) // 2, (settings.window_height - GameOver.text_height) // 2)
    show_gameOver = True
    if joystick:
        joystick.rumble(0.2, 0.8, 500)

    while show_gameOver:
        clock.tick(settings.fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                show_gameOver = False
        keys = pygame.key.get_pressed()
        if not pygame.mixer.music.get_busy() or keys[pygame.K_SPACE] or keys[pygame.K_ESCAPE]:
            show_gameOver = False

        pygame.display.update()

    while True:  # wait for key to be released to avoid pressing it on menu
        clock.tick(settings.fps)

        pygame.event.get()
        keys = pygame.key.get_pressed()
        if not (keys[pygame.K_SPACE] or keys[pygame.K_ESCAPE]):
            break

        pygame.display.update()

    pygame.mixer.music.pause()
    if joystick:
        joystick.stop_rumble()


def creditss_main():
    global mouse
    global creditss
    global CreditsText
    global CreditsBackButton

    # I do not prerender it, as it is unlikely to be used often
    CreditsText = LongText("Icon: \n Icon made by Freepik from www.flaticon.com \n \n Music during gameplay: \n Tristan Lohengrin - Happy 8bit Loop 01 \n \n Sound after loss: \n Sad Trombone Wah Wah Wah Fail Sound Effect", settings.color_font, settings.font_size_creditsscene, line_lenght=52)
    CreditsBackButton = Button((settings.window_width - settings.button_width) // 2, 500, settings.button_width, settings.button_height, settings.color_button, settings.color_button_focused, settings.button_text_color, "Back", settings.button_text_size, ButtonCmds.creditssFalse)

    while creditss:
        clock.tick(settings.fps)

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                creditss = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                CreditsBackButton.click()  # Back to menu

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            creditss = False

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

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                error = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                ButtonExit2.click()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            error = False

        window.fill(settings.color_error_backgorund)
        ErrorText.draw((settings.window_width - ErrorText.text_width) / 2, (settings.window_height - ErrorText.text_height) / 2 - 60)
        ButtonExit2.draw()
        pygame.display.update()


############## Settings ##############

class settings:
    version = "1.3.1"
    grid = 25
    grid_border = 2
    window_width = grid * 33
    window_height = grid * 26
    topbar_width = window_width
    topbar_height = 2 * grid
    game_x = grid
    game_y = topbar_height
    game_width = window_width - 2 * grid  # odd multiples of grid
    game_height = window_height - topbar_height - grid  # odd multiples of grid

    color_window_background = (1, 170, 64)
    color_error_backgorund = (208, 26, 26)
    color_game_background = (0, 0, 0)
    color_button = (254, 151, 12)
    color_button_focused = (195, 122, 20)
    color_font = (255, 255, 255)
    color_gameover = (255, 0, 0)
    color_newhighscore = (0, 0, 255)
    color_snakeLogo = (255, 255, 255)
    color_author = (215, 215, 215)

    font_size_loading = 35
    font_size_error = 30
    font_size_gameover = 77
    font_size_newhighscore = 33
    font_size_snakeLogo = 62
    font_size_lastscore = 27
    font_size_author = 21
    font_size_website = 21
    font_size_creditsscene = 25
    font_size_speed = 22
    font_size_currentspeed = 17

    button_width = grid * 10
    button_height = grid * 4
    button_text_size = 35
    button_text_color = (255, 255, 255)

    ButtonPlay_y = 275
    ButtonExit_y = 420
    SpeedButton_width = 40
    SpeedButton_height = 35
    SpeedButton_spacing = 15

    if os.name == "nt":
        path_gameDirectory = MyPath.home() / "AppData" / "Roaming" / ".snake"  # ~\AppData\Roaming\.snake\
    else:
        path_gameDirectory = MyPath.home() / ".snake"  # ~/.snake/
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

    url_font = "https://cdn.discordapp.com/attachments/854111213709557821/956506488115974164/OpenSans-Bold.ttf"
    url_music_Game = "https://cdn.discordapp.com/attachments/854111213709557821/956506487579095070/Tristan_Lohengrin_-_Happy_8bit_Loop_01.ogg"
    url_music_GameOver = "https://cdn.discordapp.com/attachments/854111213709557821/956506487902068746/Sad_Trombone_Wah_Wah_Wah_Fail_Sound_Effect.ogg"
    url_website = "http://tiny.cc/snake_website"

    icon_content = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAABR1BMVEUAAABeswAAgABrygBnuwBrygBowQBnvAAAbwFnvgDlNBdrywBpwADuORRtvQBrzgAAgABnvQABcAFovgBsygBrygBrygBowQAAcwBqwwBqxQAAfgBpxwBxzgALdwFfwQALhwBcvwAAbQFnvgAxogBrygBnvgAFgwBovwBsywAnkABpxgAAcgAAcQBsygAAcgBrygA7nQBryABowQAAgAB6rAMAbQEAbAEokABrygAXjwBovQBmxwBrygADgQA0pQBwtwFnxgAAgAAAbwFBrQBovwBrygBovwBrygBqwAAAcQAAgABqygAAcQBovwA8pAAPgABrywAAdQBqzAAAgABrywAvoQAAgQBGsQAAcgAdlgAAdQAnlgBXrwBpwwBnugBrygAAgAAAaQExogDeLBsWgAE8qQBdtQA5qABnuwBSrAB7qARZsgAJeIArAAAAX3RSTlMABOLg/fpo+uLi28yjWRsU+Pbr3dXBh35dVU8+OQz8/Pz39PDv59nUwLSlkpKIZ2dINCwhFPn59/Lw7ezq6enm5d3c09HQxMS6tbSrqKWMiXh1dHNsYlxXRUM9MCcjEayMVDsAAAHASURBVEjH1dVnUwIxEAbgnByCYgERFMHeBREBe++993rhxAL4/z/LJbckJ8lMZnSc8f3Ezu5zQzbcgFRSn883wud/CZobtqZKpdWRWsX5iG7YCWoq850eo5I9FdBmsHhUwIjBJaMAhngQUQALPGhTAB4eNHzvPqdvr++ziE+BBzuOVsfhHMZvuVzOf3BT2XiTwSeIWGI+jLEFSIaj8BQH6GfzV24MgMR/ya5BdBERjAFAjkgj7gA6zKfd1cBstzq1DhAAsIsFoM/qaAHRWmNYBMxzcmqdzQ/B8sJisEEX2199bT4Yd29vzg/7AUzTbh0A9gYNAkhZVRSAKQWwoyVargPIysCLnQFarnxYKRaLj6ScfbVzUgFwzh5a9mIr5UdOkrLLtDP2c7BMyzUAT6RsAXBaBWpo2QqgiZReABO/BnwAYs6v1C4DowDqMghpCRPyIANxAEah8GmyaDKQooDknc17kQxog0IwLgUoKQJ9SA60EA/YjkQ/PppmVxVIIC7YTjeqiBAAdgAxgGgXOge8USQEi46/tuNgQC/fw0zL/h1CYuBCkvw9cNkgpArCNkiqgk76BoxqSFmEXe7WM7X5L+xVXXt8wCY7AAAAAElFTkSuQmCC"

    fps = 60
    speed = 5  # default speed (aka movesPerSecond) (fps divisor)
    speed_list = [5, 10, 15, 30, 60]
    move_delay = fps / speed

    joystick_sentivity = 0.91


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
formatter = logging.Formatter("%(asctime)s [%(levelname)s] (Line %(lineno)d in %(funcName)s) - %(message)s")
file_handler = logging.FileHandler(filename=settings.path_log1, mode="a")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

#### Main game code ####
logger.info(f"Starting Snake v{settings.version}")
logger.info(f"System: {platform.system()}, version: {platform.release()}")
pygame.display.init()
pygame.mixer.init()
pygame.font.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() else False
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
HighscoresInMenu = HighscoresInMenuClass()
TotalStatsInMenu = TotalStatsInMenuClass()

Snake = SnakeClass()
Apple = AppleClass()
TopBar = TopBarClass()
CurrentSpeedText = CurrentSpeedTextClass()

menu_main()

logger.info("Quitting")

pygame.quit()
