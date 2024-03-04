# Frequently Asked Questions

Here's a list of things you may want to know about Uma Launcher. If you have a question that is not answered here, feel free to ask in the [Discord server](https://discord.gg/wvGHW65C6A). (Head to the `#help-needed` channel.)

<details>
<summary><b>How to set up automatic VPN</b></summary>

**This feature is experimental. Please report any bugs you may encounter.**
The feature is disabled by default. Please read the usage guide below on how to correctly set it up:

## Usage guide:
Currently only **OpenVPN Community**, **SoftEther** and **NordVPN** are supported.
For OpenVPN and SoftEther, a server will be chosen from [https://umapyoi.net](https://umapyoi.net/docs/vpn.html).
### Step 1
Start Uma Launcher, right-click the horseshoe icon in the taskbar tray and click on `Preferences`.
### Step 2
Scroll down the General settings until you reach `Auto-VPN enabled`. Tick the setting to enable auto-VPN. (This will apply when you restart Uma Launcher.)
You can leave `VPN for DMM only` checked if you want the VPN to disconnect when the game starts. Uncheck if you want the VPN to stay enabled as long as Uma Launcher is running.
### Step 3
Choose which VPN client you want to use in the `VPN client` setting. Depending on your choice, you might need to do something more:

**OpenVPN**
Place the path to `openvpn.exe` in the `VPN client path` text field. You can click on the `Browse` button to open a file browser to select it. First go to where you installed OpenVPN (likely in some Program Files folder) and go inside the `bin` folder. Then choose `openvpn.exe`.
You may use the next setting `VPN override` to specify a path to a custom ovpn profile to use. (No browse button.)

**SoftEther**
Nothing special to configure. Just make sure the setting `VPN override` is empty or input a custom server IP.

**NordVPN**
Place the path to `NordVPN.exe` in the `VPN client path` text field. You can click on the `Browse` button to open a file browser to select it. First go to where you installed NordVPN (likely in some Program Files folder) and choose `NordVPN.exe`.
### Step 4
Click `Save & close` at the bottom of the settings window and right-click the horseshoe icon in the taskbar tray and choose `Close`. Close DMM if needed. Now run Uma Launcher again and use Uma Launcher like normal. (Depending on your location, the connection may not be very fast.)

Keep in mind that this feature is experimental, so be sure to let me know if anything does not work on your machine.
</details>

<details>
<summary><b>CarrotJuicer issues / The automatic training event helper window does not show up when a training run is started/continued.</b></summary>

This feature requires you install the CarrotJuicer mod for Uma Musume. Please carefully read <a href="https://umapyoi.net/uma-launcher" target="_blank">the instructions</a> on how to install it. (See bottom of the instructions section on how to use if you already use Trainers' Legend G or Noccu's English Patch.)<br>
If you installed CarrotJuicer according to the instructions but nothing happens when you start/enter a training run, try the following:

* Check if a folder called `CarrotJuicer` was created in the same folder as the game's executable `umamusume.exe`. Start the game once without Uma Launcher. You should see a command prompt when the game starts, and it should stay open. Do something in the game that requires a server connection (when it says `Connecing...` in the top-right of the game.) There should now be a few `.msgpack` files in the `CarrotJuicer` folder, assuming you did not have Uma Launcher running. If any of these things did not happen, CarrotJuicer is not installed/working correctly. Make sure it is installed in the correct folder. Check where you installed the game. Instructions are below.
* If you are sure you placed `version.dll` in the right place, but no `CarrotJuicer` folder is created when starting the game, try renaming the dll to `umpdc.dll`. Sometimes this fixes the issue. (Unsure why.)
* Make sure CarrotJuicer functionality is enabled in the preferences of Uma Launcher.
  * Right-click the horseshoe icon in the taskbar tray and click on `Preferences`. Make sure `Enable CarrotJuicer` is checked.
* Make sure Uma Launcher uses the correct game folder when it looks for CarrotJuicer's output.
  * Right-click the horseshoe icon in the taskbar tray and click on `Preferences`. Make sure `Game install path` is set to the folder where you installed Uma Musume.
  * If you ever had Uma Musume installed in its default location, but have since installed it elsewhere, make sure you confirm where the game is installed directly in DMMGamePlayer.
    * Open DMMGamePlayer, open the "My Games" (マイゲーム) page.
    * Hover over the Uma Musume game image and click the information icon 🛈
    * Click on the link in the bottom-right of the popup that says `ダウンロード先フォルダを表示` and has a folder icon next to it.
    * This will open a file browser and highlight the folder that the game is installed in (it has `umamusume.exe` inside it). Set that folder in Uma Launcher's preferences.

Make sure to **restart Uma Launcher** after doing any of the above. (Right-click the horseshoe icon in the taskbar tray and click on `Close`.)<br>
If the helper window still does not show up, please ask for help in the Discord server (see top of the page.)
</details>


<details>
<summary><b>Other browser-related issues</b></summary>

If you get error messages related to the web browser, try switching to Firefox in the preferences. Chromium-based browsers (Chrome, Edge) are inconsistent and a pain to work with. Firefox is the most stable browser to use with Uma Launcher.<br>
You may still report issues you have with Chromium-based browsers.
</details>

<details>
<summary><b>I can't move my game window!</b></summary>

Right-click the horseshoe icon and uncheck `Lock game window`. You should now be able to move the game window.<br>
When you are done moving the window, re-enable `Lock game window` and it will remember the position of the game window.<br>
You will need to do this again when the game switches into landscape mode.

</details>

<details>
<summary><b>DMMGamePlayer opens but the game never starts!</b></summary>

This happens if there is an update available for Uma Musume. You will need to update the game manually.<br>
Move to the "My Games" (マイゲーム) page and click the orange button when you hover over the Uma Musume game image.<br>
The way DMM works makes it impossible to automate this process. (In an old version of DMM, it would properly show the update popup, but that is no longer the case.)<br>
If you want to know when there is an update available, you can follow either Umapyoi.net's Twitter account, or the official Japanese Uma Musume Twitter account.

</details>

<details>
<summary><b>What OS does Uma Launcher support?</b></summary>

Uma Launcher is only built for and tested on Windows 10. It should work with Windows 11 as well.<br>
If you are trying to use Uma Launcher on Linux or Mac, figure it out yourself since you managed to get Uma Musume running on it. ;)
</details>

<details>
<summary><b>Streaming the game on Discord displays a frozen image?</b></summary>

This appears to be a bug with Discord and it's unrelated to Uma Launcher. I've found this happens when the game's window is close to the taskbar.<br>
* Right-click the horseshoe icon and choose `Preferences`.
* Move to the `Position` tab.
* Scroll down to the safezone offsets.
* Add at least 8 offset to whatever side your taskbar is at.
* Click `Save and close`.
* Right-click the horseshoe icon and choose `Maximize + center game`.
</details>
