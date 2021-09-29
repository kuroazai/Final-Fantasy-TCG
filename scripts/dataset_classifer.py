# -*- coding: utf-8 -*-
"""
Created on Tue Sep 28 15:53:23 2021

@author: KuroAzai
"""

import database
import json


def namestr(obj, namespace):
    return [name for name in namespace if namespace[name] is obj]


def classify():
    # pull from data base
    results = database.DB.retrieve_query('effect')

    # classify effects by their classification
    forwards = [x for x in results if 'Choose 1 Forward' in x[0]]
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

    # compile all variables into a list and
    names = [forwards,
             dullforwards,
             backups,
             exburst,
             special1,
             special2,
             brave,
             entersfield,
             leavesfield,
             search,
             dealit,
             itgains,
             intobreakzone]

    # empty dict to store our automated classification
    data = {'items': []}
    for x in names:
        intent = namestr(x, locals())
        print(intent[0])
        if x:
            for item in x:
                feat = {'text': '', 'intent': ''}
                feat['text'] = item[0]
                feat['intent'] = intent[0]
                data['items'].append(feat)

    # print(len(data['items']))
    # save it to json file
    with open('dataset.json', 'w') as json_file:
        json.dump(data, json_file)


def main():
    classify()


if __name__ == "__main__":
    main()
