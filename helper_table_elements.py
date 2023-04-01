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
    def __init__(self, value="", bold=False, color=None, percent=False):
        self.value = value
        self.bold = bold
        self.color = color
        self.percent = percent

    def to_td(self):
        style = ""
        if self.bold:
            style += "font-weight:bold;"
        if self.color:
            style += f"color:{self.color.value};"
        if style:
            style = f"style=\"{style}\""
        return f"<td {style if style else ''}>{self.value}{'%' if self.percent else ''}</td>"


class Row():
    long_name = None
    short_name = None
    description = None
    settings = None
    cells = None

    dialog = None

    """Defines a row in the helper table.
    """
    def __init__(self):
        self.dialog = None

    def _generate_cells(self, game_state) -> list[Cell]:
        """Returns a list of cells for this row.
        """
        cells = [Cell(self.short_name)]

        for command in game_state:
            cells.append(Cell())
        
        return cells

    def get_cells(self, game_state) -> list[Cell]:
        """Returns the value of the row at the given column index.
        """
        return self._generate_cells(game_state)

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

class Preset():
    name = None
    rows = None
    initialized_rows: list[Row] = None
    default = False

    def __init__(self, row_types):
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
    
    def generate_table(self, game_state):
        if not game_state:
            return ""

        table = [[f"<th>{header}</th>" for header in TABLE_HEADERS]]

        for row in self.initialized_rows:
            table.append([cell.to_td() for cell in row.get_cells(game_state)])

        table = [f"<tr>{''.join(row)}</tr>" for row in table]

        thead = f"<thead>{table[0]}</thead>"
        tbody = f"<tbody>{''.join(table[1:])}</tbody>"
        return thead + tbody

class SettingType(enum.Enum):
    BOOL = "bool"
    INT = "int"

class Settings():
    def get_settings_keys(self):
        return [attr for attr in dir(self) if attr.startswith("s_")]

    def to_dict(self):
        settings = self.get_settings_keys()
        return {setting: getattr(self, setting).value for setting in settings}


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