# Changelog

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
