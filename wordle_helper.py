import os
from collections import defaultdict


class WordleHelper:
    @staticmethod
    def load_words(max_words: int, max_word_len: int, path: str = 'resources/unigram_freq.csv') -> (list, defaultdict):
        valid_words = []
        english_word_frequencies = defaultdict(int)

        # Load the word-frequency dictionary
        dict_path = os.path.join(os.getcwd(), path)
        with open(dict_path, 'r') as f:
            for i, line in enumerate(f):
                if i >= max_words: break
                word, freq = str(line).strip().split(sep=',')
                if len(word) != max_word_len: continue

                valid_words.append(word)
                english_word_frequencies[word] = int(freq)

        return valid_words, english_word_frequencies

    @staticmethod
    def normalize_values(d: defaultdict) -> (defaultdict, list):
        if len(d) <= 0: return d, []

        # Sort the values in the dict and take the max in order to normalize
        sorted_items = sorted(d.items(), key=lambda item: item[1], reverse=True)
        max_val = sorted_items[0][1]

        # Normalize values in the dict
        for k in d.keys():
            d[k] /= max_val

        return d, sorted_items

    @staticmethod
    def print_top_k(scores, label, k=3, suppress_output=False):
        if len(scores) <= 0 or suppress_output: return
        print("\nTop {} {}:".format(min(k, len(scores)), label))
        for key, score in scores[:k]:
            print("{}: {:.3f}".format(key, score))
