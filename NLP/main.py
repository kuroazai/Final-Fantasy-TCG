# -*- coding: utf-8 -*-
"""
Created on Sun Sep 19 20:05:08 2021

@author: KuroAzai
"""
import nltk
from nltk.tokenize import sent_tokenize
import re

example_str = '''
                EX BURST When The Emperor enters the field, choose up to 2 Forwards opponent controls. Dull them and Freeze them.
                , discard 1 card: Choose 1 dull Forward. Break it. You can only use this ability during your turn.

            '''

if __name__ == "__main__":
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

    for x in data:
        intents = []
        results = x[0].strip()
        # classify effects by their classification
        exburst = re.findall('EX BURST', str(results))
        entersfield = re.findall('When ([^"]*) enters the field', str(results))
        forwards = re.findall('Choose ([^"]*) Forward', str(results))
        oppforwards = re.findall('choose up to ([^"]*) Forwards opponent controls', str(results))
        discardactivation = re.findall('discard ([^"]*) card', str(results))
        dullandfreeze = re.findall('Dull them and Freeze them', str(results))
        breakit = re.findall('Break it', str(results))
        turnlimit = re.findall('You can only use this ability during your turn', str(results))
        if exburst:
            intents.append('EX Burst')
        if entersfield:
            intents.append('Enters Field')
        if oppforwards:
            intents.append('Target Opponent Forwards')
        if discardactivation:
            intents.append('Discard Activation')
        if forwards:
            intents.append('Choose Forward')
        if dullandfreeze:
            intents.append('Dull and Freeze')
        if breakit:
            intents.append('Break It')
        if turnlimit:
            intents.append(('Player Turn Only'))
        dullforwards = [x for x in results if 'Choose 1 dull Forward' in x[0]]
        backups = [x for x in results if 'Choose 1 Backup' in x[0]]
        exburst = [x for x in results if 'EX BURST' in x[0]]
        special1 = [x for x in results if 'S1:' in x[0]]
        special2 = [x for x in results if 'S2:' in x[0]]
        brave = [x for x in results if 'Brave' in x[0]]
        entersfield = [x for x in results if 'enters the field' in x[0]]
        leavesfield = [x for x in results if 'from the the field into Break Zone' in x[0]]
        search = [x for x in results if 'search' in x[0]]
        dealit = [x for x in results if 'deal it' in x[0]]
        itgains = [x for x in results if 'it gains' in x[0]]
        intobreakzone = [x for x in results if 'into Break Zone' in x[0]]
        print('\n', x[0].strip(),
              '\n', intents)

