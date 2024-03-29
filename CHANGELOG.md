# Changelog

## Release 1.6.0 (2023-02-25)
* Added bananas, eating of which removes one point
* Volume can be changed
* Buttons can now only be clicked with left mouse button
* Other improvements

## Release 1.5.0 (2022-04-23)
* Snake segments and apple have rounded corners
* Count score from 0
* Back up game data
* Render the game at 120 FPS for smoother gameplay
* Other improvements

## Release 1.4.0 (2022-04-03)
* Tail segments have different colors
* Basic gamepad support - moving with joystick (tested on Xbox One S Controller)
* Change speed using +/- keys in menu
* Optimizations, code cleanup
* Show stderr in terminal

## Release 1.3.1 (2022-03-31)
* Fixed walrus operator for Python 3.8 and 3.9
* Start counting time only after first move
* Count total time more precisely

## Release 1.3 (2022-03-25)
* Separate highscores for different speeds
* Count and show number of games played and time spent
* Host assets on Discord, because sometimes files downloaded from GDrive were empty
* Added GNU GPLv3 license

## Release 1.2 (2022-03-19)
* Use `pathlib` to work with paths
* Show current speed during game
* Updated preset speeds
* Code improvements
* Show last score in menu
* Buttons have rounded corners
* Renamed the "music" directory to "assets"
* Use Open Sans font
* Press spacebar in menu to start game
* Press spacebar or escape to skip game over

## Release 1.1 (2021-04-09)
* Added an icon (it is Base64 encoded in the code, instead of downloading it)
* Changed the way the button commands are executed
* Got rid of the `two_digits()` function (use f-strings formatting `:02`)
* Added support for forcing a new line by `\n` in LongText
* Credits scene
* Buttons in the menu changing snake speed
* Save the set speed to the game data
* Changed default speed from 3 to 4

## Release 1.0 (2021-03-21)
* Changed from processes to threads (processes do not want to work on Windows, and threads are enough here)
* Play music via pygame
* Changed music files from mp3 to ogg (because pygame does not work with mp3)
* Improved rendering of the game over text
* Use f-strings
* Changed `logger.exception()` to a probably better way of logging an error
* Corrected drawing text on the button - if the button size was different than the default, the text was not centered
* Added a button to the website ;)

## Release 0.7 (2021-03-20)
* Better traceback logging (by redirecting stderr to a file)
* Added a file storing the game version (may be helpful if I change the game file structure in the future)
* Show best score in menu
* Added operating system info to logs
* The game directory on Windows is now in AppData
* Changed from `os.rename()` to `os.replace()`, as the first one does not work on Windows

## Release 0.6 (2021-02-25)
* Added program logging
* Put download into try/except block
* Added an error screen in case of an error (e.g. during downloading)
* Renamed game data file (from `.snake_data` to `data`)
* Use `os.path.join()` to create paths instead of string concatenation
* Re-written reading and writing of game data - now data is saved as JSON encoded in Base64
* Added easy rendering of long, multi-line text

## Release 0.5 (2021-01-15)
* Added in-game music (running in a separate process) and sound at loss
* Expanded the game directory and creating it if it doesn't exist
* Loading screen and downloading music from Google Drive in a separate process if not yet downloaded

## Release 0.4 (2021-01-13)
* Added menu
* Added Game Over text and a message if the record was beaten
* Changed data storage path to `~/.snake_data` (this is cross-platform)
* Minor code improvements

## Release 0.3 (????-??-??)
* Added game window border and top bar displaying game time, current score and high score
* Score calculated as snake length
* Store the best score in a text file

## Release 0.2 (????-??-??)
* Added gaps between tiles

## Release 0.1 (????-??-??)
* Basic functionality
