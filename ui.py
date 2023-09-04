from collections.abc import Callable

import pygame

import config


class Text:
    def __init__(self, surface: pygame.Surface, text: str, color, font_size: int):
        self.surface = surface
        self.font = pygame.font.Font(config.path_font, font_size)
        self.text = self.font.render(text, True, color)
        self.width, self.height = self.text.get_size()

    def draw(self, x: int, y: int):
        self.surface.blit(self.text, (x, y))


class LongText:
    def __init__(self, surface: pygame.Surface, text: str, color, font_size: int, line_length: int = 40, line_spacing: int = 1):
        self.line_spacing = line_spacing
        lines = self.split_into_lines(text, line_length)
        self.renderedTextList = [Text(surface, line, color, font_size) for line in lines]
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
    def __init__(self, surface: pygame.Surface, width: int, height: int, radius: int, color):
        self.surface = surface
        self.width = width
        self.height = height
        self.radius = radius
        self.color = color

    def draw(self, x: int, y: int):
        pygame.draw.rect(self.surface, self.color, (x, y, self.width, self.height), border_radius=self.radius)


class Button:
    def __init__(self, surface: pygame.Surface, x: int, y: int, width: int, height: int, text: str, font_size: int, color1=(254, 151, 12), color2=(195, 122, 20), color_text=(255, 255, 255), command: Callable = lambda: None, radius: int = 9):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.background1 = RoundedRectangle(surface, width, height, radius, color1)
        self.background2 = RoundedRectangle(surface, width, height, radius, color2)
        self.text = Text(surface, text, color_text, font_size)
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


def draw_tile(surface: pygame.Surface, color, x: int, y: int):
    pygame.draw.rect(surface, color, (x, y, config.tile_width, config.tile_width), border_radius=config.tile_radius)

