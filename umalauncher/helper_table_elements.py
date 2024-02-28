import enum
from loguru import logger
import gui
import util
import constants
import settings_elements as se

TABLE_HEADERS = {
    "fac": "Facility",
    "speed": "Speed",
    "stamina": "Stamina",
    "power": "Power",
    "guts": "Guts",
    "wiz": "Wisdom",
    "ss_match": "SS Match"
}

class Colors(enum.Enum):
    """Defines the colors used in the helper table.
    """
    ALERT = "red"
    WARNING = "orange"
    GOOD = "lightgreen"


class Cell():
    def __init__(self, value="", bold=False, color=None, background=None, percent=False, title="", style="text-overflow: clip;white-space: nowrap;overflow: hidden;"):
        self.value = value
        self.bold = bold
        self.color = color
        self.percent = percent
        self.background = background
        self.style = style
        self.title = title

    def to_td(self):
        style = self.style
        if self.bold:
            style += "font-weight:bold;"
        if self.color:
            style += f"color:{self.color};"
        if self.background:
            style += f"background:{self.background};"
        if style:
            style = f" style=\"{style}\""
        
        title = self.title
        if title:
            title = title.replace('\n','')
            title = f" title=\"{title}\""
        return f"<td{style if style else ''}{title if title else ''}>{self.value}{'%' if self.percent else ''}</td>"


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
        self.disabled = False

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
        settings_var = [self.settings]
        self.dialog = gui.UmaPresetSettingsDialog(parent, settings_var, window_title="Change row options")
        self.dialog.exec()
        self.dialog = None
        self.settings = settings_var[0]
    
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


class PresetSettings(se.Settings):
    def __init__(self):
        self.s_energy_enabled = se.Setting(
            "Show energy",
            "Displays energy in the event helper.",
            True,
            se.SettingType.BOOL,
            priority=13
        )
        self.s_support_bonds = se.Setting(
            "Show support bonds",
            "Choose how to display support bonds.",
            2,
            se.SettingType.COMBOBOX,
            choices=["Off", "Number", "Bar", "Both"],
            priority=12
        )
        self.s_hide_support_bonds = se.Setting(
            "Auto-hide maxed supports",
            "When support bonds are enabled, automatically hide characters when they reach 100.",
            True,
            se.SettingType.BOOL,
            priority=11
        )
        self.s_displayed_value = se.Setting(
            "Displayed value(s) for stats",
            "Which value(s) to display for stats rows.",
            0,
            se.SettingType.COMBOBOX,
            choices=["Raw gained stats", "Overcap-compensated gained stats", "Both"],
            priority=10
        )
        self.s_skillpt_enabled = se.Setting(
            "Show skill points",
            "Displays skill points in the event helper.",
            False,
            se.SettingType.BOOL,
            priority=9
        )
        self.s_fans_enabled = se.Setting(
            "Show fans",
            "Displays fans in the event helper.",
            False,
            se.SettingType.BOOL,
            priority=8
        )
        self.s_schedule_enabled = se.Setting(
            "Show schedule countdown",
            "Displays the amount of turns until your next scheduled race. (If there is one.)",
            True,
            se.SettingType.BOOL,
            priority=7
        )
        self.s_scenario_specific_enabled = se.Setting(
            "Show scenario specific elements",
            "Show scenario specific elements in the event helper. \n(Grand Live tokens, Grand Masters fragments, Project L'Arc aptitude/supporter points & expectation gauge)",
            True,
            se.SettingType.BOOL,
            priority=6
        )


class Preset():
    name = None
    rows = None
    initialized_rows: list[Row] = None
    row_types = None

    gm_fragment_dict = util.get_gm_fragment_dict()
    gl_token_dict = util.get_gl_token_dict()

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
        settings_var = [self.settings]
        self.dialog = gui.UmaPresetSettingsDialog(parent, settings_var, window_title="Toggle elements")
        self.dialog.exec()
        self.dialog = None
        self.settings = settings_var[0]
    
    def generate_overlay(self, main_info, command_info):
        html_elements = []

        if self.settings.s_energy_enabled.value:
            html_elements.append(self.generate_energy(main_info))

        if self.settings.s_skillpt_enabled.value:
            html_elements.append(self.generate_skillpt(main_info))

        if self.settings.s_fans_enabled.value:
            html_elements.append(self.generate_fans(main_info))
        
        if self.settings.s_schedule_enabled.value:
            html_elements.append(self.generate_schedule(main_info))
        
        if self.settings.s_support_bonds.value:
            html_elements.append(self.generate_bonds(main_info, display_type=self.settings.s_support_bonds.value))

        if self.settings.s_scenario_specific_enabled.value:
            html_elements.append(self.generate_gm_table(main_info))
            html_elements.append(self.generate_gl_table(main_info))
            html_elements.append(self.generate_arc(main_info))
            html_elements.append(self.generate_uaf(main_info))

        html_elements.append(self.generate_table(command_info, main_info))

        # html_elements.append("""<button id="btn-skill-window" onclick="window.await_skill_window();">Open Skills Window</button>""")

        return ''.join(html_elements)
    
    def generate_energy(self, main_info):
        return f"<div id=\"energy\"><b>Energy:</b> {main_info['energy']}/{main_info['max_energy']}</div>"
    
    def generate_skillpt(self, main_info):
        return f"<div id=\"skill-pt\"><b>Skill Points:</b> {main_info['skillpt']:,}</div>"

    def generate_fans(self, main_info):
        return f"<div id=\"fans\"><b>Fans:</b> {main_info['fans']:,}</div>"
    
    def generate_table(self, command_info, main_info):
        if not command_info:
            return ""
        
        headers = [TABLE_HEADERS['fac']]
        if main_info['scenario_id'] == 7:
            headers = [f"""<th style="text-overflow: clip;white-space: nowrap;overflow: hidden;">{header}</th>""" for header in headers]

            # Use icons as headers
            for command_id in list(main_info['all_commands'].keys())[:5]:
                color_block_part = f"<div style=\"width: 100%;height: 100%;background-color: {util.UAF_COLOR_DICT[str(command_id)[1]]};position: absolute;top: 0;left: 0;z-index: -1\"></div>"
                img_part = f"<img src=\"{util.get_uaf_sport_image_dict()[str(command_id)]}\" width=\"32\" height=\"32\" style=\"display:inline-block; width: auto; height: 1.5rem; margin-top: 1px;\"/>"
                text_part = f"<br>{TABLE_HEADERS[constants.COMMAND_ID_TO_KEY[command_id]]}"
                header = f"""<th style="position: relative; text-overflow: clip;white-space: nowrap;overflow: hidden; z-index: 0; font-size: 0.8rem;">{color_block_part}{img_part}{text_part}</th>"""
                headers.append(header)

        else:
            headers += [TABLE_HEADERS[command] for command in command_info]
            headers = [f"""<th style="text-overflow: clip;white-space: nowrap;overflow: hidden;">{header}</th>""" for header in headers]


        table_header = ''.join(headers)
        table = [f"<tr>{table_header}</tr>"]

        for row in self.initialized_rows:
            if not row.disabled:
                table.append(row.to_tr(command_info))

        thead = f"<thead>{table[0]}</thead>"
        tbody = f"<tbody>{''.join(table[1:])}</tbody>"
        return f"<table id=\"training-table\">{thead}{tbody}</table>"

    def generate_bonds(self, main_info, display_type):
        eval_dict = main_info['eval_dict']
        ids = []
        for key in eval_dict.keys():
            if self.settings.s_hide_support_bonds.value and eval_dict[key].starting_bond == 100:
                continue

            if key < 100:
                ids.append(key)
            elif key == 102 and main_info['scenario_id'] not in (6,):  # Filter out non-cards except Akikawa
                ids.append(key)
        
        if not ids:
            return ""
    
        ids = sorted(ids)

        partners = []

        for id in ids:
            partner = eval_dict[id]

            bond_color = ""
            for cutoff, color in constants.BOND_COLOR_DICT.items():
                if partner.starting_bond < cutoff:
                    break
                bond_color = color

            img = f"<img src=\"{partner.img}\" width=\"56\" height=\"56\" style=\"display:inline-block;\"/>"
            bond_ele = ""
            if display_type in (2, 3):
                # Bars
                bond_ele += f"""
<div style="width: 100%;height: 0.75rem;position: relative;background-color: #4A494B;border-radius: 0.5rem;">
    <div style="position: absolute;width:calc(100% - 4px);height:calc(100% - 4px);top:2px;left:50%;transform: translateX(-50%);">
        <div style="position: absolute;width:100%;height:100%;background-color:#6E6B79;border-radius: 1rem;"></div>
        <div style="position: absolute;width:{partner.starting_bond}%;height:100%;background-color:{bond_color};"></div>
        <div style="position: absolute;width:2px;height:100%;background-color:#4A494B;top:0px;left:20%;transform: translateX(-50%);"></div>
        <div style="position: absolute;width:2px;height:100%;background-color:#4A494B;top:0px;left:40%;transform: translateX(-50%);"></div>
        <div style="position: absolute;width:2px;height:100%;background-color:#4A494B;top:0px;left:60%;transform: translateX(-50%);"></div>
        <div style="position: absolute;width:2px;height:100%;background-color:#4A494B;top:0px;left:80%;transform: translateX(-50%);"></div>
        <div style="position: absolute;width:100%;height:100%;border: 2px solid #4A494B;box-sizing: content-box;left: -2px;top: -2px;border-radius: 1rem;"></div>
    </div>
</div>""".replace("\n", "").replace("    ", "")
            if display_type in (1, 3):
                # Numbers
                bond_ele += f"<p style=\"margin:0;padding:0;color:{bond_color};font-weight:bold;\">{partner.starting_bond}</p>"
            
            ele = f"<div style=\"display:flex;flex-direction:column;align-items:center;gap:0.2rem;\">{img}{bond_ele}</div>"
            partners.append(ele)
        
        inner = ''.join(partners)

        return f"<div id=\"support-bonds\" style=\"max-width: 100vw; display: flex; flex-direction: row; flex-wrap: nowrap; overflow-x: auto; gap:0.3rem;\">{inner}</div>"

    def generate_gm_table(self, main_info):
        if main_info['scenario_id'] != 5:
            return ""
        
        header = "<tr><th colspan=\"8\">Fragments</th></tr>"
    
        frag_tds = []
        for index, fragment_id in enumerate(main_info['gm_fragments']):
            frag_tds.append(f"<td style=\"{'outline: 1px solid red; outline-offset: -1px;' if index in (0, 4) else ''}\"><img src=\"{self.gm_fragment_dict[fragment_id]}\" height=\"32\" width=\"30\" style=\"display:block; margin: auto; width: auto; height: 32px;\" /></td>")
        
        frag_tr = f"<tr>{''.join(frag_tds)}</tr>"

        return f"<table id=\"gm-fragments\"><thead>{header}</thead><tbody>{frag_tr}</tbody></table>"

    def generate_gl_table(self, main_info):
        if main_info['scenario_id'] != 3:
            return ""
        
        top_row = []
        bottom_row = []

        for token_type in constants.GL_TOKEN_LIST:
            top_row.append(f"<th><img src=\"{self.gl_token_dict[token_type]}\" height=\"32\" width=\"31\" style=\"display:block; margin: auto; width: auto; height: 32px;\" /></th>")
            bottom_row.append(f"<td>{main_info['gl_stats'][token_type]}</td>")
        
        top_row = f"<tr>{''.join(top_row)}</tr>"
        bottom_row = f"<tr>{''.join(bottom_row)}</tr>"

        return f"<table id=\"gl-tokens\"><thead>{top_row}</thead><tbody>{bottom_row}</tbody></table>"
    
    def generate_schedule(self, main_info):
        cur_turn = main_info['turn']
        next_race = None
        for race in main_info['scheduled_races']:
            if race['turn'] >= cur_turn:
                next_race = race
                break
        
        if not next_race:
            return ""
        
        turns_left = next_race['turn'] - cur_turn
        text = f"<p><b>{turns_left} turn{'' if turns_left == 1 else 's'}</b> until</p>"
        img = f"<img width=100 height=50 src=\"{next_race['thumb_url']}\"/>"

        fan_warning = ""

        if main_info['fans'] < next_race['fans']:
            fans_needed = next_race['fans'] - main_info['fans']
            fan_warning = f"""<p style="color: orange; margin: 0;"><b>{fans_needed} more</b> fans needed!</p>"""

        return f"""<div id="schedule" style="display: flex; flex-direction: column; justify-content: center; align-items: center;"><div id="schedule-race-container" style="display: flex; align-items: center; gap: 0.5rem;">{text}{img}</div>{fan_warning}</div>"""

    def generate_arc(self, main_info):
        if main_info['scenario_id'] != 6 or main_info['turn'] < 3:
            return ""

        gauge_str = str(main_info['arc_expectation_gauge'] // 10)
        gauge_str2 = str(main_info['arc_expectation_gauge'] % 10)
        return f"<div id=\"arc\"><b>Aptitude Points:</b> {main_info['arc_aptitude_points']:,} - <b>Supporter Points:</b> {main_info['arc_supporter_points']:,} - <b>Expectation Gauge:</b> {gauge_str}.{gauge_str2}%</div>"

    def generate_uaf(self, main_info):
        if main_info['scenario_id'] != 7:
            return ""
        
        uaf_sport_rank = main_info['uaf_sport_ranks']
        uaf_sport_rank_total = main_info['uaf_sport_rank_total']

        html_output = "<div id='uaf'><table><thead><tr><th style='position: relative; text-overflow: clip;white-space: nowrap;overflow: hidden; z-index: 0; font-size: 0.8rem;'>Genres</th>"
        
        for command_id in list(main_info['all_commands'].keys())[:5]:
            text_part = f"{TABLE_HEADERS[constants.COMMAND_ID_TO_KEY[command_id]]}"
            header = f"""<th style="position: relative; text-overflow: clip;white-space: nowrap;overflow: hidden; z-index: 0; font-size: 0.8rem;">{text_part}</th>"""
            html_output += header
            
        html_output += "</tr></thead><tbody>"

        # Loop through the IDs
        for base in [2100, 2200, 2300]:
            total_row = 0
            row = f"<tr style='background-color:{util.UAF_COLOR_DICT[str(base)[1]]}'><td style='display: flex; align-items: center; justify-content: center; flex-direction: row; gap: 5px'><img src=\"{util.get_uaf_genre_image_dict()[str(base)]}\" width=\"32\" height=\"32\" style=\"display:inline-block; width: auto; height: 1.5rem; margin-top: 1px;\"/><div>{uaf_sport_rank_total[base]}</div></td>"
            for i in range(1, 6):
                id = base + i
                if id in uaf_sport_rank:
                    rank = uaf_sport_rank.get(id, 0)
                    total_row += rank
                    row += f"""<td>{rank}</td>"""
                    
            row += "</tr>"
            html_output += row

        html_output += "</tbody></table></div>"

        return html_output
        
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
