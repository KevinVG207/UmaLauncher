# Frequently Asked Questions

Here's a list of things you may want to know about Uma Launcher. If you have a question that is not answered here, feel free to ask in the [Discord server](https://discord.gg/wvGHW65C6A). (Head to the `#help-needed` channel.)

<details>
<summary><b>How to set up automatic VPN</b></summary>

**This feature is experimental. Please report any bugs you may encounter.**
The feature is disabled by default. Please read the usage guide below on how to correctly set it up:

## Usage guide:
Currently only **OpenVPN Community**, **SoftEther** and **NordVPN** are supported.
For OpenVPN and SoftEther, a server will be chosen from [https://nasu-ser.me/vpn/](https://nasu-ser.me/vpn/).
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
<summary><b>Browser-related issues<b></summary>

If you get error messages related to the web browser, try switching to Firefox in the preferences. Chromium-based browsers (Chrome, Edge) are inconsistent and a pain to work with. Firefox is the most stable browser to use with Uma Launcher.<br>
You may still report issues you have with Chromium-based browsers.
</details>

<details>
<summary><b>What OS does Uma Launcher support?</b></summary>

Uma Launcher is only built for and tested on Windows 10. It should work with Windows 11 as well.<br>
If you are trying to use Uma Launcher on Linux or Mac, figure it out yourself since you managed to get Uma Musume running on it. ;)
</details>