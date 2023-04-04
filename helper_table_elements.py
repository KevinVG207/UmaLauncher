import enum
from dataclasses import dataclass
from loguru import logger
import gui

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

    def _make_settings_dialog(self, parent) -> gui.UmaMainWidget:
        """Returns a settings dialog for this row.
        """
        return gui.UmaRowSettingsDialog(parent, self, SettingType)

    def display_settings_dialog(self, parent):
        """Displays the settings dialog for this row.
        """
        self.dialog = self._make_settings_dialog(parent)
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


class Preset():
    name = None
    rows = None
    initialized_rows: list[Row] = None
    row_types = None

    def __init__(self, row_types):
        self.energy_enabled = True
        self.scenario_specific_enabled = True

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
    
    def generate_overlay(self, main_info, command_info):
        return ''.join([
            self.generate_energy(main_info),
            self.generate_table(command_info)
        ])
    
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

    def to_dict(self):
        return {
            "name": self.name,
            "rows": [row.to_dict(self.row_types) for row in self.initialized_rows] if self.initialized_rows else []
        }
    
    def import_dict(self, preset_dict):
        self.name = preset_dict["name"]
        self.initialized_rows = []
        for row_dict in preset_dict["rows"]:
            row_object = self.row_types[row_dict["type"]].value()
            if row_object.settings:
                row_object.settings.import_dict(row_dict["settings"])
            self.initialized_rows.append(row_object)

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