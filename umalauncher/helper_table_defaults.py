from enum import Enum
import copy
import helper_table_elements as hte
import util
import settings_elements as se

def compensate_overcap(game_state, command):
    # Compensate for overcapped stats by doubling any gained stats that bring the current stats over 1200.
    current_stats = {command_type: game_state[command_type]['current_stats'] for command_type in game_state}
    gained_stats = copy.deepcopy(command['gained_stats'])
    for stat in current_stats:
        if current_stats[stat] + gained_stats[stat] > 1200:
            stats_until_1200 = max(1200 - current_stats[stat], 0)
            gained_stats[stat] = stats_until_1200 + (gained_stats[stat] - stats_until_1200) * 2

    return gained_stats


class CurrentStatsRow(hte.Row):
    long_name = "Current stats"
    short_name = "Current Stats"
    description = "Shows the current stats of each facility."

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            gained_stats = command['current_stats']
            cells.append(hte.Cell(gained_stats))

        return cells


class GainedStatsSettings(se.Settings):
    def __init__(self):
        self.s_highlight_max = se.Setting(
            "Highlight max",
            "Highlights the facility with the most gained stats.",
            True,
            se.SettingType.BOOL,
            priority=8
        )
        self.s_enable_skillpts = se.Setting(
            "Include skill points",
            "Include skill points in the total.",
            False,
            se.SettingType.BOOL,
            priority=10
        )
        self.s_displayed_value = se.Setting(
            "Displayed value(s)",
            "Which value(s) to display.",
            0,
            se.SettingType.LISTSELECT,
            choices=["Raw gained stats", "Overcap-compensated gained stats", "Both"],
            priority=9
        )
        self.s_highlight_max_overcapped = se.Setting(
            "Highlight max (compensated)",
            "(Only when 'highlight max' is enabled and both stats types are displayed.)\nHighlights the facility with the most gained stats, using the compensated values.",
            True,
            se.SettingType.BOOL,
            priority=7
        )
        self.s_highlight_color = se.Setting(
            "Highlight color",
            "The color to use for highlighting.",
            "#90EE90",
            se.SettingType.COLOR,
            priority=6
        )

def make_gained_stats_text(gained_stats, gained_stats_compensated, highlight_color="#90EE90", highlight=0):
    stats_highlight_span_open = f"<span style=\"font-weight: bold; color: {highlight_color};\">"
    stats_highlight_span_close = "</span>"

    if gained_stats_compensated == gained_stats:
        if highlight < 1:
            return f"{gained_stats}"
        else:
            return f"{stats_highlight_span_open}{gained_stats}{stats_highlight_span_close}"
    else:
        if highlight == 1:
            return f"{stats_highlight_span_open}{gained_stats}{stats_highlight_span_close} ({gained_stats_compensated})"
        elif highlight == 2:
            return f"{gained_stats} ({stats_highlight_span_open}{gained_stats_compensated}{stats_highlight_span_close})"
        else:
            return f"{gained_stats} ({gained_stats_compensated})"

class GainedStatsRow(hte.Row):
    long_name = "Stats gained total"
    short_name = "Stat Gain"
    description = "Shows the total stats gained per facility. This includes stats gained outside the facility itself. \nExcludes skill points by default."

    def __init__(self):
        super().__init__()
        self.settings = GainedStatsSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        all_gained_stats = []
        all_gained_stats_compensated = []
        for command in game_state.values():
            gained_stats = sum(command['gained_stats'].values())
            gained_stats_compensated = sum(compensate_overcap(game_state, command).values())
            if self.settings.s_enable_skillpts.value:
                gained_stats += command['gained_skillpt']
                gained_stats_compensated += command['gained_skillpt']
            all_gained_stats.append(gained_stats)
            all_gained_stats_compensated.append(gained_stats_compensated)

        if self.settings.s_highlight_max_overcapped.value and self.settings.s_displayed_value.value == 2 or self.settings.s_displayed_value.value == 1:
            max_gained_stats = max(all_gained_stats_compensated)
        else:
            max_gained_stats = max(all_gained_stats)

        for i, gained_stats in enumerate(all_gained_stats):
            gained_stats_compensated = all_gained_stats_compensated[i]
            if self.settings.s_highlight_max.value:
                if self.settings.s_displayed_value.value == 2:
                    if self.settings.s_highlight_max_overcapped.value and gained_stats_compensated == max_gained_stats:
                        cells.append(hte.Cell(make_gained_stats_text(gained_stats, gained_stats_compensated, self.settings.s_highlight_color.value, highlight=2)))
                        continue
                    elif not self.settings.s_highlight_max_overcapped.value and gained_stats == max_gained_stats:
                        cells.append(hte.Cell(make_gained_stats_text(gained_stats, gained_stats_compensated, self.settings.s_highlight_color.value, highlight=1)))
                        continue
                elif self.settings.s_displayed_value.value == 0 and gained_stats == max_gained_stats:
                    cells.append(hte.Cell(gained_stats, bold=True, color=self.settings.s_highlight_color.value))
                    continue
                elif self.settings.s_displayed_value.value == 1 and gained_stats_compensated == max_gained_stats:
                    cells.append(hte.Cell(gained_stats_compensated, bold=True, color=self.settings.s_highlight_color.value))
                    continue

            if self.settings.s_displayed_value.value == 2:
                cells.append(hte.Cell(make_gained_stats_text(gained_stats, gained_stats_compensated)))
            elif self.settings.s_displayed_value.value == 0:
                cells.append(hte.Cell(gained_stats))
            elif self.settings.s_displayed_value.value == 1:
                cells.append(hte.Cell(gained_stats_compensated))

        return cells

class GainedStatsDistributionSettings(se.Settings):
    def __init__(self):
        self.s_include_skillpts = se.Setting(
            "Include skill points",
            "Include skill points in the row.",
            False,
            se.SettingType.BOOL
        )
        self.s_displayed_value = se.Setting(
            "Displayed value(s)",
            "Which value(s) to display.",
            0,
            se.SettingType.LISTSELECT,
            choices=["Raw gained stats", "Overcap-compensated gained stats", "Both"]
        )


class GainedStatsDistributionRow(hte.Row):
    long_name = "Stats gained distribution"
    short_name = "Stat Gain <br>Distribution"
    description = "Shows the stats gained per facility per type. This includes stats gained outside the facility itself."

    def __init__(self):
        super().__init__()
        self.settings = GainedStatsDistributionSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            gained_stats = command['gained_stats']
            gained_stats_compensated = compensate_overcap(game_state, command)

            def display_value(gained, compensated):
                if self.settings.s_displayed_value.value == 0:
                    return gained
                elif self.settings.s_displayed_value.value == 1:
                    return compensated
                elif self.settings.s_displayed_value.value == 2:
                    return make_gained_stats_text(gained, compensated)

            out_lines = []
            if gained_stats['speed'] > 0:
                out_lines.append(f"Spd: {display_value(gained_stats['speed'], gained_stats_compensated['speed'])}")
            if gained_stats['stamina'] > 0:
                out_lines.append(f"Sta: {display_value(gained_stats['stamina'], gained_stats_compensated['stamina'])}")
            if gained_stats['power'] > 0:
                out_lines.append(f"Pow: {display_value(gained_stats['power'], gained_stats_compensated['power'])}")
            if gained_stats['guts'] > 0:
                out_lines.append(f"Gut: {display_value(gained_stats['guts'], gained_stats_compensated['guts'])}")
            if gained_stats['wiz'] > 0:
                out_lines.append(f"Wis: {display_value(gained_stats['wiz'], gained_stats_compensated['wiz'])}")

            if self.settings.s_include_skillpts.value and command['gained_skillpt'] > 0:
                out_lines.append(f"Skl: {command['gained_skillpt']}")
            
            cells.append(hte.Cell('<br>'.join(out_lines)))

        return cells


class GainedEnergySettings(se.Settings):
    def __init__(self):
        self.s_enable_colors = se.Setting(
            "Enable colors",
            "Enables coloring of the energy gained or lost.",
            False,
            se.SettingType.BOOL,
            priority=10
        )
        self.s_gain_color = se.Setting(
            "Energy gain color",
            "The color to use for energy gained.",
            "#90EE90",
            se.SettingType.COLOR
        )
        self.s_loss_color = se.Setting(
            "Energy loss color",
            "The color to use for energy lost.",
            "#FFA500",
            se.SettingType.COLOR
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
                    cells.append(hte.Cell(gained_energy, color=self.settings.s_gain_color.value))
                elif gained_energy < 0:
                    cells.append(hte.Cell(gained_energy, color=self.settings.s_loss_color.value))
                else:
                    cells.append(hte.Cell(gained_energy))
            else:
                cells.append(hte.Cell(gained_energy))

        return cells


class TotalBondSettings(se.Settings):
    def __init__(self):
        self.s_highlight_max = se.Setting(
            "Highlight max",
            "Highlights the facility with the most total bond.",
            True,
            se.SettingType.BOOL
        )
        self.s_highlight_max_color = se.Setting(
            "Highlight max color",
            "The color to use for highlighting the facility with the most total bond.",
            "#90EE90",
            se.SettingType.COLOR
        )

class TotalBondRow(hte.Row):
    long_name = "Bond gained total"
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
                cells.append(hte.Cell(total_bond, bold=True, color=self.settings.s_highlight_max_color.value))
            else:
                cells.append(hte.Cell(total_bond))

        return cells


class UsefulBondSettings(se.Settings):
    def __init__(self):
        self.s_highlight_max = se.Setting(
            "Highlight max",
            "Highlights the facility with the most useful bond.",
            True,
            se.SettingType.BOOL
        )
        self.s_highlight_max_color = se.Setting(
            "Highlight max color",
            "The color to use for highlighting the facility with the most useful bond.",
            "#90EE90",
            se.SettingType.COLOR
        )



class UsefulBondRow(hte.Row):
    long_name = "Useful bond gained total"
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
                cells.append(hte.Cell(useful_bond, bold=True, color=self.settings.s_highlight_max_color.value))
            else:
                cells.append(hte.Cell(useful_bond))

        return cells


class GainedSkillptSettings(se.Settings):
    def __init__(self):
        self.s_highlight_max = se.Setting(
            "Highlight max",
            "Highlights the facility with the most gained skill points.",
            True,
            se.SettingType.BOOL
        )
        self.s_highlight_max_color = se.Setting(
            "Highlight max color",
            "The color to use for highlighting the facility with the most gained skill points.",
            "#90EE90",
            se.SettingType.COLOR
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
                cells.append(hte.Cell(gained_skillpt, bold=True, color=self.settings.s_highlight_max_color.value))
            else:
                cells.append(hte.Cell(gained_skillpt))

        return cells


class FailPercentageSettings(se.Settings):
    def __init__(self):
        self.s_enable_colors = se.Setting(
            "Enable colors",
            "Enables coloring of the fail percentage.",
            True,
            se.SettingType.BOOL,
            priority=10
        )
        self.s_warning_color = se.Setting(
            "Warning color",
            "The color to use for the fail percentage when it is above the warning threshold.",
            "#FFA500",
            se.SettingType.COLOR,
            priority=9
        )
        self.s_warning_threshold = se.Setting(
            "Warning threshold",
            "The number from which the fail percentage uses the warning color.",
            1,
            se.SettingType.INT,
            priority=8,
            min_value=0,
            max_value=100
        )
        self.s_alert_color = se.Setting(
            "Alert color",
            "The color to use for the fail percentage when it is above the alert threshold.",
            "#FF0000",
            se.SettingType.COLOR,
            priority=7
        )
        self.s_alert_threshold = se.Setting(
            "Alert threshold",
            "The number from which the fail percentage uses the alert color.",
            30,
            se.SettingType.INT,
            priority=6,
            min_value=0,
            max_value=100
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

            if fail_percentage >= self.settings.s_alert_threshold.value:
                cells.append(hte.Cell(fail_string, color=self.settings.s_alert_color.value, bold=True))
            elif fail_percentage >= self.settings.s_warning_threshold.value:
                cells.append(hte.Cell(fail_string, color=self.settings.s_warning_color.value, bold=True))
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

class GrandMastersFragmentsSettings(se.Settings):
    def __init__(self):
        self.s_double_color = se.Setting(
            "Double fragment color",
            "The color to use to indicate a double fragment.",
            "#90EE90",
            se.SettingType.COLOR
        )

class GrandMastersFragmentsRow(hte.Row):
    long_name = "Grand Masters fragments"
    short_name = "Fragments"
    description = "[Scenario-specific] Shows the total Grand Masters fragments on each facility. Hidden in other scenarios."

    def __init__(self):
        super().__init__()
        self.settings = GrandMastersFragmentsSettings()

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

            cells.append(hte.Cell(cell_text, bold=True, color=self.settings.s_double_color.value))

        return cells
    
    def to_tr(self, command_info):
        if command_info['speed']['scenario_id'] != 5:
            return ""

        return super().to_tr(command_info)


class GrandLiveTotalTokensSettings(se.Settings):
    def __init__(self):
        self.s_highlight_max = se.Setting(
            "Highlight max",
            "Highlights the facility with the most Grand Live tokens.",
            True,
            se.SettingType.BOOL
        )
        self.s_highlight_max_color = se.Setting(
            "Highlight max color",
            "The color to use to highlight the facility with the most Grand Live tokens.",
            "#90EE90",
            se.SettingType.COLOR
        )

class GrandLiveTotalTokensRow(hte.Row):
    long_name = "Grand Live tokens total"
    short_name = "Token Gain"
    description = "[Scenario-specific] Shows the total Grand Live tokens on each facility. Hidden in other scenarios."

    def __init__(self):
        super().__init__()
        self.settings = GrandLiveTotalTokensSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        if game_state['speed']['scenario_id'] != 3:
            return []

        cells = [hte.Cell(self.short_name, title=self.description)]

        max_gl_tokens = max(sum(command['gl_tokens'].values()) for command in game_state.values())

        for command in game_state.values():
            gl_tokens = sum(command['gl_tokens'].values())
            if self.settings.s_highlight_max.value and max_gl_tokens > 0 and gl_tokens == max_gl_tokens:
                cells.append(hte.Cell(gl_tokens, bold=True, color=self.settings.s_highlight_max_color.value))
            else:
                cells.append(hte.Cell(gl_tokens))

        return cells



class GrandLiveTokensDistributionRow(hte.Row):
    long_name = "Grand Live tokens gained distribution"
    short_name = "Token Gain <br>Distribution"
    description = "[Scenario-specific] Shows the distribution of Grand Live tokens on each facility. Hidden in other scenarios."

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        if game_state['speed']['scenario_id'] != 3:
            return []

        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            gl_tokens_dict = command['gl_tokens']
            
            cell_text = f"<div style=\"display: flex; align-items: center; justify-content: center; gap: 0.2rem;\">"
            for token_type, value in gl_tokens_dict.items():
                if value <= 0:
                    continue
                cell_text += f"<div style=\"display: flex; flex-direction: column; align-items: center; justify-content: center;\"><img src=\"{util.get_gl_token_dict()[token_type]}\" height=\"24\" width=\"24\" />"
                cell_text += f"<div>{value}</div>"
                cell_text += "</div>"

            cell_text += "</div>"

            cells.append(hte.Cell(cell_text))

        return cells
    
    def to_tr(self, command_info):
        if command_info['speed']['scenario_id'] != 3:
            return ""

        return super().to_tr(command_info)
    

class RainbowCountRow(hte.Row):
    long_name = "Rainbow count"
    short_name = "Rainbows"
    description = "Shows the total number of rainbows on each facility."

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        for command in game_state.values():
            cells.append(hte.Cell(command['rainbow_count']))

        return cells


class PartnerCountSettings(se.Settings):
    def __init__(self):
        self.s_highlight_max = se.Setting(
            "Highlight max",
            "Highlights the facility with the most training partners.",
            True,
            se.SettingType.BOOL
        )
        self.s_highlight_max_color = se.Setting(
            "Highlight max color",
            "The color to use to highlight the facility with the most training partners.",
            "#90EE90",
            se.SettingType.COLOR
        )


class PartnerCountRow(hte.Row):
    long_name = "Training partner count"
    short_name = "Partners"
    description = "Shows the total number of training partners on each facility. This includes partners that don't give extra stats when training together."

    def __init__(self):
        super().__init__()
        self.settings = PartnerCountSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        highest_partner_count = max(command['partner_count'] for command in game_state.values())

        for command in game_state.values():
            if self.settings.s_highlight_max.value and highest_partner_count > 0 and command['partner_count'] == highest_partner_count:
                cells.append(hte.Cell(command['partner_count'], bold=True, color=self.settings.s_highlight_max_color.value))
            else:
                cells.append(hte.Cell(command['partner_count']))

        return cells


class UsefulPartnerCountSettings(se.Settings):
    def __init__(self):
        self.s_highlight_max = se.Setting(
            "Highlight max",
            "Highlights the facility with the most useful training partners.",
            True,
            se.SettingType.BOOL
        )
        self.s_highlight_max_color = se.Setting(
            "Highlight max color",
            "The color to use to highlight the facility with the most useful training partners.",
            "#90EE90",
            se.SettingType.COLOR
        )

class UsefulPartnerCountRow(hte.Row):
    long_name = "Useful training partner count"
    short_name = "Useful<br>Partners"
    description = "Shows the number of useful training partners on each facility. Useful partners are any that give extra stats when training together."

    def __init__(self):
        super().__init__()
        self.settings = UsefulPartnerCountSettings()

    def _generate_cells(self, game_state) -> list[hte.Cell]:
        cells = [hte.Cell(self.short_name, title=self.description)]

        highest_useful_partner_count = max(command['useful_partner_count'] for command in game_state.values())

        for command in game_state.values():
            if self.settings.s_highlight_max.value and highest_useful_partner_count > 0 and command['useful_partner_count'] == highest_useful_partner_count:
                cells.append(hte.Cell(command['useful_partner_count'], bold=True, color=self.settings.s_highlight_max_color.value))
            else:
                cells.append(hte.Cell(command['useful_partner_count']))

        return cells


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
    PARTNER_COUNT = PartnerCountRow
    USEFUL_PARTNER_COUNT = UsefulPartnerCountRow
    RAINBOW_COUNT = RainbowCountRow
    GL_TOKENS = GrandLiveTokensDistributionRow
    GL_TOKENS_TOTAL = GrandLiveTotalTokensRow
    GM_FRAGMENTS = GrandMastersFragmentsRow


class DefaultPreset(hte.Preset):
    name = "Default"
    rows = [
        RowTypes.GL_TOKENS,
        RowTypes.GM_FRAGMENTS,
        RowTypes.CURRENT_STATS,
        RowTypes.GAINED_STATS,
        RowTypes.USEFUL_BOND,
        RowTypes.GAINED_SKILLPT,
        RowTypes.FAIL_PERCENTAGE,
    ]
