# Uma Launcher

## Requirements
- Python 3
  - Make sure to run `pip install -r requirements.txt` before first launch.
- Node.js
  - Make sure to run `npm install` before first launch.

## Features
- Launch Uma Musume simply by running one Python script.
  - `umalauncher.pyw` automatically launches DMMGamePlayer and autostarts the game. No interaction necessary.
    - Alternatively, run `umalauncher.py` to keep the console open.
    - Whichever way you run the script, output will be logged to `log.log`.
    - The script will ask for administrator privileges to interact the DMMGamePlayer and Uma Musume windows and to patch DMMGamePlayer.
- Various options to enable/disable during gameplay by right-clicking the horse shoe icon in the taskbar:
  - Better Discord rich presence for Uma Musume.
  - Automatically resizing the game to the largest possible size on your screen.
  - Take screenshots.
- Or manually change settings after first launch by editing `umasettings.json`.
  - E.g. to change the path to DMMGamePlayer to a non-default location.

## Disclaimer
UmaLauncher is in no way associated with Uma Musume, Cygames or DMM.  
It is the developer's belief that this tool is harmless to the above companies and brands and merely acts as a tool to improve the user experience.  
That being said; **UmaLauncher modifies files of DMMGamePlayer and does not fall under its TOS, so use at your own risk!**

## License
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)  
This code is available under the GNU GPLv3 license.