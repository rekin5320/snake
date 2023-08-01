#!/usr/bin/env python3

from collections.abc import Callable
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

from utils import base64_decode, base64_encode, thousands_separators, format_time


######## Classes, functions and definitions ########

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


class Text:
    def __init__(self, text: str, color, font_size: int):
        self.font = pygame.font.Font(conf.path_font, font_size)
        self.text = self.font.render(text, True, color)
        self.width, self.height = self.text.get_size()

    def draw(self, x: int, y: int):
        window.blit(self.text, (x, y))


class LongText:
    def __init__(self, text: str, color, font_size: int, line_length: int = 40, line_spacing: int = 1):
        self.line_spacing = line_spacing
        lines = self.split_into_lines(text, line_length)
        self.renderedTextList = [Text(line, color, font_size) for line in lines]
        self.width = max(T.width for T in self.renderedTextList)
        self.line_height = self.renderedTextList[0].height
        self.height = len(self.renderedTextList) * (self.line_height + self.line_spacing) - self.line_spacing

    @staticmethod
    def split_into_lines(text: str, line_length: int):
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
            elif words[i] == "\t":
                curr_line += "    "
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

    def draw(self, x: int, y: int):
        i = 0
        for line in self.renderedTextList:
            line.draw(x, y + i)
            i += self.line_height + self.line_spacing


class RoundedRectangle:
    def __init__(self, width: int, height: int, radius: int, color):
        self.width = width
        self.height = height
        self.radius = radius
        self.color = color

    def draw(self, x: int, y: int):
        pygame.draw.rect(window, self.color, (x, y, self.width, self.height), border_radius=self.radius)


def draw_tile(color, x: int, y: int):
    pygame.draw.rect(window, color, (x, y, conf.tile_width, conf.tile_width), border_radius=conf.tile_radius)


class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font_size: int, color1=(254, 151, 12), color2=(195, 122, 20), color_text=(255, 255, 255), command: Callable = lambda: None, radius: int = 9):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.background1 = RoundedRectangle(width, height, radius, color1)
        self.background2 = RoundedRectangle(width, height, radius, color2)
        self.text = Text(text, color_text, font_size)
        self.command = command

    def is_pointed(self, mouse):
        return self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height

    def is_highlighted(self, mouse):
        return self.is_pointed(mouse)

    def click(self, mouse):
        if self.is_pointed(mouse):
            self.command()

    def draw(self, mouse):
        if self.is_highlighted(mouse):
            self.background2.draw(self.x, self.y)
        else:
            self.background1.draw(self.x, self.y)
        self.text.draw(self.x + (self.width - self.text.width) // 2, self.y + (self.height - self.text.height) // 2)


class ButtonSpeed(Button):
    def __init__(self, x: int, y: int, width: int, height: int, font_size: int, desired_value: int):
        super().__init__(x, y, width, height, str(desired_value), font_size, radius=4)
        self.desired_value = desired_value

    def click(self, mouse):
        if self.is_pointed(mouse) and conf.speed != self.desired_value:
            conf.change_speed_to(self.desired_value)

    def is_highlighted(self, mouse):
        return super().is_pointed(mouse) or conf.speed == self.desired_value


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

        self.ButtonsList = [
            ButtonSpeed(
                self.x + index * (self.spacing + self.width_single),
                self.y, self.width_single, self.height,
                self.font_size, value
            )
            for index, value in enumerate(self.speed_list)
        ]

    def click(self, mouse):
        for button in self.ButtonsList:
            button.click(mouse)

    def draw(self, mouse):
        for button in self.ButtonsList:
            button.draw(mouse)

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
            ErrorScreen("Error while reading game data")

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
            ErrorScreen("Error while writing game data")

    def dump_data(self):
        return base64_encode(json.dumps(self.datadict, separators=(",", ":")))


def check_directories():
    """Check if game directories exists, if not - create them."""
    for dir_path in (conf.path_gameDir, conf.path_logDir):
        if not dir_path.exists():
            dir_path.mkdir()


def rotate_log_files(log_paths):
    if log_paths[-1].exists():
        log_paths[-1].unlink()

    for log1_path, log2_path in zip(log_paths[-2::-1], log_paths[-1:0:-1]):
        if log1_path.exists():
            log1_path.replace(log2_path)


def configure_logging():
    log_paths = [conf.path_logDir / f"{i}.log" for i in range(1, conf.n_logs + 1)]
    rotate_log_files(log_paths)

    for handler in logging.root.handlers[:]:  # this is needed in PyCharm and can be left for safety
        logging.root.removeHandler(handler)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    sys.stderr = Tee(sys.stderr, log_paths[0], "a")
    formatter_file = logging.Formatter("%(asctime)s [%(levelname)s] (Line %(lineno)d in %(funcName)s) - %(message)s")
    file_handler = logging.FileHandler(filename=log_paths[0], mode="a")
    file_handler.setFormatter(formatter_file)
    logger.addHandler(file_handler)

    formatter_stdout = logging.Formatter("[%(levelname)s] %(message)s")
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter_stdout)
    stdout_handler.setLevel(logging.INFO)
    logger.addHandler(stdout_handler)

    return logger


def check_assets():
    if not conf.path_assetsDir.exists():
        logger.error(f"Game assets directory not found ({conf.path_assetsDir})")
        sys.exit(1)

    for file_path in (conf.path_font, conf.path_music_Game, conf.path_music_GameOver, conf.path_icon):
        if not file_path.is_good():
            logger.error(f'Asset "{file_path.name}" not found ({file_path})')
            sys.exit(1)


def check_data_files():
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


class SnakeClass:
    def __init__(self):
        self.velocity = conf.grid
        self.color_head = (255, 255, 255)
        self.colors_tail = [(3, 255, 3), (2, 232, 2), (1, 187, 0)]
        self.colors_tail_len = len(self.colors_tail)
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

    def move(self) -> bool:
        """Move the snake. If the return value is True, game is over."""
        game_over = False
        self.dirx_current = self.dirx
        self.diry_current = self.diry

        if self.dirx != 0:
            self.x += self.dirx
        elif self.diry != 0:
            self.y += self.diry
        self.head_location = (self.x + conf.grid_border, self.y + conf.grid_border)

        if self.x == conf.game_x - conf.grid or self.x == conf.game_width + conf.grid or self.y == conf.game_y - conf.grid or self.y == conf.game_height + conf.topbar_height:
            game_over = True

        for pair in self.xyList[:-1]:  # collision with itself
            if self.head_location == pair:
                game_over = True

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
                game_over = True
            Banana.move()

        return game_over

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
        Time = Text(f"time: {format_time(Snake.fpsCounter // conf.fps)}", conf.color_text, self.font_size)
        Time.draw(int(1.4 * conf.grid), (self.height - Time.height) // 2)

        Score = Text(f"score: {thousands_separators(Snake.score)}", conf.color_text, self.font_size)
        Score.draw((self.width - Score.width) // 2, (self.height - Score.height) // 2)

        HighscoreOnBar = Text(f"highscore: {thousands_separators(Data.highscores_speed[str(conf.speed)])}", conf.color_text, self.font_size)
        HighscoreOnBar.draw(self.width - int(1.4 * conf.grid) - HighscoreOnBar.width, (self.height - HighscoreOnBar.height) // 2)


class CurrentSpeedTextClass:
    def __init__(self):
        self.update()
        self.x = int(1.4 * conf.grid)
        self.y = 25 * conf.grid + (conf.grid - self.text.height) // 2

    def update(self):
        self.text = Text(f"speed: {conf.speed}", conf.color_text, conf.font_size_currentspeed)

    def draw(self):
        self.text.draw(self.x, self.y)


class HighscoresInMenuClass:
    def __init__(self):
        self.x1 = conf.margin
        self.x2 = conf.margin + 15
        self.y1 = conf.margin - 4
        self.color = conf.color_text
        self.font_size1 = 23
        self.font_size2 = 21
        self.update()
        self.y_bottom = self.y2 + self.text2.height

    def update(self):
        self.text1 = Text("Highscores:", self.color, self.font_size1)
        self.text2 = LongText(
            f"• overall: {Data.highscore} \n "
            + " \n ".join([
                f"• {speed}: {score}"
                for speed, score
                in Data.highscores_speed.items()
            ]),
            self.color,
            self.font_size2
        )
        self.y2 = conf.margin + self.text1.height

    def draw(self):
        self.text1.draw(self.x1, self.y1)
        self.text2.draw(self.x2, self.y2)


class TotalStatsInMenuClass:
    def __init__(self):
        self.x = conf.margin
        self.y1 = HighscoresInMenu.y_bottom + 7
        self.color = conf.color_text
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
        self.text = Text(f"Volume: {Data.volume:.0%}", conf.color_text, self.font_size)
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

    def draw(self, mouse):
        self.button_minus.draw(mouse)
        self.button_plus.draw(mouse)
        self.text.draw(self.x_text, self.y_text)


########### Scenes managing ###########

def menu_main():
    global LastScore

    LastScore = None
    while True:
        clock.tick(conf.fps)

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ButtonPlay.is_pointed(mouse):
                    game_main()
                elif ButtonExit.is_pointed(mouse):
                    return
                elif AboutButton.is_pointed(mouse):
                    AboutScreen()
                WebsiteButton.click(mouse)
                SpeedButtons.click(mouse)
                VolumeWidgetInMenu.button_minus.click(mouse)
                VolumeWidgetInMenu.button_plus.click(mouse)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return
        if keys[pygame.K_SPACE]:
            game_main()

        if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            SpeedButtons.await_decrease()
        elif (keys[pygame.K_EQUALS] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])) or keys[pygame.K_KP_PLUS]:
            SpeedButtons.await_increase()
        else:
            SpeedButtons.change_speed()

        menu_redraw(mouse)


def menu_redraw(mouse):
    global LastScore
    window.fill(conf.color_window_background)
    SnakeLogo.draw((conf.window_width - SnakeLogo.width) // 2, 113)
    HighscoresInMenu.draw()
    TotalStatsInMenu.draw()
    if LastScore:
        LastScore.draw((conf.window_width - LastScore.width) // 2, 205)
    ButtonPlay.draw(mouse)
    ButtonExit.draw(mouse)
    VersionNumberInMenu.draw(
        conf.window_width - conf.margin - VersionNumberInMenu.width,
        conf.window_height - conf.margin - VersionNumberInMenu.height
    )
    WebsiteButton.draw(mouse)
    AboutButton.draw(mouse)
    SpeedText.draw(
        conf.window_width - conf.margin - SpeedButtons.width_total - SpeedButtons.spacing - SpeedText.width,
        conf.margin + (SpeedButtons.height - SpeedText.height) // 2
    )
    SpeedButtons.draw(mouse)
    VolumeWidgetInMenu.draw(mouse)

    pygame.display.update()


def game_main():
    global Snake
    global Apple
    global Banana
    pygame.mixer.music.load(conf.path_music_Game)
    pygame.mixer.music.play(loops=-1)
    Snake = SnakeClass()
    Apple = AppleClass()
    Banana = BananaClass()
    Apple.move()
    Banana.move()

    game_main_loop()

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
        NewHighscoreText.draw(
            (conf.window_width - NewHighscoreText.width) // 2,
            (conf.window_height - GameOver.height) // 2 - GameOver.height + NewHighscoreText.height - 10
        )
        HighscoresInMenu.update()
    elif Snake.score > Data.highscore:
        logger.info(f"Highscore beaten, old: {Data.highscore}, new: {Snake.score} (speed {conf.speed})")
        Data.highscore = Snake.score
        NewHighscoreText = Text(f"new highscore: {Snake.score}", conf.color_newhighscore, conf.font_size_newhighscore)
        NewHighscoreText.draw(
            (conf.window_width - NewHighscoreText.width) // 2,
            (conf.window_height - GameOver.height) // 2 - GameOver.height + NewHighscoreText.height - 10
        )
        HighscoresInMenu.update()
    Data.write()

    global LastScore
    LastScore = Text(f"last score: {Snake.score}", conf.color_text, conf.font_size_lastscore)

    gameover_main()


def game_main_loop():
    while True:
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
                return
            elif joystick and event.type == pygame.JOYAXISMOTION:
                if joystick.get_axis(3) < -conf.joystick_sensitivity:    # ← -x
                    Snake.change_dir_left()
                elif joystick.get_axis(3) > conf.joystick_sensitivity:   # → +x
                    Snake.change_dir_right()
                elif joystick.get_axis(4) < -conf.joystick_sensitivity:  # ↑ -y
                    Snake.change_dir_up()
                elif joystick.get_axis(4) > conf.joystick_sensitivity:   # ↓ +y
                    Snake.change_dir_down()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:     # ← -x
            Snake.change_dir_left()
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:  # → +x
            Snake.change_dir_right()
        elif keys[pygame.K_UP] or keys[pygame.K_w]:     # ↑ -y
            Snake.change_dir_up()
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:   # ↓ +y
            Snake.change_dir_down()

        if Snake.fpsCounter % conf.move_delay == 0:
            game_over = Snake.move()
            if game_over:
                return


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


class AboutScreen():
    def __init__(self):
        self.Text = LongText(
            (
                "Credits: \n "
                "- Icon: \n "
                "\t Icon made by Freepik from www.flaticon.com \n "
                "\n "
                "- Music during gameplay: \n "
                "\t Tristan Lohengrin - Happy 8bit Loop 01 \n "
                "\n "
                "- Sound after loss: \n "
                "\t Sad Trombone Wah Wah Wah Fail Sound Effect \n "
                "\n "
                "© 2023 Michał Machnikowski \n "
                "License: GNU General Public License version 3 (https://www.gnu.org/licenses/gpl-3.0.html)"
            ),
            conf.color_text,
            font_size=24,
            line_length=52
        )
        self.BackButton = Button((conf.window_width - conf.button_width) // 2, 540, 200, 70, "Back", 30)

        self.main_loop()

    def main_loop(self):
        while True:
            clock.tick(conf.fps)
    
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.BackButton.is_pointed(mouse):  # Back to menu
                        return
    
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                sys.exit()
    
            self.redraw(mouse)

    def redraw(self, mouse):
        window.fill(conf.color_window_background)
        self.Text.draw((conf.window_width - self.Text.width) // 2, 55)
        self.BackButton.draw(mouse)
        pygame.display.update()


class LoadingScreen:
    def __init__(self, function: Callable, error_text: str, loading_text: str = "Loading", font_size: int = 35):
        self.error_text = error_text
        self.time = 0
        self.thread = MyThread(target=function, daemon=True)
        self.LoadingTexts = (
            Text(loading_text, conf.color_text, font_size),
            Text(f"{loading_text}.", conf.color_text, font_size),
            Text(f"{loading_text}..", conf.color_text, font_size),
            Text(f"{loading_text}...", conf.color_text, font_size)
        )

        self.main_loop()

    def main_loop(self):
        self.thread.start()
        while self.thread.is_alive():
            clock.tick(conf.fps)
            self.redraw()
            self.time += 1

        if self.thread.error:
            logger.error(self.thread.error)
            logger.error(self.thread.traceback)
            ErrorScreen(self.error_text)

    def redraw(self):
        window.fill(conf.color_window_background)
        Loading = self.LoadingTexts[self.time // conf.fps % 4]
        Loading.draw((conf.window_width - Loading.width) // 2, (conf.window_height - Loading.height) // 2)
        pygame.display.update()


class ErrorScreen:
    color_background = (208, 26, 26)
    font_size = 30
    def __init__(self, message: str):
        self.message = message
        logger.critical(f"Error screen: {message}")

        self.ErrorText = LongText(message, conf.color_text, self.font_size)
        self.text_x = (conf.window_width - self.ErrorText.width) // 2
        self.text_y = (conf.window_height - self.ErrorText.height) // 2 - 60
        self.ButtonExitError = Button(
            (conf.window_width - conf.button_width) // 2,
            500,
            conf.button_width,
            conf.button_height,
            "Exit",
            conf.button_font_size,
            command=lambda: sys.exit(1)
        )

        self.main_loop()
    
    def main_loop(self):
        while True:
            clock.tick(conf.fps)
    
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit(1)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.ButtonExitError.click(mouse)
    
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                sys.exit(1)

            self.redraw(mouse)
    
    def redraw(self, mouse):
        window.fill(self.color_background)
        self.ErrorText.draw(self.text_x, self.text_y)
        self.ButtonExitError.draw(mouse)
        pygame.display.update()


####### Settings / Config #######

class conf:
    version = "2.0.0-dev"
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
    color_game_background = (0, 0, 0)
    color_text = (255, 255, 255)
    color_newhighscore = (0, 0, 255)

    font_size_newhighscore = 33
    font_size_lastscore = 27
    font_size_website = 21
    font_size_currentspeed = 17

    button_width = grid * 10
    button_height = grid * 4
    button_font_size = 35

    if os.name == "nt":
        path_gameDir = MyPath.home() / "AppData" / "Roaming" / ".snake"  # ~\AppData\Roaming\.snake\
    else:
        path_gameDir = MyPath.home() / ".snake"  # ~/.snake/
    path_data = path_gameDir / "data"  # ~/.snake/data
    path_data_backup = path_gameDir / "data.backup"  # ~/.snake/data.backup
    path_version = path_gameDir / "version"  # ~/.snake/version
    path_assetsDir = MyPath(__file__).resolve().parent / "assets"  # assets/
    path_font = path_assetsDir / "OpenSans-Bold.ttf"
    path_music_Game = path_assetsDir / "Tristan Lohengrin - Happy 8bit Loop 01.ogg"
    path_music_GameOver = path_assetsDir / "Sad Trombone Wah Wah Wah Fail Sound Effect.ogg"
    path_icon = path_assetsDir / "icon_48px.png"
    path_logDir = path_gameDir / "logs"  # ~/.snake/logs/
    n_logs = 4

    url_website = "http://tiny.cc/snake_website"

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
    check_directories()

    logger = configure_logging()
    logger.info(f"Starting Snake v{conf.version}")
    logger.info(f"System: {platform.system()}, version: {platform.release()}")

    check_assets()
    check_data_files()
    logger.info("Checking files done")

    pygame.display.init()
    pygame.mixer.init()
    pygame.font.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() else None
    clock = pygame.time.Clock()
    window = pygame.display.set_mode((conf.window_width, conf.window_height), vsync=1)
    pygame.display.set_caption(f"Snake v{conf.version}")
    pygame.display.set_icon(pygame.image.load(conf.path_icon))

    Data = File()
    Data.read()

    # Prerendered objects
    GameOver = Text("GAME  OVER", (255, 0, 0), 77)
    SnakeLogo = Text("Snake Game", (255, 255, 255), 62)
    VersionNumberInMenu = Text(f"v{conf.version}", (215, 215, 215), 19)

    ButtonPlay = Button((conf.window_width - conf.button_width) // 2, 275, conf.button_width, conf.button_height, "Play", conf.button_font_size)
    ButtonExit = Button((conf.window_width - conf.button_width) // 2, 420, conf.button_width, conf.button_height, "Exit", conf.button_font_size)
    WebsiteButton = Button(
        conf.margin,
        conf.window_height - conf.margin - 2 * conf.grid,
        int(4.85 * conf.grid),
        2 * conf.grid, "website",
        conf.font_size_website,
        command=lambda: webbrowser.open(conf.url_website, new=0, autoraise=True),
        radius=7
    )
    AboutButton = Button(
        conf.margin + int(5.5 * conf.grid),
        conf.window_height - conf.margin - 2 * conf.grid,
        int(4.65 * conf.grid),
        2 * conf.grid,
        "about",
        conf.font_size_website,
        radius=7
    )

    SpeedText = Text("Speed:", conf.color_text, 22)
    SpeedButtons = ButtonSpeedGroup()
    HighscoresInMenu = HighscoresInMenuClass()
    TotalStatsInMenu = TotalStatsInMenuClass()
    VolumeWidgetInMenu = VolumeWidgetInMenuClass()

    TopBar = TopBarClass()
    CurrentSpeedText = CurrentSpeedTextClass()

    menu_main()

    logger.info("Quitting")
    logger.debug(Data.dump_data())

    pygame.quit()

