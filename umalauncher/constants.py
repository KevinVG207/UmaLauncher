SCENARIO_DICT = {
    1: "URA Finals",
    2: "Aoharu Cup",
    3: "Grand Live",
    4: "Make a New Track",
    5: "Grand Masters",
}

MOTIVATION_DICT = {
    5: "Very High",
    4: "High",
    3: "Normal",
    2: "Low",
    1: "Very Low"
}

SUPPORT_CARD_RARITY_DICT = {
    1: "R",
    2: "SR",
    3: "SSR"
}

SUPPORT_CARD_TYPE_DICT = {
    (101, 1): "speed",
    (105, 1): "stamina",
    (102, 1): "power",
    (103, 1): "guts",
    (106, 1): "wiz",
    (0, 2): "friend",
    (0, 3): "group"
}

SUPPORT_CARD_TYPE_DISPLAY_DICT = {
    "speed": "Speed",
    "stamina": "Stamina",
    "power": "Power",
    "guts": "Guts",
    "wiz": "Wisdom",
    "friend": "Friend",
    "group": "Group"
}

SUPPORT_TYPE_TO_COMMAND_IDS = {
    "speed": [101, 601],
    "stamina": [105, 602],
    "power": [102, 603],
    "guts": [103, 604],
    "wiz": [106, 605],
    "friend": [],
    "group": []
}

COMMAND_ID_TO_KEY = {
    101: "speed",
    105: "stamina",
    102: "power",
    103: "guts",
    106: "wiz",
    601: "speed",
    602: "stamina",
    603: "power",
    604: "guts",
    605: "wiz"
}

TARGET_TYPE_TO_KEY = {
    1: "speed",
    2: "stamina",
    3: "power",
    4: "guts",
    5: "wiz"
}

MONTH_DICT = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

GL_TOKEN_LIST = [
    'dance',
    'passion',
    'vocal',
    'visual',
    'mental'
]

ORIENTATION_DICT = {
    True: 's_game_position_portrait',
    False: 's_game_position_landscape',
    's_game_position_portrait': True,
    's_game_position_landscape': False,
}

# Request packets contain keys that should not be kept for privacy reasons.
REQUEST_KEYS_TO_BE_REMOVED = [
    "device",
    "device_id",
    "device_name",
    "graphics_device_name",
    "ip_address",
    "platform_os_version",
    "carrier",
    "keychain",
    "locale",
    "button_info",
    "dmm_viewer_id",
    "dmm_onetime_token",
]

HEROES_SCORE_TO_LEAGUE_DICT = {
    0: "Bronze 1",
    1000: "Bronze 2",
    2000: "Bronze 3",
    3000: "Bronze 4",
    4000: "Silver 1",
    5500: "Silver 2",
    7000: "Silver 3",
    8500: "Silver 4",
    10000: "Gold 1",
    12500: "Gold 2",
    15000: "Gold 3",
    17500: "Gold 4",
    20000: "Platinum 1",
    23000: "Platinum 2",
    26000: "Platinum 3",
    30000: "Platinum 4"
}