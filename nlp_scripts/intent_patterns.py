import re


def classify_card_intents(card_description: str):
    intents = []
    results = card_description.strip()

    patterns = {
        r'Haste': 'Haste',
        r'First Strike': 'First Strike',
        r'Brave': 'Brave',
        r'Deal it ([^"]*) damage': 'Deal it damage',
        r'If you control ([^"]*),': 'Control Ally',
        r'gains +([^"]*) power': 'Gains Power',
        r'For each Forward opponent controls': 'For Each Forward',
        r'When ([^"]*) deals damage to your opponent': 'Deal it',
        r'choose ([^"]*) dull Forward': 'Dulls Forward',
        r'EX BURST': 'EX Burst',
        r'When ([^"]*) enters the field': 'Enters Field',
        r'When ([^"]*) leaves the field': 'Leaves Field',
        r'choose ([^"]*) Forward': 'Choose Forward',
        r'choose ([^"]*) Backup': 'Choose Forward',
        r'choose up to ([^"]*) Forwards opponent controls': 'Target Opponent Forwards',
        r'discard ([^"]*) card': 'Discard Activation',
        r'Dull them and Freeze them': 'Dull and Freeze',
        r'Break it': 'Break It',
        r'You can only use this ability during your turn': 'Player Turn Only'
    }

    for pattern, intent in patterns.items():
        matches = re.findall(pattern, results)
        if matches:
            intents.append(intent)

    return intents
