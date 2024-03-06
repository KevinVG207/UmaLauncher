import enum
from loguru import logger

class SettingType(enum.Enum):
    UNDEFINED = "undefined"
    BOOL = "bool"
    INT = "int"
    COMBOBOX = "combobox"
    LIST = "list"
    COLOR = "color"
    STRING = "string"
    DICT = "dict"
    RADIOBUTTONS = "radiobuttons"
    FOLDERDIALOG = "folderdialog"
    FILEDIALOG = "filedialog"
    MESSAGE = "message"
    XYWHSPINBOXES = "xywhspinboxes"
    LRTBSPINBOXES = "lrtbspinboxes"
    DIVIDER = "divider"
    COMMANDBUTTON = "commandbutton"


class Settings():
    def get_settings_keys(self):
        return sorted([attr for attr in dir(self) if attr.startswith("s_")], key=lambda x: getattr(self, x).priority, reverse=True)

    def to_dict(self):
        settings = self.get_settings_keys()
        return {setting: getattr(self, setting).value for setting in settings if getattr(self, setting).type not in (SettingType.MESSAGE, SettingType.DIVIDER, SettingType.COMMANDBUTTON)} if settings else {}

    def import_dict(self, settings_dict, keep_undefined=False):
        for key, value in settings_dict.items():
            if not key.startswith("s_"):
                continue

            if not hasattr(self, key):
                if keep_undefined:
                    self.__setattr__(key, Setting(
                        name=key,
                        description="Undefined setting",
                        value=value,
                        type=SettingType.UNDEFINED,
                        priority=-2
                    ))
                continue

            attribute = getattr(self, key)

            if isinstance(attribute.value, dict):
                true_keys = set(attribute.value.keys())
                new_keys = set(value.keys())

                if true_keys != new_keys:
                    logger.warning(f"Setting {key} has different keys in the new settings dict. Reverting to default.")
                    logger.warning(f"True keys: {true_keys}")
                    logger.warning(f"New keys: {new_keys}")
                    continue

            attribute.value = value

    def __repr__(self):
        return str(self.to_dict())


class NewSettings():
    _settings = {}

    def __init__(self):
        for key, value in self._settings.items():
            self.__setattr__(key, value)

    def keys(self):
        return self._settings.keys()

    def to_dict(self):
        ret_dict = {}
        for key, value in self._settings.items():
            if value.type in (SettingType.MESSAGE, SettingType.DIVIDER, SettingType.COMMANDBUTTON):
                continue
            ret_dict[key] = value.value
        return ret_dict

    def from_dict(self, settings_dict, keep_undefined=False):
        for key, value in settings_dict.items():
            if key.startswith("s_"):
                key = key[2:]

            if not hasattr(self, key):
                if keep_undefined:
                    self.__setattr__(key, Setting(
                        name=key,
                        description="Undefined setting",
                        value=value,
                        type=SettingType.UNDEFINED,
                        hidden=True
                    ))
                continue

            attribute = getattr(self, key)

            if isinstance(attribute.value, dict):
                true_keys = set(attribute.value.keys())
                new_keys = set(value.keys())

                if true_keys != new_keys:
                    logger.warning(f"Setting {key} has different keys in the new settings dict. Reverting to default.")
                    logger.warning(f"True keys: {true_keys}")
                    logger.warning(f"New keys: {new_keys}")
                    continue

            attribute.value = value

    def __contains__(self, key):
        return key in self._settings
    
    def __getitem__(self, key):
        if not key in self._settings:
            raise KeyError(f"Setting {key} not found in settings.")
        return self._settings[key]
    
    def __setitem__(self, key, value):
        if not key in self._settings:
            raise KeyError(f"Setting {key} not found in settings.")
        self._settings[key].value = value

    def __repr__(self):
        return str(self.to_dict())


class Setting():
    name: str = None
    description: str = None
    hidden: bool = False
    value: ... = None
    type: SettingType = None
    min_value: int = None
    max_value: int = None
    choices: list = None

    def __init__(self, name, description, value, type, hidden=False, min_value=0, max_value=100, choices=None, tab=" General"):
        self.name = name
        self.description = description
        self.value = value
        self.type = type
        self.hidden = hidden
        self.min_value = min_value
        self.max_value = max_value
        self.choices = choices if choices else []
        self.tab = tab