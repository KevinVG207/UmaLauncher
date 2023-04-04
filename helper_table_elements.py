import enum
import os
import base64
from loguru import logger
import gui
import util

TABLE_HEADERS = [
    "Facility",
    "Speed",
    "Stamina",
    "Power",
    "Guts",
    "Wisdom"
]

class Colors(enum.Enum):
    """Defines the colors used in the helper table.
    """
    ALERT = "red"
    WARNING = "orange"
    GOOD = "lightgreen"

class SettingType(enum.Enum):
    BOOL = "bool"
    INT = "int"

class Settings():
    def get_settings_keys(self):
        return [attr for attr in dir(self) if attr.startswith("s_")]

    def to_dict(self):
        settings = self.get_settings_keys()
        return {setting: getattr(self, setting).value for setting in settings} if settings else {}
    
    def import_dict(self, settings_dict):
        for key, value in settings_dict.items():
            if hasattr(self, key):
                getattr(self, key).value = value


class Setting():
    name: str = None
    description: str = None
    value: ... = None
    type: SettingType = None
    min_value: int = None
    max_value: int = None

    def __init__(self, name, description, value, type, min_value=0, max_value=100):
        self.name = name
        self.description = description
        self.value = value
        self.type = type
        self.min_value = min_value
        self.max_value = max_value


class Cell():
    def __init__(self, value="", bold=False, color=None, percent=False, style=""):
        self.value = value
        self.bold = bold
        self.color = color
        self.percent = percent
        self.style = style

    def to_td(self):
        style = self.style
        if self.bold:
            style += "font-weight:bold;"
        if self.color:
            style += f"color:{self.color.value};"
        if style:
            style = f" style=\"{style}\""
        return f"<td{style if style else ''}>{self.value}{'%' if self.percent else ''}</td>"


class Row():
    long_name = None
    short_name = None
    description = None
    settings = None
    cells = None

    dialog = None
    style = None

    """Defines a row in the helper table.
    """
    def __init__(self):
        self.dialog = None
        self.style = None

    def _generate_cells(self, command_info) -> list[Cell]:
        """Returns a list of cells for this row.
        """
        cells = [Cell(self.short_name)]

        for command in command_info:
            cells.append(Cell())
        
        return cells

    def get_cells(self, command_info) -> list[Cell]:
        """Returns the value of the row at the given column index.
        """
        return self._generate_cells(command_info)

    def display_settings_dialog(self, parent):
        """Displays the settings dialog for this row.
        """
        self.dialog = gui.UmaPresetSettingsDialog(parent, self, SettingType, window_title="Change row options")
        self.dialog.exec()
        self.dialog = None
    
    def to_tr(self, command_info):
        td = ''.join(cell.to_td() for cell in self.get_cells(command_info))
        return f"<tr{self.get_style()}>{td}</tr>"
    
    def get_style(self):
        if self.style:
            return f" style=\"{self.style}\""
        return ""
    
    def to_dict(self, row_types):
        return {
            "type": row_types(type(self)).name,
            "settings": self.settings.to_dict() if self.settings else {}
        }


class PresetSettings(Settings):
    def __init__(self):
        self.s_energy_enabled = Setting(
            "Show energy",
            "Displays energy in the event helper.",
            True,
            SettingType.BOOL
        )
        self.s_scenario_specific_enabled = Setting(
            "Show scenario specific elements",
            "Show scenario specific elements in the event helper.\n(Grand Live tokens/Grand Masters fragments)",
            True,
            SettingType.BOOL
        )


def get_gm_fragment_strings():
    fragment_dict = {}
    for i in range(0, 23):
        fragment_img_path = f"_assets/gm/frag_{i:02}.png"
        asset_path = util.get_asset(fragment_img_path)

        if not os.path.exists(asset_path):
            continue

        with open(asset_path, "rb") as f:
            b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        
        fragment_dict[i] = b64

    return fragment_dict


class Preset():
    name = None
    rows = None
    initialized_rows: list[Row] = None
    row_types = None

    gm_fragment_dict = get_gm_fragment_strings()

    def __init__(self, row_types):
        self.settings = PresetSettings()

        self.row_types = row_types
        if self.rows:
            self.initialized_rows = [row.value() for row in self.rows]
        else:
            self.initialized_rows = []

    def __iter__(self):
        return iter(self.initialized_rows)
    
    def __gt__(self, other):
        return self.name > other.name
    
    def __lt__(self, other):
        return self.name < other.name
    
    def __eq__(self, other):
        return self.name == other.name
    
    def display_settings_dialog(self, parent):
        self.dialog = gui.UmaPresetSettingsDialog(parent, self, SettingType, window_title="Toggle elements")
        self.dialog.exec()
        self.dialog = None
    
    def generate_overlay(self, main_info, command_info):
        html_elements = []

        if self.settings.s_energy_enabled.value:
            html_elements.append(self.generate_energy(main_info))

        if self.settings.s_scenario_specific_enabled.value:
            html_elements.append(self.generate_gm_table(main_info))

        html_elements.append(self.generate_table(command_info))

        return ''.join(html_elements)
    
    def generate_energy(self, main_info):
        return f"<div id=\"energy\">Energy: {main_info['energy']}/{main_info['max_energy']}</div>"
    
    def generate_table(self, command_info):
        if not command_info:
            return ""

        table_header = ''.join(f"<th>{header}</th>" for header in TABLE_HEADERS)
        table = [f"<tr>{table_header}</tr>"]

        for row in self.initialized_rows:
            table.append(row.to_tr(command_info))

        thead = f"<thead>{table[0]}</thead>"
        tbody = f"<tbody>{''.join(table[1:])}</tbody>"
        return f"<table id=\"training-table\">{thead}{tbody}</table>"

    def generate_gm_table(self, main_info):
        if main_info['scenario_id'] != 5:
            return ""
        
        header = "<tr><th colspan=\"8\">Fragments</th></tr>"
    
        frag_tds = []
        for index, fragment_id in enumerate(main_info['gm_fragments']):
            frag_tds.append(f"<td style=\"{'outline: 1px solid red; outline-offset: -1px;' if index in (0, 4) else ''}\"><img src=\"{self.gm_fragment_dict[fragment_id]}\" height=\"36\" width=\"34\" style=\"display:block; margin: auto; width: auto; height: 36px;\" /></td>")
        
        frag_tr = f"<tr>{''.join(frag_tds)}</tr>"

        return f"<table id=\"gm-fragments\"><thead>{header}</thead><tbody>{frag_tr}</tbody></table>"


    def to_dict(self):
        return {
            "name": self.name,
            "settings": self.settings.to_dict(),
            "rows": [row.to_dict(self.row_types) for row in self.initialized_rows] if self.initialized_rows else []
        }
    
    def import_dict(self, preset_dict):
        if "name" in preset_dict:
            self.name = preset_dict["name"]
        if "settings" in preset_dict:
            self.settings.import_dict(preset_dict["settings"])
        if "rows" in preset_dict:
            self.initialized_rows = []
            for row_dict in preset_dict["rows"]:
                row_object = self.row_types[row_dict["type"]].value()
                if row_object.settings:
                    row_object.settings.import_dict(row_dict["settings"])
                self.initialized_rows.append(row_object)