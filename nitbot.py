#!/usr/bin/env python3

import pickle
from collections import defaultdict
from pathlib import Path
from sys import exit

import contractions
import discord
import nltk
from decouple import config, UndefinedValueError

BIBLE_PLAINTEXT = Path('bible_en.txt')
BIBLE_PICKLE = Path('bible_en.pickle')
WORD_TOKENIZER = nltk.RegexpTokenizer(r'[a-zA-Z]+')

try:
    DISCORD_TOKEN = config('DISCORD_TOKEN')
except UndefinedValueError:
    print('ERROR: Environment file not found or DISCORD_TOKEN undefined. Please create a valid settings.ini or .env file with DISCORD_TOKEN defined.')
    exit(-1)


# Helper function that returns a unique, ordered list 
def ordered_set(items):
    return list(dict.fromkeys(items))


class NITBot(discord.Client):
    def __init__(self, bible_index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bible_index = bible_index

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
    
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        
        if message.content.startswith('!nitb'):
            # If used in reply to a message, fetch content of referred message
            if message.reference is not None and not message.is_system():
                channel = self.get_channel(message.reference.channel_id)
                original = await channel.fetch_message(message.reference.message_id)
                content = contractions.fix(original.content)
                words = ordered_set(WORD_TOKENIZER.tokenize(content))
            # Otherwise, use body of message
            else:
                content = contractions.fix(message.content)
                # Exclude !nitb
                words = ordered_set(WORD_TOKENIZER.tokenize(content)[1:])
            
            not_in_bible = [w for w in words if not self.bible_index.find(w)]
            if len(words) == len(not_in_bible):
                response = 'None of these words are in the Bible.'
            elif len(not_in_bible) == 1:
                response = f'{not_in_bible[0]} is not in the Bible.'
            elif len(not_in_bible) == 2:
                response = f"{' and '.join(not_in_bible)} are not in the Bible."
            else:
                response = f"{', '.join(not_in_bible[:-1])} and {not_in_bible[-1]} are not in the Bible."

            # Add cross reaction to message
            await message.add_reaction('✝️')

            # Reply to message
            await message.reply(response, mention_author=True)

class BibleIndex(defaultdict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def add(self, word):
        index = tuple(sorted(word))
        self[index].add(word)
    
    def find(self, word):
        index = tuple(sorted(word.lower()))
        return self[index]


def main():
    # Open existing bible pickle file
    if BIBLE_PICKLE.exists():
        with BIBLE_PICKLE.open('rb') as f:
            bible_index = pickle.load(f)
    # If bible pickle file does not exist, generate from plaintext
    else:
        # If bible plaintext does not exist, exit program
        if not BIBLE_PLAINTEXT.exists():
            print('ERROR: Bible plaintext/pickle files not found.')
            return -1
        
        with BIBLE_PLAINTEXT.open() as f:
            bible_index = BibleIndex(set)
            for line in f:
                word = line.rstrip()
                bible_index.add(word)
        
        # Write index to file
        with BIBLE_PICKLE.open('wb') as f:
            pickle.dump(bible_index, f, pickle.HIGHEST_PROTOCOL)
    
    intents = discord.Intents.default()
    intents.message_content = True

    client = NITBot(bible_index, intents=intents)
    client.run(DISCORD_TOKEN)
        
    
if __name__ == '__main__':
    exit(main())