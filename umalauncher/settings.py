import os
import json
import uuid
from win32com.shell import shell
import traceback
from loguru import logger
import util
import constants
import version
import gui
import settings_elements as se
import helper_table_defaults as htd
import helper_table_elements as hte


class DefaultSettings(se.Settings):
    def __init__(self):
        self.s_version = se.Setting(
            "Version",
            "(Private) Version of the settings file.",
            version.VERSION,
            se.SettingType.STRING,
            priority=-1
        )
        self.s_skip_update = se.Setting(
            "Skip update",
            "(Private) Version to skip updating to.",
            None,
            se.SettingType.STRING,
            priority=-1
        )
        self.s_unique_id = se.Setting(
            "Unique ID",
            "(Private) Unique ID for this installation.",
            str(uuid.uuid4()),
            se.SettingType.STRING,
            priority=-1
        )
        self.s_save_packets = se.Setting(
            "Save packets.",
            "Save incoming/outgoing packets to json. (For debugging purposes)",
            False,
            se.SettingType.BOOL,
            priority=-1
        )
        self.s_beta_optin = se.Setting(
            "Beta opt-in",
            "Opt-in to the beta version. (Pre-release versions)",
            False,
            se.SettingType.BOOL,
            priority=1
        )
        self.s_debug_mode = se.Setting(
            "Debug mode",
            "Enable debug mode. (Enables additional logging)",
            False,
            se.SettingType.BOOL,
            priority=0
        )
        self.s_autoclose_dmm = se.Setting(
            "Autoclose DMM Game Player",
            "Automatically close DMM Game Player when the game is launched.",
            True,
            se.SettingType.BOOL,
            priority=94
        )
        self.s_lock_game_window = se.Setting(
            "Lock game window",
            "Lock the game window to prevent accidental resizing.",
            True,
            se.SettingType.BOOL,
            priority=100,
            tab="Position"
        )
        self.s_discord_rich_presence = se.Setting(
            "Discord rich presence",
            "Display your current status in Discord.",
            True,
            se.SettingType.BOOL,
            priority=100
        )
        self.s_enable_carrotjuicer = se.Setting(
            "Enable CarrotJuicer",
            "Enable CarrotJuicer functionality.",
            True,
            se.SettingType.BOOL,
            priority=99
        )
        self.s_hide_carrotjuicer = se.Setting(
            "Hide CarrotJuicer console",
            "Hide the CarrotJuicer console window.",
            True,
            se.SettingType.BOOL,
            priority=99
        )
        self.s_track_trainings = se.Setting(
            "Track trainings",
            "Track training events in /training_logs as gzip files.",
            True,
            se.SettingType.BOOL,
            priority=95
        )
        # self.s_game_install_path = se.Setting(
        #     "Game install path",
        #     "Path to the game's installation folder. (Where DMM installed the game and umamusume.exe is located.)",
        #     "%userprofile%/Umamusume",
        #     se.SettingType.FOLDERDIALOG,
        #     priority=-1
        # )
        self.s_game_position_portrait = se.Setting(
            "Game position (portrait)",
            "Position of the game window in portrait mode.",
            None,
            se.SettingType.XYWHSPINBOXES,
            priority=-1
        )
        self.s_game_position_landscape = se.Setting(
            "Game position (landscape)",
            "Position of the game window in landscape mode.",
            None,
            se.SettingType.XYWHSPINBOXES,
            priority=-1
        )
        self.s_browser_position = se.Setting(
            "Browser position",
            "Position of the browser window.",
            None,
            se.SettingType.XYWHSPINBOXES,
            priority=70,
            tab="Position"
        )
        self.s_skills_position = se.Setting(
            "Skills browser position",
            "Position of the skills browser window.",
            None,
            se.SettingType.XYWHSPINBOXES,
            priority=60,
            tab="Position"
        )
        self.s_maximize_safezone = se.Setting(
            "Safezone for \"Maximize + center game\" in tray menu",
            "Amount of pixels to leave around the game window when maximizing.<br><b>If you are having issues streaming the game on Discord,</b> try adding a safezone of at least 8 pixels where your taskbar is.",
            None,
            se.SettingType.LRTBSPINBOXES,
            priority=50,
            tab="Position"
        )
        self.s_enable_browser = se.Setting(
            "Enable browser",
            "Enable the Automatic Training Event helper browser.",
            True,
            se.SettingType.BOOL,
            priority=100,
            tab="Event Helper"
        )
        self.s_selected_browser = se.Setting(
            "Browser type",
            "Browser to use for the Automatic Training Event Helper.",
            {
                "Auto": True,
                "Chrome": False,
                "Firefox": False,
                "Edge": False
            },
            se.SettingType.RADIOBUTTONS,
            priority=98,
            tab="Event Helper"
        )
        self.s_gametora_dark_mode = se.Setting(
            "GameTora dark mode",
            "Enable dark mode for GameTora.",
            True,
            se.SettingType.BOOL,
            priority=97,
            tab="Event Helper"
        )
        self.s_custom_browser_divider = se.Setting(
            "Custom browser divider",
            None,
            None,
            se.SettingType.DIVIDER,
            priority=96,
            tab="Event Helper"
        )
        self.s_custom_browser_message = se.Setting(
            "Custom browser",
            "<p>The following settings allow overriding of the browser binary and driver given to Selenium to control. You should only enable this if the browser fails to start, or you want to use a different Chromium-based browser.</p>",
            None,
            se.SettingType.MESSAGE,
            priority=96,
            tab="Event Helper"
        )
        self.s_enable_browser_override = se.Setting(
            "Enable browser override",
            "Enable overriding of the browser binary and driver. This also disables app mode for Chromium-based browsers, so you can reach settings in case things don't work.",
            False,
            se.SettingType.BOOL,
            priority=95,
            tab="Event Helper"
        )
        self.s_custom_browser_type = se.Setting(
            "Browser override type",
            "Browser to use for the Automatic Training Event Helper. If browser override is enabled, this <b>will</b> override the browser type setting above.",
            {
                "Firefox": True,
                "Other (Chromium)": False
            },
            se.SettingType.RADIOBUTTONS,
            priority=94,
            tab="Event Helper"
        )
        self.s_browser_custom_binary = se.Setting(
            "Browser custom binary",
            "Path to a custom browser executable.<br>Leave empty to let Selenium decide.",
            None,
            se.SettingType.FILEDIALOG,
            priority=93,
            tab="Event Helper"
        )
        self.s_browser_custom_driver = se.Setting(
            "Browser custom driver",
            "Path to a custom browser driver.<br>Leave empty to let Selenium decide.",
            None,
            se.SettingType.FILEDIALOG,
            priority=92,
            tab="Event Helper"
        )
        self.s_training_helper_table_preset = se.Setting(
            "Training helper table preset",
            "Preset to use for the Automatic Training Event Helper.",
            "Default",
            se.SettingType.STRING,
            priority=-1
        )
        self.s_training_helper_table_preset_list = se.Setting(
            "Training helper table preset list",
            "List of presets for the Automatic Training Event Helper.",
            [],
            se.SettingType.LIST,
            priority=-1
        )
        self.s_training_helper_table_scenario_presets_enabled = se.Setting(
            "Training helper table scenario presets enabled",
            "Enable scenario-specific presets for the Automatic Training Event Helper.",
            False,
            se.SettingType.BOOL,
            priority=-1
        )
        self.s_training_helper_table_scenario_presets = se.Setting(
            "Training helper table scenario presets",
            "Scenario-specific selected preset.",
            {str(key): "Default" for key in constants.SCENARIO_DICT},
            se.SettingType.DICT,
            priority=-1
        )
        self.s_vpn_message = se.Setting(
            "VPN Help",
            """<p>Automatic VPN is still experimental. Please report any issues you encounter.<br>For a guide on how to set up automatic VPN, see the guide on the <a href="https://github.com/KevinVG207/UmaLauncher/blob/main/FAQ.md">Frequently Asked Questions</a> page.</p>""",
            None,
            se.SettingType.MESSAGE,
            priority=100,
            tab="VPN"
        )
        self.s_vpn_enabled = se.Setting(
            "Auto-VPN enabled",
            "Connect to VPN when Uma Launcher is started.<br>For OpenVPN and SoftEther: A random JP server<br>will be chosen from VPN Gate to connect to.<br>NordVPN will connect to Japan.",
            False,
            se.SettingType.BOOL,
            priority=94,
            tab="VPN"
        )
        self.s_vpn_dmm_only = se.Setting(
            "VPN for DMM only",
            "Disconnect from VPN after DMM Game Player is closed.<br>If unchecked, VPN will stay connected until Uma Launcher is closed.",
            True,
            se.SettingType.BOOL,
            priority=93,
            tab="VPN"
        )
        self.s_vpn_client = se.Setting(
            "VPN client",
            "Choose VPN client to use.<br>Restart Uma Launcher after changing this setting.",
            {
                "OpenVPN": True,
                "SoftEther": False,
                "NordVPN": False
            },
            se.SettingType.RADIOBUTTONS,
            priority=92,
            tab="VPN"
        )
        self.s_vpn_client_path = se.Setting(
            "VPN client path (OpenVPN/NordVPN)",
            "Path to the VPN client executable (openvpn.exe or nordvpn.exe).<br>Not required for SoftEther.",
            None,
            se.SettingType.FILEDIALOG,
            priority=91,
            tab="VPN"
        )
        self.s_vpn_ip_override = se.Setting(
            "VPN override (OpenVPN/SoftEther)",
            "OpenVPN: Place a path to a custom ovpn profile.<br>SoftEther: Place an IP to override (no port, port is assumed to be 443.)",
            "",
            se.SettingType.STRING,
            priority=90,
            tab="VPN"
        )
        self.s_enable_english_patch = se.Setting(
            "Enable Carotene English patch on startup",
            "Applies the latest Carotene English patch before the game is launched.",
            False,
            se.SettingType.BOOL,
            priority=100,
            tab="English Patch"
        )
        self.s_english_patch_dll = se.Setting(
            "Mod DLL Name",
            "Change if you encounter issues.",
            {
                "version.dll": True,
                "umpdc.dll": False,
                "xinput1_3.dll": False
            },
            se.SettingType.RADIOBUTTONS,
            priority=90,
            tab="English Patch"
        )


class SettingsHandler():
    settings_file = "umasettings.json"
    loaded_settings = DefaultSettings()

    def __init__(self, threader):
        self.threader = threader

        # Load settings on import
        if not os.path.exists(util.get_relative(self.settings_file)):
            self.save_settings()

        self.load_settings(first_load=True)
        logger.info(self.loaded_settings)
    
    def regenerate_unique_id(self):
        self['s_unique_id'] = str(uuid.uuid4())

    def make_user_choose_folder(self, setting, file_to_verify, title, error):
        if not os.path.exists(os.path.join(self[setting], file_to_verify)):
            logger.debug(self[setting])
            pidl, _, _ = shell.SHBrowseForFolder(None, None, title)
            try:
                selected_directory = shell.SHGetPathFromIDListW(pidl)
            except:
                selected_directory = None

            if selected_directory and os.path.exists(os.path.join(selected_directory, file_to_verify)):
                self[setting] = selected_directory
            else:
                util.show_warning_box("Error", f"{error}<br>Uma Launcher will now close.")
                self.threader.stop()
    
    def save_settings(self):
        with open(util.get_relative(self.settings_file), "w", encoding="utf-8") as f:
            json.dump(self.loaded_settings.to_dict(), f, ensure_ascii=False, indent=4)
    
    def load_settings(self, first_load=False):
        raw_settings = ""
        with open(util.get_relative(self.settings_file), 'r', encoding='utf-8') as f:
            try:
                raw_settings = json.load(f)
            except (json.JSONDecodeError, TypeError) as _:
                logger.error(traceback.format_exc())
                util.show_warning_box("Error", "Failed to load settings file. Loading default settings instead.")
                self.loaded_settings = DefaultSettings()
                return
        self.loaded_settings.import_dict(raw_settings, keep_undefined=True)

        if first_load:
            success = version.auto_update(self)
            if not success:
                self.threader.stop()

        version.upgrade(self, raw_settings)

        if self['s_debug_mode']:
            util.is_debug = True
            util.log_set_trace()
            logger.debug("Debug mode enabled. Logging more.")
        else:
            util.is_debug = False
            util.log_set_info()
            logger.debug("Debug mode disabled. Logging less.")

        # # Check if the game install path is correct.
        # for folder_tuple in [
        #     ('s_game_install_path', "umamusume.exe", "Please choose the game's installation folder.\n(Where umamusume.exe is located.)", "Selected folder does not include umamusume.exe.\nPlease try again.")
        # ]:
        #     self.make_user_choose_folder(*folder_tuple)

        self.save_settings()

    def __contains__(self, key):
        return hasattr(self.loaded_settings, key)
    
    def __getitem__(self, key):
        value = getattr(self.loaded_settings, key).value
        if isinstance(value, str):
            value = os.path.expandvars(value)
        return value
    
    def __setitem__(self, key, value):
        logger.info(f"Setting {key} to {value}")
        getattr(self.loaded_settings, key).value = value
        self.save_settings()
    
    def __repr__(self):
        return repr(self.loaded_settings)
    

    def save_game_position(self, pos, portrait):
        if util.is_minimized(self.threader.screenstate.game_handle):
            # logger.warning(f"Game minimized, cannot save {constants.ORIENTATION_DICT[portrait]}: {pos}")
            return

        if (pos[0] == -32000 and pos[1] == -32000):
            # logger.warning(f"Game minimized, cannot save {constants.ORIENTATION_DICT[portrait]}: {pos}")
            return

        orientation_key = constants.ORIENTATION_DICT[portrait]
        self[orientation_key] = pos
        logger.info(f"Saving {orientation_key}: {pos}")
        self.save_settings()

    def load_game_position(self, portrait):
        orientation_key = constants.ORIENTATION_DICT[portrait]
        return self[orientation_key]

    def get_preset_list(self):
        preset_list = []
        for preset in self["s_training_helper_table_preset_list"]:
            preset_object = hte.Preset(htd.RowTypes)
            preset_object.import_dict(preset)
            preset_list.append(preset_object)
        return preset_list
    

    def get_preset_with_name(self, name):
        found_preset = None
        for preset in self.get_preset_list():
            if preset.name == name:
                found_preset = preset
                break
        
        if found_preset:
            return found_preset
        
        return htd.DefaultPreset(htd.RowTypes)


    def get_helper_table_data(self):
        preset_dict = {preset.name: preset for preset in self.get_preset_list()}
        selected_preset_name = self["s_training_helper_table_preset"]
        if selected_preset_name in preset_dict:
            selected_preset = preset_dict[selected_preset_name]
        else:
            selected_preset = htd.DefaultPreset(htd.RowTypes)
        return preset_dict, selected_preset

    def update_helper_table(self):
        logger.debug("Showing helper table preset menu.")
        preset_dict, selected_preset = self.get_helper_table_data()
        new_preset_list = []
        gui.show_widget(gui.UmaPresetMenu,
            selected_preset=selected_preset,
            default_preset=htd.DefaultPreset(htd.RowTypes),
            new_preset_class=hte.Preset,
            preset_list=list(preset_dict.values()),
            row_types_enum=htd.RowTypes,
            output_list=new_preset_list
        )
        if new_preset_list:
            logger.debug("Saving new helper table preset list.")
            selected_preset = new_preset_list.pop(0)
            self["s_training_helper_table_preset"] = selected_preset.name
            self["s_training_helper_table_preset_list"] = [preset.to_dict() for preset in new_preset_list]
            if self.threader.carrotjuicer.helper_table:
                self.threader.carrotjuicer.helper_table.update_presets(*self.get_helper_table_data())
            self.save_settings()

    def notify_server(self):
        version_str = version.VERSION
        if util.is_script:
            version_str += ".script"
        util.do_get_request(f"https://umapyoi.net/api/v1/umalauncher/startup/{self['s_unique_id']}/{version_str}")

    def display_preferences(self):
        general_var = [self.loaded_settings]
        
        preset_dict, selected_preset = self.get_helper_table_data()
        new_preset_list = []
        new_scenario_preset_dict = [self['s_training_helper_table_scenario_presets_enabled']]

        gui.show_widget(gui.UmaPreferences,
            umasettings=self,
            general_var=general_var,
            preset_dict=preset_dict,
            selected_preset=selected_preset,
            new_preset_list=new_preset_list,
            default_preset=htd.DefaultPreset(htd.RowTypes),
            new_preset_class=hte.Preset,
            new_scenario_preset_dict=new_scenario_preset_dict,
            row_types_enum=htd.RowTypes
        )

        # Update settings
        self.loaded_settings = general_var[0]

        if new_preset_list:
            logger.debug("Saving new helper table preset list.")
            selected_preset = new_preset_list.pop(0)
            self["s_training_helper_table_preset"] = selected_preset.name
            self["s_training_helper_table_preset_list"] = [preset.to_dict() for preset in new_preset_list]
        
        if len(new_scenario_preset_dict) > 1:
            logger.debug("Saving new helper table scenario preset list.")
            self["s_training_helper_table_scenario_presets_enabled"] = new_scenario_preset_dict[0]
            self["s_training_helper_table_scenario_presets"] = new_scenario_preset_dict[1]
        
        if self.threader.carrotjuicer.helper_table:
            self.threader.carrotjuicer.helper_table.update_presets(*self.get_helper_table_data())

        self.save_settings()
        self.load_settings()
        self.threader.tray.icon_thread.update_menu()
