# Uma Launcher
Script that enhances the Uma Musume (DMM Version) experience.

## Requirements
- [EXNOA-CarrotJuicer](https://github.com/CNA-Bld/EXNOA-CarrotJuicer)
  - Make sure CarrotJuicer's `version.dll` is located in the same directory as `umamusume.exe`.
  - CarrotJuicer allows UmaLauncher to extract information from the network packets the game sends/receives. This information is used to determine the current status of the game for Discord rich presence.
- [Python 3](https://www.python.org/downloads/)
  - Make sure to run `pip install -r requirements.txt` where you unpacked UmaLauncher before running UmaLauncher.
- [Node.js](https://nodejs.org/)
  - Make sure to run `npm install` where you unpacked UmaLauncher before running UmaLauncher.
- [Firefox](https://www.mozilla.org/)
  - A version of Firefox needs to be installed for the automatic GameTora event helper.

## Installation
Move instructions from requirements here.

## Usage
Extract the latest release's source code .zip anywhere and run `UmaLauncher.lnk`. Change settings or close by right-clicking the horse shoe tray icon on the taskbar.
On first launch, you may be asked to select the installation locations for the game and DMM if you are not using the default locations.

## Features
- Launch Uma Musume simply by running one file.
  - `UmaLauncher.pyw` automatically launches DMMGamePlayer and autostarts the game. No interaction necessary.
    - Alternatively, run `threader.py` to keep the console open.
    - Whichever way you run the script, output will be logged to `log.log`.
    - The script will ask for administrator privileges to interact the DMMGamePlayer and Uma Musume windows and to patch DMMGamePlayer.
- Better Discord rich presence for Uma Musume. (WIP)
    - (Still work-in-progress and only works if nothing is above the game window.)
    - Shows which home screen you're on.
    - Shows training details extracted from the game's packets through CarrotJuicer.
- Automation of GameTora's training event helper.
  - Automatically start a browser window with the current trained character and support cards.
  - Automatically selects and scrolls to event choices when needed.
- Various options to enable/disable during gameplay by right-clicking the horse shoe icon in the taskbar:
  - Locking and remembering the game window position for portrait and landscape mode separately.
  - Automatically resizing the game to the largest possible size on your screen.
  - Take screenshots.
- Or manually change settings after first launch by editing `umasettings.json`.

## Disclaimer
UmaLauncher is in no way associated with Uma Musume, Cygames or DMM.  
It is the developer's belief that this tool is harmless to the above companies and brands and merely acts as a tool to improve the user experience.  
That being said; **UmaLauncher modifies files of DMMGamePlayer and does not fall under its TOS, so use at your own risk!**

## License
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)  
This code is available under the GNU GPLv3 license.