import nltk
from nltk.tokenize import sent_tokenize
from nlp_scripts import intent_patterns


def process_text(input_text) -> dict:

    intents = intent_patterns.classify_card_intents(input_text)
    data = {
        'text': input_text,
        'intent': intents
    }

    return data


def process_card_description(card_desc: str) -> list:

    card_tokens = sent_tokenize(card_desc)
    data = nltk.pos_tag(card_tokens)

    output = []
    for sentence in data:
        if sentence:
            data = process_text(sentence[0].strip())
            if data['intent']:
                output.append(data)
            # output.append(process_text(sentence[0].strip()))

    return output


if __name__ == "__main__":

    example_str = '''
                  If you control [Card Name (Aerith)], Zack gains +2000 power.
                  When Zack enters the field, choose 1 Forward opponent controls. Deal it 2000 damage.
                  '''

    response = process_card_description(example_str)
    print(response)
