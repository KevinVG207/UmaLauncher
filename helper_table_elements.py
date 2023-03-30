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

    """Defines a row in the helper table.
    """
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

    def _make_settings_dialog(self) -> gui.UmaMainWidget:
        """Returns a settings dialog for this row.
        """
        pass

    def display_settings_dialog(self):
        """Displays the settings dialog for this row.
        """
        dialog = self._make_settings_dialog()
        dialog.show()

class Preset():
    name = None
    rows: list[Row] = []

    def __init__(self, row_types):
        self.rows = [row_types[row]() for row in self.rows]

    def __iter__(self):
        return iter(self.rows)
    
    def generate_table(self, game_state):
        if not game_state:
            return ""

        table = [[f"<th>{header}</th>" for header in TABLE_HEADERS]]

        for row in self.rows:
            table.append([cell.to_td() for cell in row.get_cells(game_state)])

        table = [f"<tr>{''.join(row)}</tr>" for row in table]

        thead = f"<thead>{table[0]}</thead>"
        tbody = f"<tbody>{''.join(table[1:])}</tbody>"
        return thead + tbody

class SettingType(enum.Enum):
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "str"

class Settings():
    def get_settings_keys(self):
        return [attr for attr in dir(self) if attr.startswith("s_")]

    def to_dict(self):
        settings = self.get_settings_keys()
        return {setting: getattr(self, setting).value for setting in settings}

@dataclass
class Setting():
    name: str
    description: str
    value: ...
    type: SettingType
