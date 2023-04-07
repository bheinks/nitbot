#!/usr/bin/env python3

import argparse
from collections import defaultdict
from pathlib import Path
from sys import exit

import contractions
import discord
import nltk
from decouple import config, UndefinedValueError

DEFAULT_BIBLE_SOURCE_PATH = Path('assets/dictionaries/bible_en.txt')
ACTIVATION_COMMAND = '!nitb'
# TODO: tokenize non-ASCII words for multilingual support
WORD_TOKENIZER = nltk.RegexpTokenizer(r'[a-zA-Z]+')


class NITBot(discord.Client):
    def __init__(self, bible_index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bible_index = bible_index

    async def on_ready(self):
        ready_text = f'Logged in as {self.user} (ID: {self.user.id})'
        print(ready_text)
        print('-' * len(ready_text))

        # Set bot presence
        activity = discord.Activity(type=discord.ActivityType.watching, name='you sin in real-time')
        await self.change_presence(activity=activity)
    
    async def on_message(self, message):
        # Ignore messages from self
        if message.author.id == self.user.id:
            return
        
        # Act on messages starting with activation command
        if message.content.startswith(ACTIVATION_COMMAND):
            # If used in reply to a message, fetch content of original message
            if message.reference is not None and not message.is_system():
                channel = self.get_channel(message.reference.channel_id)
                original = await channel.fetch_message(message.reference.message_id)
                
                # Expand contractions
                content = contractions.fix(original.content)

                # Tokenize and uniquify message content
                words = ordered_set(WORD_TOKENIZER.tokenize(content))
            # Otherwise, use body of message
            else:
                # Expand contractions
                content = contractions.fix(message.content)

                # Tokenize and uniquify message content (excluding activation command)
                words = ordered_set(WORD_TOKENIZER.tokenize(content)[1:])
            
            # Filter only words that aren't found in the bible
            words_not_in_bible = [w for w in words if w not in self.bible_index]
            if len(words) == len(words_not_in_bible):
                response = 'None of these words are in the Bible.'
            elif not words_not_in_bible:
                response = 'All of these words are in the Bible.'
            elif len(words_not_in_bible) == 1:
                response = f'{words_not_in_bible[0]} is not in the Bible.'
            elif len(words_not_in_bible) == 2:
                response = f"{' and '.join(words_not_in_bible)} are not in the Bible."
            else:  # > 2
                response = f"{', '.join(words_not_in_bible[:-1])} and {words_not_in_bible[-1]} are not in the Bible."

            # Add cross reaction to message
            await message.add_reaction('✝️')

            # Reply to message
            await message.reply(response, mention_author=True)


# Store strings in a dictionary whose key is the sorted version of each string, i.e.:
#
# index.add('test')
# index = {
#     ('e', 's', 't', 't'): {'test'}
# }
#
# This allows for queries in average O(1) time.
class SortedIndex(defaultdict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __contains__(self, word):
        word = word.lower()
        index = tuple(sorted(word))
        return word in self[index]

    def add(self, word):
        index = tuple(sorted(word))
        self[index].add(word)


# Helper function that returns a unique, ordered list (as set is an unordered structure)
def ordered_set(items):
    return list(dict.fromkeys(items))
    

def main(args):
    # If Bible source file does not exist, exit program
    if not args.source.exists():
        print(f'ERROR: Bible source file {args.source.as_posix()} not found.')
        return -1
    
    # Parse Bible source
    with args.source.open() as f:
        bible_index = SortedIndex(set)
        for line in f:
            # Strip newline and add to index
            word = line.rstrip()
            bible_index.add(word)
    
    # Get Discord token from args or environment
    try:
        discord_token = args.token or config('DISCORD_TOKEN')
    except UndefinedValueError:
        print('ERROR: Discord token not provided (must be passed in or defined in environment as DISCORD_TOKEN).')
        return -1
    
    # Define bot intents
    intents = discord.Intents.default()
    intents.message_content = True

    # Initialize and run bot
    client = NITBot(bible_index, intents=intents)
    client.run(discord_token)
        
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple Discord bot to tell you if your users' deranged ramblings are holy or not")
    parser.add_argument('-s', '--source', type=Path, default=DEFAULT_BIBLE_SOURCE_PATH,
                        help='newline-delimited bible source file (defaults to KJV in English)')
    parser.add_argument('-t', '--token', type=str,
                        help='Discord token (overrides DISCORD_TOKEN environment variable)')
    args = parser.parse_args()

    exit(main(args))
