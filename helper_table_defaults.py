from enum import Enum
import helper_table_elements as hte

class CurrentStatsRow(hte.Row):
    long_name = "Current stats per facility"
    short_name = "Current"
    description = "Shows the current stats of each facility."
    settings = None

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name)]

        for command in game_state.values():
            gained_stats = command['current_stats']
            cells.append(hte.Cell(gained_stats))

        return cells


class GainedStatsSettings(hte.Settings):
    s_highlight_max = hte.Setting(
        "Highlight max",
        "Highlights the facility with the most gained stats.",
        True,
        hte.SettingType.BOOL
    )

class GainedStatsRow(hte.Row):
    long_name = "Stats gained per facility"
    short_name = "Stat Gain"
    description = "Shows the total stats gained per facility. This includes stats gained outside the facility itself."
    settings = GainedStatsSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name)]

        max_gained_stats = max(facility['gained_stats'] for facility in game_state.values())

        for command in game_state.values():
            gained_stats = command['gained_stats']
            if self.settings.s_highlight_max.value and gained_stats == max_gained_stats:
                cells.append(hte.Cell(gained_stats, bold=True, color=hte.Colors.GOOD))
            else:
                cells.append(hte.Cell(gained_stats))

        return cells


class GainedEnergySettings(hte.Settings):
    s_enable_colors = hte.Setting(
        "Enable colors",
        "Enables coloring of the energy gained or lost.",
        False,
        hte.SettingType.BOOL
    )

class GainedEnergyRow(hte.Row):
    long_name = "Energy gained/lost per facility"
    short_name = "Energy"
    description = "Shows the total energy gained or lost per facility."
    settings = GainedEnergySettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name)]

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


class UsefulBondSettings(hte.Settings):
    s_highlight_max = hte.Setting(
        "Highlight max",
        "Highlights the facility with the most useful bond.",
        True,
        hte.SettingType.BOOL
    )

class UsefulBondRow(hte.Row):
    long_name = "Useful bond gained per facility"
    short_name = "Useful Bond"
    description = "Useful includes supports until orange bar, excluding friend/group cards. Also Akikawa until green bar."
    settings = UsefulBondSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name)]

        max_useful_bond = max(facility['useful_bond'] for facility in game_state.values())

        for command in game_state.values():
            useful_bond = command['useful_bond']
            if self.settings.s_highlight_max.value and useful_bond == max_useful_bond:
                cells.append(hte.Cell(useful_bond, bold=True, color=hte.Colors.GOOD))
            else:
                cells.append(hte.Cell(useful_bond))

        return cells


class GainedSkillptSettings(hte.Settings):
    s_highlight_max = hte.Setting(
        "Highlight max",
        "Highlights the facility with the most gained skill points.",
        False,
        hte.SettingType.BOOL
    )
    s_highlight_max2 = hte.Setting(
        "Highlight max2",
        "Highlights the facility with the most gained skill points.",
        False,
        hte.SettingType.BOOL
    )
    s_highlight_max3 = hte.Setting(
        "Highlight max3",
        "Highlights the facility with the most gained skill points.",
        False,
        hte.SettingType.BOOL
    )

class GainedSkillptRow(hte.Row):
    long_name = "Skill points gained per facility"
    short_name = "Skill Points"
    description = "Shows the total skill points gained per facility."
    settings = GainedSkillptSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name)]

        max_gained_skillpt = max(facility['gained_skillpt'] for facility in game_state.values())

        for command in game_state.values():
            gained_skillpt = command['gained_skillpt']
            if self.settings.s_highlight_max.value and gained_skillpt == max_gained_skillpt:
                cells.append(hte.Cell(gained_skillpt, bold=True, color=hte.Colors.GOOD))
            else:
                cells.append(hte.Cell(gained_skillpt))

        return cells


class FailPercentageSettings(hte.Settings):
    s_enable_colors = hte.Setting(
        "Enable colors",
        "Enables coloring of the fail percentage.",
        True,
        hte.SettingType.BOOL
    )
    s_orange_threshold = hte.Setting(
        "Orange threshold",
        "The number from which the fail percentage is orange.",
        1,
        hte.SettingType.INT,
        0,
        100
    )
    s_red_threshold = hte.Setting(
        "Red threshold",
        "The number from which the fail percentage is red.",
        30,
        hte.SettingType.INT,
        0,
        100
    )

class FailPercentageRow(hte.Row):
    long_name = "Fail percentage per facility"
    short_name = "Fail %"
    description = "Shows the fail percentage per facility."
    settings = FailPercentageSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name)]

        for command in game_state.values():
            fail_percentage = command['failure_rate']
            fail_string = f"{fail_percentage}%"
            if self.settings.s_enable_colors.value:
                if fail_percentage >= self.settings.s_red_threshold.value:
                    cells.append(hte.Cell(fail_string, color=hte.Colors.ALERT))
                elif fail_percentage >= self.settings.s_orange_threshold.value:
                    cells.append(hte.Cell(fail_string, color=hte.Colors.WARNING))
                else:
                    cells.append(hte.Cell(fail_string))
            else:
                cells.append(hte.Cell(fail_string))

        return cells


class LevelRow(hte.Row):
    long_name = "Facility level"
    short_name = "Level"
    description = "Shows the level of each facility."

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name)]

        for command in game_state.values():
            cells.append(hte.Cell(command['level']))

        return cells

class RowTypes(Enum):
    CURRENT_STATS = CurrentStatsRow
    GAINED_STATS = GainedStatsRow
    GAINED_ENERGY = GainedEnergyRow
    USEFUL_BOND = UsefulBondRow
    GAINED_SKILLPT = GainedSkillptRow
    FAIL_PERCENTAGE = FailPercentageRow
    LEVEL = LevelRow


class DefaultPreset(hte.Preset):
    name = "Default"
    rows = [
        RowTypes.CURRENT_STATS,
        RowTypes.GAINED_STATS,
        RowTypes.GAINED_ENERGY,
        RowTypes.USEFUL_BOND,
        RowTypes.GAINED_SKILLPT,
        RowTypes.FAIL_PERCENTAGE,
        RowTypes.LEVEL
    ]

class TestPreset(hte.Preset):
    name = "Test 1"
    rows = [
        RowTypes.CURRENT_STATS,
        RowTypes.GAINED_ENERGY,
        RowTypes.USEFUL_BOND
    ]

class Test2Preset(hte.Preset):
    name = "Test 2"
    rows = [
        RowTypes.GAINED_ENERGY,
        RowTypes.USEFUL_BOND,
        RowTypes.GAINED_SKILLPT,
        RowTypes.FAIL_PERCENTAGE
    ]