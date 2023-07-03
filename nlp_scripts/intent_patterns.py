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
        r'You can only use this ability during your turn': 'Player Turn Only',
        r'Add it to your hand': 'Add to Hand',
        r'is also Card Name': 'Card Name',
        r'onto the field': 'onto the Field',
        r'The cost required to cast ([^"]*) is reduced by ([^"]*) for every ([^"]*) cards in your Break Zone': 'Cost Reduction',
        r'Remove ([^"]*) Backups from the game: Choose ([^"]*) Forward': 'Discard Backups',
        r'Add up to 5 Forwards': 'Add Forwards',
        r'Break Zone': 'Break Zone',
        r'cannot leave the field': 'Cannot Leave Field',
        r'produce CP': 'Produce CP',
        r'If ([^"]*) is on the field': 'If On Field',
        r"Return them to their owners' hands": 'Return to Hand',
        r'Choose up to ([^"]*) Forwards': 'Choose Forwards',
        r'Break them': 'Break Them',
        r'Activate': 'Activate',
        r'all the Forwards': 'All Forwards',
        r'all the Backups': 'All Backups',
        r'Choose ([^"]*) Character of cost ([^"]*) or less': 'Choose Character',
        r'Choose': 'Choose',
        r'Select up to': 'Select Actions',
        r"Put it on top of its owner's deck": 'Put on Top of Deck',
        r'Play up to 1 Character': 'Play Character',
        r'return the other cards to the bottom of your deck in any order': 'Return to Deck',
        r'into the Damage Zone': 'into Damage Zone',
        r'You can play ([^"]*) or more': 'Play n or More',
        r'Summons': 'Summons',
        r'abilities': 'Abilities',
        r'If': 'conditional',
        r'the damage becomes': 'damage modifier',
        r'cancel': 'cancel',
        r'ability': 'ability',


    }

    for pattern, intent in patterns.items():
        matches = re.findall(pattern.lower(), results.lower())
        if matches:
            intents.append(intent)

    return intents
