import os

from mypath import MyPath


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

joystick_sensitivity = 0.91

