# -*- coding: utf-8 -*-
"""
Created on Sun Sep 19 20:05:08 2021

@author: KuroAzai
"""
import nltk
from nltk.tokenize import sent_tokenize
import re

example_str = '''
              If you control [Card Name (Aerith)], Zack gains +2000 power.
              When Zack enters the field, choose 1 Forward opponent controls. Deal it 2000 damage.
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
        haste = re.findall('Haste', str(results))
        firststrike = re.findall('First Strike', str(results))
        brave = re.findall('Brave', str(results))
        dealit = re.findall('Deal it ([^"]*) damage', str(results))
        controllally = re.findall('If you control ([^"]*),', str(results))
        gainspwr = re.findall('gains +([^"]*) power,', str(results))
        foreachforward = re.findall(
            'For each Forward opponent controls', str(results))
        dealsdamage = re.findall(
            'When ([^"]*) deals damage to your opponent', str(results))
        dullforward = re.findall('choose ([^"]*) dull Forward', str(results))

        exburst = re.findall('EX BURST', str(results))
        entersfield = re.findall('When ([^"]*) enters the field', str(results))
        leavesfield = re.findall('When ([^"]*) leaves the field', str(results))

        forwards = re.findall('Choose ([^"]*) Forward', str(results))
        oppforwards = re.findall(
            'choose up to ([^"]*) Forwards opponent controls', str(results))
        discardactivation = re.findall('discard ([^"]*) card', str(results))
        dullandfreeze = re.findall('Dull them and Freeze them', str(results))
        breakit = re.findall('Break it', str(results))
        turnlimit = re.findall(
            'You can only use this ability during your turn', str(results))
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
        print('\n', x[0].strip(),
              '\n', intents)
