from argparse import ArgumentParser
P = ArgumentParser(description="Read a decklist txt file and write a CSV file with various information")
P.add_argument('filename', help='decklist filename')

args = P.parse_args()


import pandas as pd
import json
import requests
from alive_progress import alive_bar

cleaner = {'Snow Artifact': 'Artifact', 'Basic Snow Land': 'Land', 'Snow Land': 'Land', 'Land Creature': 'Creature',
     'Snow Creature': 'Creature', 'Snow Instant': 'Instant', 'Snow Sorcery': 'Sorcery',
     'Tribal Sorcery': 'Sorcery','Tribal Instant': 'Instant', 'Tribal Enchantment': 'Enchantment',
     'Tribal Artifact': 'Artifact', 'Artifact Creature': 'Creature', 'Snow Enchantment': 'Enchantment',
     'Enchantment Artifact': 'Artifact', 'Enchantment Creature': 'Creature',
    'World Enchantment': 'Enchantment', 'Enchant World': 'Enchantment', 'Basic Land': 'Land'}

def nonblank_lines(f):
    for l in f:
        line = l.rstrip()
        if line:
            yield line

def read_deck(filename):
    """File format:
    The deck are formated like the following:
    NUM CARDNAME (Main board)

    NUM CARDNAME (Sideboard)
    """
    with open(filename, 'r') as f:
        file = f.read().split("\n")
        deck = []
        for line in nonblank_lines(file):
            i = line.index(" ")
            num = int(line[:i])
            card = line[i + 1:]
            deck.append((card,num))      
    return(deck)

def get_scryfall_data(deck_list):
    repo=pd.DataFrame()
    with alive_bar(len(deck_list),bar = 'smooth', spinner = 'classic') as bar:
        for card in deck_list:
            response=requests.get('https://api.scryfall.com/cards/search?q=!"{}"+cheapest:usd'.format(card[0]))
            results=response.json()
            if results['data'][0]['set'] == 'sum':
                response=requests.get('https://api.scryfall.com/cards/search?q=!"{}"+e:3ed'.format(card[0]))
                results=response.json()
            card_name=results['data'][0]['name']
            reserved = results['data'][0]['reserved']
            set_name=results['data'][0]['set_name']
            set_tckr=results['data'][0]['set']
            if len(results['data'][0]['color_identity'])==0:
                color =['X']
            elif len(results['data'][0]['color_identity'])>1:
                color =['M']
            else:
                color=results['data'][0]['color_identity']
            cmc=results['data'][0]['cmc']
            type_line=results['data'][0]['type_line']
            if results['data'][0]['prices']['usd'] is None:
                usd = results['data'][0]['prices']['usd_foil']
            else:
                usd=results['data'][0]['prices']['usd']
            df=pd.DataFrame({'card_name':[card_name],'reserved':reserved,'set':set_tckr,'set_name':set_name,'color': color,'cmc': cmc,'type': type_line,'qty':card[1],'usd':float(usd)})
            repo=repo.append(df,ignore_index=True)
            bar()
    repo.type = repo.type.str.replace(r'Legendary ', '')
    repo.type = [i.partition(' —')[0] for i in repo.type]
    repo.type = repo.type.map(cleaner).fillna(repo.type)
    repo.type = repo.type.str.replace(r"\/\/\s\w+", '', regex=True)
    return repo


print('*******************************')
print('Reading file:',args.filename)
print('*******************************')
deck = read_deck(args.filename)
print('*******************************')
print('Getting the Scryfall data')
print('*******************************')
repo = get_scryfall_data(deck)
print('*******************************')
print('Writing the CSV file')
print('*******************************')
repo.to_csv(args.filename.replace('txt', 'csv'))
print('*******************************')
print('Done')
print('*******************************')