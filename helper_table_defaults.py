import helper_table_elements as hte

class CurrentStatsRow(hte.Row):
    long_name = "Current stats per facility"
    short_name = "Current"
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
        "Highlights the facility with the most gained stats",
        True,
        hte.SettingType.BOOL
    )

class GainedStatsRow(hte.Row):
    long_name = "Total stats gained per facility"
    short_name = "Stat Gain"
    settings = None

    def __init__(self, game_state):
        self.settings = GainedStatsSettings()
        super().__init__(game_state)

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name)]

        max_gained_stats = max(facility['gained_stats'] for facility in game_state.values())

        for command in game_state.values():
            gained_stats = command['gained_stats']
            if self.settings.s_highlight_max and gained_stats == max_gained_stats:
                cells.append(hte.Cell(gained_stats, bold=True, color=hte.Colors.GOOD))
            else:
                cells.append(hte.Cell(gained_stats))

        return cells


class DefaultPreset(hte.Preset):
    name = "Default"
    rows = [
        CurrentStatsRow,
        GainedStatsRow
    ]