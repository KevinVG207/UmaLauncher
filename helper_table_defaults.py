from enum import Enum
import helper_table_elements as hte
import util

class CurrentStatsRow(hte.Row):
    long_name = "Current stats"
    short_name = "Current"
    description = "Shows the current stats of each facility."

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            gained_stats = command['current_stats']
            cells.append(hte.Cell(gained_stats))

        return cells


class GainedStatsSettings(hte.Settings):
    def __init__(self):
        self.s_highlight_max = hte.Setting(
            "Highlight max",
            "Highlights the facility with the most gained stats.",
            True,
            hte.SettingType.BOOL
        )
        self.s_enable_skillpts = hte.Setting(
            "Include skill points",
            "Include skill points in the total.",
            False,
            hte.SettingType.BOOL
        )

class GainedStatsRow(hte.Row):
    long_name = "Total stats gained"
    short_name = "Stat Gain"
    description = "Shows the total stats gained per facility. This includes stats gained outside the facility itself. \nExcludes skill points by default."

    def __init__(self):
        super().__init__()
        self.settings = GainedStatsSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        all_gained_stats = []
        for facility in game_state.values():
            gained_stats = sum(facility['gained_stats'].values())
            if self.settings.s_enable_skillpts.value:
                gained_stats += facility['gained_skillpt']
            all_gained_stats.append(gained_stats)

        max_gained_stats = max(all_gained_stats)

        for gained_stats in all_gained_stats:
            if self.settings.s_highlight_max.value and max_gained_stats > 0 and gained_stats == max_gained_stats:
                cells.append(hte.Cell(gained_stats, bold=True, color=hte.Colors.GOOD))
            else:
                cells.append(hte.Cell(gained_stats))

        return cells

class GainedStatsDistributionSettings(hte.Settings):
    def __init__(self):
        self.s_include_skillpts = hte.Setting(
            "Include skill points",
            "Include skill points in the row.",
            False,
            hte.SettingType.BOOL
        )

class GainedStatsDistributionRow(hte.Row):
    long_name = "Gained stats distribution"
    short_name = "Stat Gain <br>Distribution"
    description = "Shows the stats gained per facility per type. This includes stats gained outside the facility itself."

    def __init__(self):
        super().__init__()
        self.settings = GainedStatsDistributionSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            gained_stats = command['gained_stats']

            out_lines = []
            if gained_stats['speed'] > 0:
                out_lines.append(f"Spd: {gained_stats['speed']}")
            if gained_stats['stamina'] > 0:
                out_lines.append(f"Sta: {gained_stats['stamina']}")
            if gained_stats['power'] > 0:
                out_lines.append(f"Pow: {gained_stats['power']}")
            if gained_stats['guts'] > 0:
                out_lines.append(f"Gut: {gained_stats['guts']}")
            if gained_stats['wiz'] > 0:
                out_lines.append(f"Wis: {gained_stats['wiz']}")

            if self.settings.s_include_skillpts.value and command['gained_skillpt'] > 0:
                out_lines.append(f"Skl: {command['gained_skillpt']}")
            
            cells.append(hte.Cell('<br>'.join(out_lines)))

        return cells


class GainedEnergySettings(hte.Settings):
    def __init__(self):
        self.s_enable_colors = hte.Setting(
        "Enable colors",
        "Enables coloring of the energy gained or lost.",
        False,
        hte.SettingType.BOOL
    )

class GainedEnergyRow(hte.Row):
    long_name = "Energy gained/lost"
    short_name = "Energy"
    description = "Shows the total energy gained or lost per facility."

    def __init__(self):
        super().__init__()
        self.settings = GainedEnergySettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            gained_energy = command['gained_energy']
            if self.settings.s_enable_colors.value:
                if gained_energy > 0:
                    cells.append(hte.Cell(gained_energy, color=hte.Colors.GOOD))
                elif gained_energy < 0:
                    cells.append(hte.Cell(gained_energy, color=hte.Colors.WARNING))
                else:
                    cells.append(hte.Cell(gained_energy))
            else:
                cells.append(hte.Cell(gained_energy))

        return cells
    

class TotalBondSettings(hte.Settings):
    def __init__(self):
        self.s_highlight_max = hte.Setting(
            "Highlight max",
            "Highlights the facility with the most total bond.",
            True,
            hte.SettingType.BOOL
        )

class TotalBondRow(hte.Row):
    long_name = "Total bond gained"
    short_name = "Total Bond"
    description = "Shows the total bond gain for each facility. Total includes all bond gains of all supports and Akikawa, until the bar is filled."

    def __init__(self):
        super().__init__()
        self.settings = TotalBondSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        max_total_bond = max(facility['total_bond'] for facility in game_state.values())

        for command in game_state.values():
            total_bond = command['total_bond']
            if self.settings.s_highlight_max.value and max_total_bond > 0 and total_bond == max_total_bond:
                cells.append(hte.Cell(total_bond, bold=True, color=hte.Colors.GOOD))
            else:
                cells.append(hte.Cell(total_bond))

        return cells


class UsefulBondSettings(hte.Settings):
    def __init__(self):
        self.s_highlight_max = hte.Setting(
            "Highlight max",
            "Highlights the facility with the most useful bond.",
            True,
            hte.SettingType.BOOL
        )



class UsefulBondRow(hte.Row):
    long_name = "Useful bond gained"
    short_name = "Useful Bond"
    description = "Shows the useful bond gain for each facility. Useful includes supports until orange bar, excluding friend/group cards. Also Akikawa until green bar."

    def __init__(self):
        super().__init__()
        self.settings = UsefulBondSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        max_useful_bond = max(facility['useful_bond'] for facility in game_state.values())

        for command in game_state.values():
            useful_bond = command['useful_bond']
            if self.settings.s_highlight_max.value and max_useful_bond > 0 and useful_bond == max_useful_bond:
                cells.append(hte.Cell(useful_bond, bold=True, color=hte.Colors.GOOD))
            else:
                cells.append(hte.Cell(useful_bond))

        return cells


class GainedSkillptSettings(hte.Settings):
    def __init__(self):
        self.s_highlight_max = hte.Setting(
            "Highlight max",
            "Highlights the facility with the most gained skill points.",
            False,
            hte.SettingType.BOOL
        )

class GainedSkillptRow(hte.Row):
    long_name = "Skill points gained"
    short_name = "Skill Points"
    description = "Shows the total skill points gained per facility."

    def __init__(self):
        super().__init__()
        self.settings = GainedSkillptSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        max_gained_skillpt = max(facility['gained_skillpt'] for facility in game_state.values())

        for command in game_state.values():
            gained_skillpt = command['gained_skillpt']
            if self.settings.s_highlight_max.value and max_gained_skillpt > 0 and gained_skillpt == max_gained_skillpt:
                cells.append(hte.Cell(gained_skillpt, bold=True, color=hte.Colors.GOOD))
            else:
                cells.append(hte.Cell(gained_skillpt))

        return cells


class FailPercentageSettings(hte.Settings):
    def __init__(self):
        self.s_enable_colors = hte.Setting(
            "Enable colors",
            "Enables coloring of the fail percentage.",
            True,
            hte.SettingType.BOOL
        )
        self.s_orange_threshold = hte.Setting(
            "Orange threshold",
            "The number from which the fail percentage is orange.",
            1,
            hte.SettingType.INT,
            0,
            100
        )
        self.s_red_threshold = hte.Setting(
            "Red threshold",
            "The number from which the fail percentage is red.",
            30,
            hte.SettingType.INT,
            0,
            100
        )

class FailPercentageRow(hte.Row):
    long_name = "Fail percentage"
    short_name = "Fail %"
    description = "Shows the fail percentage per facility."

    def __init__(self):
        super().__init__()
        self.settings = FailPercentageSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            fail_percentage = command['failure_rate']
            fail_string = f"{fail_percentage}%"
            if not self.settings.s_enable_colors.value or fail_percentage == 0:
                cells.append(hte.Cell(fail_string))
                continue

            if fail_percentage >= self.settings.s_red_threshold.value:
                cells.append(hte.Cell(fail_string, color=hte.Colors.ALERT))
            elif fail_percentage >= self.settings.s_orange_threshold.value:
                cells.append(hte.Cell(fail_string, color=hte.Colors.WARNING))
            else:
                cells.append(hte.Cell(fail_string))
                

        return cells


class LevelRow(hte.Row):
    long_name = "Facility level"
    short_name = "Level"
    description = "Shows the level of each facility."

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            cells.append(hte.Cell(command['level']))

        return cells
    

class GrandMastersFragmentsRow(hte.Row):
    long_name = "Grand Masters fragments (scenario-specific)"
    short_name = "Fragments"
    description = "Shows the total Grand Masters fragments on each facility. Hidden in other scenarios."

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        if game_state['speed']['scenario_id'] != 5:
            return []

        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            fragment_id = command['gm_fragment']
            is_double = bool(command['gm_fragment_double'])

            cell_text = f"<div style=\"display: flex; align-items: center; justify-content: center;\"><img src=\"{util.get_gm_fragment_dict()[fragment_id]}\" height=\"30\" width=\"28\" />"

            if is_double:
                cell_text += "<div>x2</div>"
            
            cell_text += "</div>"

            cells.append(hte.Cell(cell_text, bold=True, color=hte.Colors.GOOD))

        return cells
    
    def to_tr(self, command_info):
        if command_info['speed']['scenario_id'] != 5:
            return ""

        return super().to_tr(command_info)


class RowTypes(Enum):
    CURRENT_STATS = CurrentStatsRow
    GAINED_STATS = GainedStatsRow
    GAINED_STATS_DISTR = GainedStatsDistributionRow
    GAINED_ENERGY = GainedEnergyRow
    USEFUL_BOND = UsefulBondRow
    TOTAL_BOND = TotalBondRow
    GAINED_SKILLPT = GainedSkillptRow
    FAIL_PERCENTAGE = FailPercentageRow
    LEVEL = LevelRow
    GM_FRAGMENTS = GrandMastersFragmentsRow


class DefaultPreset(hte.Preset):
    name = "Default"
    rows = [
        RowTypes.CURRENT_STATS,
        RowTypes.GAINED_STATS,
        RowTypes.GAINED_ENERGY,
        RowTypes.USEFUL_BOND,
        RowTypes.TOTAL_BOND,
        RowTypes.GAINED_SKILLPT,
        RowTypes.FAIL_PERCENTAGE,
        RowTypes.LEVEL,
        RowTypes.GM_FRAGMENTS,
    ]
