# Uma Launcher
Script that enhances the Uma Musume (DMM Version) experience.

## Requirements (Optional)
- [EXNOA-CarrotJuicer](https://github.com/CNA-Bld/EXNOA-CarrotJuicer)
  - Make sure CarrotJuicer's `version.dll` is located in the same directory as `umamusume.exe`.
  - While optional, CarrotJuicer allows UmaLauncher to extract information from the network packets the game sends/receives. This information is necessary to determine the current status of the game for the automatic training event helper and Discord rich presence.

## Usage
Download the latest release's `UmaLauncher.exe` and run it.

(When downloading a newer version, you may overwrite the existing .exe)

On first launch or when you change the game's location, you may be asked to select the installation location for the game if you are not using the default location.

## Features
### Launch Uma Musume simply by running one file
- The program automatically launches the game through DMM and closes it without needing any extra interaction.
  - Exceptions are logging into DMM and confirming game updates. (Updates might be automated in the future.)
- The script will ask for administrator privileges to interact with the Uma Musume window.
### Better Discord rich presence for Uma Musume
![An example of the training rich presence.](assets/rich-presence.png)
- Shows which home screen you're on.
- Shows training and concert details extracted from the game's packets. **(CarrotJuicer required)**
- (Still work-in-progress and only works if nothing is above the game window.)
### Automatic GameTora training event helper
**(CarrotJuicer required)**

![An example of the automatic training event helper scrolling to the training event.](assets/event-helper.gif)
- Automatically start a browser window with the current trained character and support cards.
- Automatically selects and scrolls to event choices when needed.
### Quality-of-life features
![An image showing the different settings in the tray icon.](assets/tray-icon.png)
- Various options to enable/disable during gameplay by right-clicking the horse shoe icon in the system tray/taskbar:
  - Locking and remembering the game window position for portrait and landscape mode separately.
    - This also includes the automatic training event helper.
  - Automatically resizing the game to the largest possible size on your screen.
  - Take screenshots.
  - Change the browser that opens with the automatic training event helper.

## Disclaimer
UmaLauncher is in no way associated with Uma Musume, Cygames or DMM.  
It is the developer's belief that this tool is harmless to the above companies and brands and merely acts as a tool to improve the user experience.  

## License
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)  
This code is available under the GNU GPLv3 license.