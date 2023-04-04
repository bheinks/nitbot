import pickle
from collections import defaultdict
from pathlib import Path
from sys import exit

BIBLE_PLAINTEXT = Path('bible_en.txt')
BIBLE_PICKLE = Path('bible_en.pickle')


class BibleIndex(defaultdict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def add(self, word):
        index = tuple(sorted(word))
        self[index].add(word)
    
    def find(self, word):
        index = tuple(sorted(word))
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
        
    
if __name__ == '__main__':
    exit(main())