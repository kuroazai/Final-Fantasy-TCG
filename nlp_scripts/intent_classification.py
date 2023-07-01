import nltk
from nltk.tokenize import sent_tokenize
import re


def classify_card_intents(card_description: str):
    intents = []
    results = card_description.strip()

    patterns = {
        r'Haste': 'Haste',
        r'First Strike': 'First Strike',
        r'Brave': 'Brave',
        r'Deal it ([^"]*) damage': 'Deal Damage',
        r'If you control ([^"]*),': 'Control Ally',
        r'gains +([^"]*) power': 'Gains Power',
        r'For each Forward opponent controls': 'For Each Forward',
        r'When ([^"]*) deals damage to your opponent': 'Deal it',
        r'choose ([^"]*) dull Forward': 'Dulls Forward',
        r'EX BURST': 'EX Burst',
        r'When ([^"]*) enters the field': 'Enters Field',
        r'When ([^"]*) leaves the field': None,  # Not specified in the code
        r'choose ([^"]*) forward': 'Choose Forward',
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


if __name__ == "__main__":

    example_str = '''
                  If you control [Card Name (Aerith)], Zack gains +2000 power.
                  When Zack enters the field, choose 1 Forward opponent controls. Deal it 2000 damage.
                  '''

    data = sent_tokenize(example_str)
    data = nltk.pos_tag(data)

    intents_all = {'Enters Field': [],
                   'Target Opponent Forwards': [],
                   'Discard Activation': [],
                   'Choose Forward': [],
                   'Dull and Freeze it': [],
                   'Break It': [],
                   'EX Burst': [],
                   'Player Turn Only': []}

    card_intents = classify_card_intents(example_str)
    print(card_intents)
    print(data)
