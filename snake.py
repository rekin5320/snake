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

def thousands_separators(n):
    """Inserts spaces as thousands separator."""
    return f"{n:,}".replace(",", " ")


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


class Tee:
    """
    Duplicates the given stream into a file.
    Inspired by https://stackoverflow.com/a/616686
    """
    def __init__(self, out_stream, filename, mode):
        self.file = open(filename, mode)
        self.out_stream = out_stream

    def __del__(self):
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.out_stream.write(data)

    def flush(self):
        self.file.flush()


def base64_encode(text):
    encodedtext_bytes = base64.b64encode(text.encode("utf-8"))
    encodedtext = str(encodedtext_bytes, "utf-8")
    return encodedtext


def base64_decode(text):
    decodedtext_bytes = base64.b64decode(text)
    decodedtext = str(decodedtext_bytes, "utf-8")
    return decodedtext


def format_time(seconds, milliseconds=False):
    if milliseconds:
        return f"{seconds // 60:02.0f}:{seconds % 60:06.3f}"
    else:
        if not isinstance(seconds, int):
            seconds = round(seconds)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02}:{seconds:02}"


class Text:
    def __init__(self, text, color, font_size, sysfont=False):
        if sysfont:
            self.font = pygame.font.SysFont("Verdana", font_size, bold=True)
        else:
            self.font = pygame.font.Font(conf.path_font, font_size)
        self.text = self.font.render(text, True, color)
        self.width, self.height = self.text.get_size()

    def draw(self, x, y):
        window.blit(self.text, (x, y))


class LongText:
    def __init__(self, text, color, font_size, line_length=40, line_spacing=6):
        self.line_spacing = line_spacing
        lines = self.split_into_lines(text, line_length)
        self.renderedTextList = [Text(line, color, font_size) for line in lines]
        self.width = max(T.width for T in self.renderedTextList)
        self.line_height = self.renderedTextList[0].height
        self.height = len(self.renderedTextList) * (self.line_height + self.line_spacing) - self.line_spacing

    @staticmethod
    def split_into_lines(text, line_length):
        words = text.split(" ")
        words_len = len(words)
        i = 0
        textList = []
        curr_line = ""
        while i < words_len:
            if words[i] == "\n":
                textList.append(curr_line)
                curr_line = ""
                i += 1
            elif line_length - len(curr_line) - 1 >= len(words[i]):
                if curr_line:
                    curr_line += " "
                curr_line += words[i]
                i += 1
            elif len(words[i]) >= line_length:
                textList.append(curr_line)
                textList.append(words[i])
                curr_line = ""
                i += 1
            else:
                textList.append(curr_line)
                curr_line = ""

        if curr_line:
            textList.append(curr_line)

        return textList

    def draw(self, x, y):
        i = 0
        for line in self.renderedTextList:
            line.draw(x, y + i)
            i += self.line_height + self.line_spacing


class RoundedRectangle:
    def __init__(self, width, height, radius, color):
        self.width = width
        self.height = height
        self.radius = radius
        self.color = color

    def draw(self, x, y):
        pygame.draw.rect(window, self.color, (x, y, self.width, self.height), border_radius=self.radius)


def draw_tile(color, x, y):
    pygame.draw.rect(window, color, (x, y, conf.tile_width, conf.tile_width), border_radius=conf.tile_radius)


class Button:
    def __init__(self, x, y, width, height, text, font_size, color1=(254, 151, 12), color2=(195, 122, 20), color_text=(255, 255, 255), command=None, radius=9):
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
        self.text.draw(self.x + (self.width - self.text.width) // 2, self.y + (self.height - self.text.height) // 2)


class ButtonSpeed(Button):
    def __init__(self, x, y, width, height, font_size, desired_value):
        super().__init__(x, y, width, height, str(desired_value), font_size, radius=4)
        self.desired_value = desired_value

    def click(self):
        if self.is_pointed() and conf.speed != self.desired_value:
            conf.change_speed_to(self.desired_value)

    def is_highlighted(self):
        return super().is_pointed() or conf.speed == self.desired_value


class ButtonSpeedGroup:
    def __init__(self):
        self.speed_list = conf.speed_list
        self.width_single = 40
        self.spacing = 11
        self.width_total = len(conf.speed_list) * (self.width_single + self.spacing) - self.spacing
        self.height = 35
        self.x = conf.window_width - self.width_total - conf.margin
        self.y = conf.margin
        self.font_size = 22
        self.dec, self.inc = False, False

        self.ButtonsList = []
        for index, value in enumerate(self.speed_list):
            self.ButtonsList.append(ButtonSpeed(self.x + index * (self.spacing + self.width_single), self.y, self.width_single, self.height, self.font_size, value))

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
        if self.dec or self.inc:
            i = conf.speed_list.index(conf.speed)
            if self.dec:
                if i > 0:
                    conf.change_speed_to(conf.speed_list[i - 1])
                    self.dec, self.inc = False, False
            else:
                if i < len(conf.speed_list) - 1:
                    conf.change_speed_to(conf.speed_list[i + 1])
                    self.dec, self.inc = False, False


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
    def creditssTrue():
        global creditss
        creditss = True

    @staticmethod
    def creditssFalse():
        global creditss
        creditss = False


class File:  # Data
    def __init__(self):
        self.path_data = conf.path_data

    def read(self):
        try:
            with conf.path_version.open("r") as file:
                self.version = base64_decode(file.readline())

            with self.path_data.open("r") as file:
                data = base64_decode(file.readline())

            self.datadict = json.loads(data)
            self.highscore = self.datadict.get("highscore", 0)
            highscores_speed = self.datadict.get("highscores_speed", {})
            self.highscores_speed = {i: highscores_speed.get(i, 0) for i in map(str, sorted(conf.speed_list))}
            self.total_games = self.datadict.get("total_games", 0)
            self.total_time = self.datadict.get("total_time", 0)
            self.volume = self.datadict.get("volume", 0.9)

            if "speed" in self.datadict:
                conf.speed = self.datadict["speed"]
                conf.move_delay = conf.fps // conf.speed

        except:
            logger.exception("Error while reading game data:")
            error_screen("Error while reading game data")

        else:
            logger.info("Game data successfully read")

    def write(self):
        try:
            logger.debug("Writing data")
            conf.path_data.replace(conf.path_data_backup)
            self.datadict["version"] = conf.version
            self.datadict["speed"] = conf.speed
            self.datadict["highscore"] = self.highscore
            self.datadict["highscores_speed"] = self.highscores_speed
            self.datadict["total_games"] = self.total_games
            self.datadict["total_time"] = round(self.total_time, 3)
            self.datadict["volume"] = round(self.volume, 1)
            with self.path_data.open("w") as file:
                file.write(self.dump_data())
                file.write("\neyJqdXN0IGZvdW5kIGFuIEVhc3RlciBFZ2c/PyI6IHRydWV9")
            conf.path_version.write_text(base64_encode(conf.version))

        except Exception as err:
            logger.error(err)
            logger.error(traceback.format_exc())
            error_screen("Error while writing game data")

    def dump_data(self):
        return base64_encode(json.dumps(self.datadict, separators=(",", ":")))


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
    if not conf.path_version.is_good():
        logger.warning("Version file did not exist, trying to create")
        conf.path_version.write_text(base64_encode(conf.version))
        logger.warning("Version file successfully created")

    if not conf.path_data.is_good():
        logger.warning("Data file did not exist, trying to create")
        with conf.path_data.open("w") as file:
            file.write(base64_encode(json.dumps({})))
            file.write("\neyJqdXN0IGZvdW5kIGFuIEVhc3RlciBFZ2c/PyI6IHRydWV9")
        logger.warning("Data file successfully created")

    download_if_needed(conf.path_font, conf.url_font, "Font")
    download_if_needed(conf.path_music_Game, conf.url_music_Game, "Game music")
    download_if_needed(conf.path_music_GameOver, conf.url_music_GameOver, "GameOver music")

    logger.info("Checking files done")


class SnakeClass:
    def __init__(self):
        self.velocity = conf.grid
        self.color_head = (255, 255, 255)
        self.colors_tail = [(3, 255, 3), (2, 232, 2), (1, 187, 0)]
        self.colors_tail_len = len(self.colors_tail)
        self.reinit()

    def reinit(self):
        self.dirx = 0
        self.diry = 0
        self.dirx_current = 0
        self.diry_current = 0
        self.x = (conf.game_width - conf.grid) // 2 + conf.game_x
        self.y = (conf.game_height - conf.grid) // 2 + conf.game_y
        self.xyList = [(self.x + conf.grid_border, self.y + conf.grid_border)]
        self.fpsCounter = 0
        self.score = 0

    def change_dir_left(self):
        if self.dirx_current == 0:
            self.dirx = -self.velocity
            self.diry = 0

    def change_dir_right(self):
        if self.dirx_current == 0:
            self.dirx = self.velocity
            self.diry = 0

    def change_dir_up(self):
        if self.diry_current == 0:
            self.dirx = 0
            self.diry = -self.velocity

    def change_dir_down(self):
        if self.diry_current == 0:
            self.dirx = 0
            self.diry = self.velocity

    def move(self):
        global game_notOver
        self.dirx_current = self.dirx
        self.diry_current = self.diry

        if self.dirx != 0:
            self.x += self.dirx
        elif self.diry != 0:
            self.y += self.diry
        self.head_location = (self.x + conf.grid_border, self.y + conf.grid_border)

        if self.x == conf.game_x - conf.grid or self.x == conf.game_width + conf.grid or self.y == conf.game_y - conf.grid or self.y == conf.game_height + conf.topbar_height:
            game_notOver = False

        for pair in self.xyList[:-1]:  # collision with itself
            if self.head_location == pair:
                game_notOver = False

        self.xyList.append(self.head_location)

        if self.head_location == Apple.location:  # ate the apple
            self.score += 1
            Apple.move()
        else:
            self.xyList.pop(0)

        if self.head_location == Banana.location:
            self.score -= 1
            self.xyList.pop(0)
            if self.score < 0:
                self.score = 0
                game_notOver = False
            Banana.move()

    def draw(self):
        for i, (x, y) in enumerate(self.xyList[:-1], start=1):
            color_num = (self.score - i) % self.colors_tail_len
            draw_tile(self.colors_tail[color_num], x, y)
        draw_tile(self.color_head, *self.xyList[-1])


class AppleClass:
    def __init__(self):
        self.color = (255, 0, 0)
        self.width = conf.tile_width
        self.location = None

    def move(self):
        self.x = randrange(0, conf.game_width // conf.grid) * conf.grid + conf.game_x
        self.y = randrange(0, conf.game_height // conf.grid) * conf.grid + conf.game_y
        self.location = (self.x + conf.grid_border, self.y + conf.grid_border)
        if self.location in Snake.xyList or self.location == Banana.location:
            self.move()

    def draw(self):
        draw_tile(self.color, *self.location)


class BananaClass:
    def __init__(self):
        self.color = (255, 255, 0)
        self.width = conf.tile_width
        self.lifetime_default = conf.fps * 10  # seconds
        self.location = None

    def move(self):
        self.x = randrange(0, conf.game_width // conf.grid) * conf.grid + conf.game_x
        self.y = randrange(0, conf.game_height // conf.grid) * conf.grid + conf.game_y
        self.location = (self.x + conf.grid_border, self.y + conf.grid_border)
        if self.location in Snake.xyList or self.location == Apple.location:
            self.move()
        else:
            self.lifetime = self.lifetime_default

    def draw(self):
        draw_tile(self.color, *self.location)


class TopBarClass:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = conf.topbar_width
        self.height = conf.topbar_height
        self.font_size = int(1.04 * conf.grid)

    def draw(self):
        Time = Text(f"time: {format_time(Snake.fpsCounter // conf.fps)}", conf.color_font, self.font_size)
        Time.draw(1.4 * conf.grid, (self.height - Time.height) // 2)

        Score = Text(f"score: {thousands_separators(Snake.score)}", conf.color_font, self.font_size)
        Score.draw((self.width - Score.width) // 2, (self.height - Score.height) // 2)

        HighscoreOnBar = Text(f"highscore: {thousands_separators(Data.highscores_speed[str(conf.speed)])}", conf.color_font, self.font_size)
        HighscoreOnBar.draw(self.width - conf.grid - HighscoreOnBar.width - 0.4 * conf.grid, (self.height - HighscoreOnBar.height) // 2)


class CurrentSpeedTextClass:
    def __init__(self):
        self.update()
        self.x = 1.4 * conf.grid
        self.y = 25 * conf.grid + (conf.grid - self.text.height) // 2

    def update(self):
        self.text = Text(f"speed: {conf.speed}", conf.color_font, conf.font_size_currentspeed)

    def draw(self):
        self.text.draw(self.x, self.y)


class HighscoresInMenuClass:
    def __init__(self):
        self.x1 = conf.margin
        self.x2 = conf.margin + 15
        self.y1 = conf.margin - 4
        self.color = conf.color_font
        self.font_size1 = 23
        self.font_size2 = 21
        self.update()
        self.y_bottom = self.y2 + self.text2.height

    def update(self):
        self.text1 = Text("Highscores:", self.color, self.font_size1)
        self.text2 = LongText(f"• overall: {Data.highscore} \n " + " \n ".join([f"• {k}: {v}" for k, v in Data.highscores_speed.items()]), self.color, self.font_size2, line_spacing=6)
        self.y2 = conf.margin + self.text1.height

    def draw(self):
        self.text1.draw(self.x1, self.y1)
        self.text2.draw(self.x2, self.y2)


class TotalStatsInMenuClass:
    def __init__(self):
        self.x = conf.margin
        self.y1 = HighscoresInMenu.y_bottom + 7
        self.color = conf.color_font
        self.font_size = 20
        self.update()
        self.y2 = self.y1 + self.text_games.height + 5

    def update(self):
        self.text_games = Text(f"total games: {Data.total_games}", self.color, self.font_size)
        self.text_time = Text(f"total time: {format_time(Data.total_time)}", self.color, self.font_size)

    def draw(self):
        self.text_games.draw(self.x, self.y1)
        self.text_time.draw(self.x, self.y2)


class VolumeWidgetInMenuClass:
    def __init__(self):
        self.button_dim = 22
        self.font_size = 22
        self.spacing = 10

        self.update()
        self.y_text = conf.margin + SpeedButtons.ButtonsList[0].height + 9
        self.y_buttons = self.y_text + (self.text.height - self.button_dim) // 2
        self.x_button_minus = conf.window_width - conf.margin - self.button_dim
        self.x_button_plus = self.x_button_minus - self.spacing - self.button_dim
        self.button_minus = Button(self.x_button_minus, self.y_buttons, self.button_dim, self.button_dim, "−", self.font_size, command=VolumeWidgetInMenuClass.decrease)
        self.button_plus = Button(self.x_button_plus, self.y_buttons, self.button_dim, self.button_dim, "+", self.font_size, command=VolumeWidgetInMenuClass.increase)

    def update(self):
        pygame.mixer.music.set_volume(Data.volume)
        self.text = Text(f"Volume: {Data.volume:.0%}", conf.color_font, self.font_size)
        self.x_text = conf.window_width - conf.margin - 2 * (self.spacing + self.button_dim) - self.text.width

    @staticmethod
    def decrease():
        Data.volume -= 0.1
        if Data.volume < 0:
            Data.volume = 0
        logger.info(f"Changed volume to {Data.volume:.0%}")
        Data.write()
        VolumeWidgetInMenu.update()

    @staticmethod
    def increase():
        Data.volume += 0.1
        if Data.volume > 1:
            Data.volume = 1
        logger.info(f"Changed volume to {Data.volume:.0%}")
        Data.write()
        VolumeWidgetInMenu.update()

    def draw(self):
        self.button_minus.draw()
        self.button_plus.draw()
        self.text.draw(self.x_text, self.y_text)


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
        clock.tick(conf.fps)

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ButtonPlay.click()     # Game
                ButtonExit.click()     # Exit
                WebsiteButton.click()  # Website
                CreditsButton.click()  # Credits
                SpeedButtons.click()   # Speed buttons
                VolumeWidgetInMenu.button_minus.click()
                VolumeWidgetInMenu.button_plus.click()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            menu = False
        if keys[pygame.K_SPACE]:
            game = True

        if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            SpeedButtons.await_decrease()
        elif (keys[pygame.K_EQUALS] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])) or keys[pygame.K_KP_PLUS]:
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
    window.fill(conf.color_window_background)
    SnakeLogo.draw((conf.window_width - SnakeLogo.width) // 2, 4.5 * conf.grid)
    HighscoresInMenu.draw()
    TotalStatsInMenu.draw()
    if LastScore:
        LastScore.draw((conf.window_width - LastScore.width) // 2, 205)
    ButtonPlay.draw()
    ButtonExit.draw()
    Author.draw(conf.window_width - conf.margin - Author.width, conf.window_height - conf.margin - Author.height)
    WebsiteButton.draw()
    CreditsButton.draw()
    SpeedText.draw(conf.window_width - conf.margin - SpeedButtons.width_total - SpeedButtons.spacing - SpeedText.width, conf.margin + (SpeedButtons.height - SpeedText.height) // 2)
    SpeedButtons.draw()
    VolumeWidgetInMenu.draw()

    pygame.display.update()


def game_main():
    global game_notOver
    global game
    pygame.mixer.music.load(conf.path_music_Game)
    pygame.mixer.music.play(loops=-1)
    Snake.reinit()
    Apple.move()
    Banana.move()
    game_notOver = True

    while game_notOver:
        clock.tick(conf.fps)

        if Snake.fpsCounter % conf.move_delay == 0:
            game_redraw()
        if Snake.dirx or Snake.diry:  # snake started moving
            Snake.fpsCounter += 1
            Banana.lifetime -= 1
            if Banana.lifetime == 0:
                Banana.move()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_notOver = False
            elif joystick and event.type == pygame.JOYAXISMOTION:
                if joystick.get_axis(3) < -conf.joystick_sensitivity:  # ← -x
                    Snake.change_dir_left()
                elif joystick.get_axis(3) > conf.joystick_sensitivity:  # → +x
                    Snake.change_dir_right()
                elif joystick.get_axis(4) < -conf.joystick_sensitivity:  # ↑ -y
                    Snake.change_dir_up()
                elif joystick.get_axis(4) > conf.joystick_sensitivity:  # ↓ +y
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

        if Snake.fpsCounter % conf.move_delay == 0:
            Snake.move()

    logger.info(f"Game over, score: {Snake.score} (speed: {conf.speed}, time: {format_time(Snake.fpsCounter / conf.fps, milliseconds=True)})")
    pygame.mixer.music.pause()
    pygame.mixer.music.load(conf.path_music_GameOver)
    pygame.mixer.music.play()

    Data.total_games += 1
    Data.total_time += Snake.fpsCounter / conf.fps
    TotalStatsInMenu.update()
    # new record
    if Snake.score > Data.highscores_speed[(speed_str := str(conf.speed))]:
        logger.info(f"Highscore beaten, old: {Data.highscores_speed[speed_str]}, new: {Snake.score} (speed {conf.speed})")
        Data.highscores_speed[speed_str] = Snake.score
        if Snake.score > Data.highscore:
            Data.highscore = Snake.score
        NewHighscoreText = Text(f"new highscore: {Snake.score} (speed {conf.speed})", conf.color_newhighscore, conf.font_size_newhighscore)
        NewHighscoreText.draw((conf.window_width - NewHighscoreText.width) // 2, (conf.window_height - GameOver.height) // 2 - GameOver.height + NewHighscoreText.height - 10)
        HighscoresInMenu.update()
    elif Snake.score > Data.highscore:
        logger.info(f"Highscore beaten, old: {Data.highscore}, new: {Snake.score} (speed {conf.speed})")
        Data.highscore = Snake.score
        NewHighscoreText = Text(f"new highscore: {Snake.score}", conf.color_newhighscore, conf.font_size_newhighscore)
        NewHighscoreText.draw((conf.window_width - NewHighscoreText.width) // 2, (conf.window_height - GameOver.height) // 2 - GameOver.height + NewHighscoreText.height - 10)
        HighscoresInMenu.update()
    Data.write()

    global LastScore
    LastScore = Text(f"last score: {Snake.score}", conf.color_font, conf.font_size_lastscore)

    gameover_main()

    game = False


def game_redraw():
    window.fill(conf.color_window_background)
    pygame.draw.rect(window, conf.color_game_background, (conf.game_x, conf.game_y, conf.game_width, conf.game_height))
    Snake.draw()
    Apple.draw()
    Banana.draw()
    TopBar.draw()
    CurrentSpeedText.draw()
    pygame.display.update()


def gameover_main():
    GameOver.draw((conf.window_width - GameOver.width) // 2, (conf.window_height - GameOver.height) // 2)
    show_gameOver = True
    if joystick:
        joystick.rumble(0.2, 0.8, 500)

    while show_gameOver:
        clock.tick(conf.fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                show_gameOver = False
        keys = pygame.key.get_pressed()
        if not pygame.mixer.music.get_busy() or keys[pygame.K_SPACE] or keys[pygame.K_ESCAPE]:
            show_gameOver = False

        pygame.display.update()

    while True:  # wait for key to be released to avoid pressing it on menu
        clock.tick(conf.fps)

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
    CreditsText = LongText("Icon: \n Icon made by Freepik from www.flaticon.com \n \n Music during gameplay: \n Tristan Lohengrin - Happy 8bit Loop 01 \n \n Sound after loss: \n Sad Trombone Wah Wah Wah Fail Sound Effect", conf.color_font, conf.font_size_creditsscene, line_length=52)
    CreditsBackButton = Button((conf.window_width - conf.button_width) // 2, 500, conf.button_width, conf.button_height, "Back", conf.button_font_size, command=ButtonCmds.creditssFalse)

    while creditss:
        clock.tick(conf.fps)

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                creditss = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                CreditsBackButton.click()  # Back to menu

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            creditss = False

        creditss_redraw()


def creditss_redraw():
    global CreditsText
    global CreditsBackButton
    window.fill(conf.color_window_background)
    CreditsText.draw((conf.window_width - CreditsText.width) // 2, 90)
    CreditsBackButton.draw()
    pygame.display.update()


def loading_screen(function, loading_text, error_text, sysfont=False):
    thread = MyThread(target=function, daemon=True)
    thread.start()
    time = 0
    LoadingTexts = (
        Text(loading_text, conf.color_font, conf.font_size_loading, sysfont=sysfont),
        Text(f"{loading_text}.", conf.color_font, conf.font_size_loading, sysfont=sysfont),
        Text(f"{loading_text}..", conf.color_font, conf.font_size_loading, sysfont=sysfont),
        Text(f"{loading_text}...", conf.color_font, conf.font_size_loading, sysfont=sysfont)
    )

    while thread.is_alive():
        clock.tick(conf.fps)
        window.fill(conf.color_window_background)
        Loading = LoadingTexts[time // conf.fps % 4]
        Loading.draw((conf.window_width - Loading.width) / 2, (conf.window_height - Loading.height) / 2)
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
    ErrorText = LongText(text, conf.color_font, conf.font_size_error)
    ButtonExit2 = Button((conf.window_width - conf.button_width) // 2, 500, conf.button_width, conf.button_height, "Exit", conf.button_font_size, command=lambda: sys.exit(1))

    while error:
        clock.tick(conf.fps)

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                error = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ButtonExit2.click()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            error = False

        window.fill(conf.color_error_background)
        ErrorText.draw((conf.window_width - ErrorText.width) / 2, (conf.window_height - ErrorText.height) / 2 - 60)
        ButtonExit2.draw()
        pygame.display.update()


####### Settings / Config #######

class conf:
    version = "1.6.0"
    grid = 25
    grid_border = 2
    window_width = grid * 33
    window_height = grid * 26
    margin = 12
    topbar_width = window_width
    topbar_height = 2 * grid
    game_x = grid
    game_y = topbar_height
    game_width = window_width - 2 * grid  # odd multiples of grid
    game_height = window_height - topbar_height - grid  # odd multiples of grid
    tile_width = grid - 2 * grid_border
    tile_radius = 2

    color_window_background = (1, 170, 64)
    color_error_background = (208, 26, 26)
    color_game_background = (0, 0, 0)
    color_font = (255, 255, 255)
    color_newhighscore = (0, 0, 255)

    font_size_loading = 35
    font_size_error = 30
    font_size_newhighscore = 33
    font_size_lastscore = 27
    font_size_website = 21
    font_size_creditsscene = 25
    font_size_currentspeed = 17

    button_width = grid * 10
    button_height = grid * 4
    button_font_size = 35

    ButtonPlay_y = 275
    ButtonExit_y = 420

    if os.name == "nt":
        path_gameDir = MyPath.home() / "AppData" / "Roaming" / ".snake"  # ~\AppData\Roaming\.snake\
    else:
        path_gameDir = MyPath.home() / ".snake"  # ~/.snake/
    path_data = path_gameDir / "data"  # ~/.snake/data
    path_data_backup = path_gameDir / "data.backup"  # ~/.snake/data.backup
    path_version = path_gameDir / "version"  # ~/.snake/version
    path_assetsDir = path_gameDir / "assets"  # ~/.snake/assets/
    path_font = path_assetsDir / "OpenSans-Bold.ttf"
    path_music_Game = path_assetsDir / "Tristan Lohengrin - Happy 8bit Loop 01.ogg"
    path_music_GameOver = path_assetsDir / "Sad Trombone Wah Wah Wah Fail Sound Effect.ogg"
    path_icon = path_assetsDir / "icon.png"
    path_logDir = path_gameDir / "logs"  # ~/.snake/logs/
    path_log1 = path_logDir / "1.log"
    path_log2 = path_logDir / "2.log"
    path_log3 = path_logDir / "3.log"
    path_log4 = path_logDir / "4.log"

    url_font = "https://cdn.discordapp.com/attachments/854111213709557821/956506488115974164/OpenSans-Bold.ttf"
    url_music_Game = "https://cdn.discordapp.com/attachments/854111213709557821/956506487579095070/Tristan_Lohengrin_-_Happy_8bit_Loop_01.ogg"
    url_music_GameOver = "https://cdn.discordapp.com/attachments/854111213709557821/956506487902068746/Sad_Trombone_Wah_Wah_Wah_Fail_Sound_Effect.ogg"
    url_website = "http://tiny.cc/snake_website"

    icon_content = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAABR1BMVEUAAABeswAAgABrygBnuwBrygBowQBnvAAAbwFnvgDlNBdrywBpwADuORRtvQBrzgAAgABnvQABcAFovgBsygBrygBrygBowQAAcwBqwwBqxQAAfgBpxwBxzgALdwFfwQALhwBcvwAAbQFnvgAxogBrygBnvgAFgwBovwBsywAnkABpxgAAcgAAcQBsygAAcgBrygA7nQBryABowQAAgAB6rAMAbQEAbAEokABrygAXjwBovQBmxwBrygADgQA0pQBwtwFnxgAAgAAAbwFBrQBovwBrygBovwBrygBqwAAAcQAAgABqygAAcQBovwA8pAAPgABrywAAdQBqzAAAgABrywAvoQAAgQBGsQAAcgAdlgAAdQAnlgBXrwBpwwBnugBrygAAgAAAaQExogDeLBsWgAE8qQBdtQA5qABnuwBSrAB7qARZsgAJeIArAAAAX3RSTlMABOLg/fpo+uLi28yjWRsU+Pbr3dXBh35dVU8+OQz8/Pz39PDv59nUwLSlkpKIZ2dINCwhFPn59/Lw7ezq6enm5d3c09HQxMS6tbSrqKWMiXh1dHNsYlxXRUM9MCcjEayMVDsAAAHASURBVEjH1dVnUwIxEAbgnByCYgERFMHeBREBe++993rhxAL4/z/LJbckJ8lMZnSc8f3Ezu5zQzbcgFRSn883wud/CZobtqZKpdWRWsX5iG7YCWoq850eo5I9FdBmsHhUwIjBJaMAhngQUQALPGhTAB4eNHzvPqdvr++ziE+BBzuOVsfhHMZvuVzOf3BT2XiTwSeIWGI+jLEFSIaj8BQH6GfzV24MgMR/ya5BdBERjAFAjkgj7gA6zKfd1cBstzq1DhAAsIsFoM/qaAHRWmNYBMxzcmqdzQ/B8sJisEEX2199bT4Yd29vzg/7AUzTbh0A9gYNAkhZVRSAKQWwoyVargPIysCLnQFarnxYKRaLj6ScfbVzUgFwzh5a9mIr5UdOkrLLtDP2c7BMyzUAT6RsAXBaBWpo2QqgiZReABO/BnwAYs6v1C4DowDqMghpCRPyIANxAEah8GmyaDKQooDknc17kQxog0IwLgUoKQJ9SA60EA/YjkQ/PppmVxVIIC7YTjeqiBAAdgAxgGgXOge8USQEi46/tuNgQC/fw0zL/h1CYuBCkvw9cNkgpArCNkiqgk76BoxqSFmEXe7WM7X5L+xVXXt8wCY7AAAAAElFTkSuQmCC"

    fps = 120
    speed = 10  # default speed (aka movesPerSecond) (fps divisor)
    speed_list = [5, 10, 15, 30, 60]
    move_delay = fps // speed

    @classmethod
    def change_speed_to(cls, s):
        cls.speed = s
        cls.move_delay = cls.fps / cls.speed
        logger.info(f"Changed speed to {s}")
        Data.write()
        CurrentSpeedText.update()

    joystick_sensitivity = 0.91


############# Main code #############
if __name__ == "__main__":
    #### Initializing game data ####
    # moved from checkFiles() to make sure there is a game directory, so that the log file can be put there and game icon set
    if not conf.path_gameDir.exists():
        conf.path_gameDir.mkdir()
    if not conf.path_logDir.exists():
        conf.path_logDir.mkdir()
    if not conf.path_assetsDir.exists():
        conf.path_assetsDir.mkdir()

    if not conf.path_icon.exists():
        conf.path_icon.write_bytes(base64.b64decode(conf.icon_content))

    #### Logging configuration ####
    if conf.path_log4.exists():
        conf.path_log4.unlink()
    if conf.path_log3.exists():
        conf.path_log3.replace(conf.path_log4)
    if conf.path_log2.exists():
        conf.path_log2.replace(conf.path_log3)
    if conf.path_log1.exists():
        conf.path_log1.replace(conf.path_log2)

    sys.stderr = Tee(sys.stderr, conf.path_log1, "a")

    for handler in logging.root.handlers[:]:  # this is needed in PyCharm and can be left for safety
        logging.root.removeHandler(handler)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] (Line %(lineno)d in %(funcName)s) - %(message)s")
    file_handler = logging.FileHandler(filename=conf.path_log1, mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    logger.addHandler(stdout_handler)

    #### Main game code ####
    logger.info(f"Starting Snake v{conf.version}")
    logger.info(f"System: {platform.system()}, version: {platform.release()}")
    pygame.display.init()
    pygame.mixer.init()
    pygame.font.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() else False
    clock = pygame.time.Clock()
    window = pygame.display.set_mode((conf.window_width, conf.window_height), vsync=1)
    pygame.display.set_caption(f"Snake v{conf.version}")
    pygame.display.set_icon(pygame.image.load(conf.path_icon))

    loading_screen(checkFiles, "Loading", "Program encountered a problem while creating local files. Check Your Internet connection and try again.", sysfont=not conf.path_font.is_good())
    Data = File()
    Data.read()

    # Prerendered objects
    GameOver = Text("GAME  OVER", (255, 0, 0), 77)
    SnakeLogo = Text("Snake Game", (255, 255, 255), 62)
    Author = Text("Michał Machnikowski 2023", (215, 215, 215), 21)

    ButtonPlay = Button((conf.window_width - conf.button_width) // 2, conf.ButtonPlay_y, conf.button_width, conf.button_height, "Play", conf.button_font_size, command=ButtonCmds.gameTrue)
    ButtonExit = Button((conf.window_width - conf.button_width) // 2, conf.ButtonExit_y, conf.button_width, conf.button_height, "Exit", conf.button_font_size, command=ButtonCmds.menuFalse)
    WebsiteButton = Button(conf.margin, conf.window_height - conf.margin - 2 * conf.grid, int(4.85 * conf.grid), 2 * conf.grid, "website", conf.font_size_website, command=lambda: webbrowser.open(conf.url_website, new=0, autoraise=True), radius=7)
    CreditsButton = Button(conf.margin + int(5.5 * conf.grid), conf.window_height - conf.margin - 2 * conf.grid, int(4.65 * conf.grid), 2 * conf.grid, "credits", conf.font_size_website, command=ButtonCmds.creditssTrue, radius=7)

    SpeedText = Text("Speed:", conf.color_font, 22)
    SpeedButtons = ButtonSpeedGroup()
    HighscoresInMenu = HighscoresInMenuClass()
    TotalStatsInMenu = TotalStatsInMenuClass()
    VolumeWidgetInMenu = VolumeWidgetInMenuClass()

    Snake = SnakeClass()
    Apple = AppleClass()
    Banana = BananaClass()
    TopBar = TopBarClass()
    CurrentSpeedText = CurrentSpeedTextClass()

    menu_main()

    logger.info("Quitting")
    logger.debug(Data.dump_data())

    pygame.quit()
