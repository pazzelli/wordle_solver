import os
from collections import defaultdict


class WordleHelper:
    @staticmethod
    def load_words(path: str = 'resources/word_frequencies.csv') -> defaultdict:
        english_word_frequencies = defaultdict(int)

        # Load the word-frequency dictionary
        dict_path = os.path.join(os.getcwd(), path)
        with open(dict_path, 'r') as f:
            for i, line in enumerate(f):
                word, freq = str(line).strip().split(sep=',')
                english_word_frequencies[word] = int(freq)

        return english_word_frequencies

    @staticmethod
    def normalize_values(d: dict, max_value: int = None, norm_to_middle=False) -> (defaultdict, list):
        if len(d) <= 0: return d, []

        if norm_to_middle:
            # Normalize values in the dict
            for k in d.keys():
                d[k] /= max_value
                # This magic formula makes items that makes items appearing in the center of the distribution (after
                #  dividing by max_value) get the highest score -> i.e. it makes items having a score of 0.5 get moved
                #  up to a score of 1.0, and items having a score close to 0 or close to 1.0 get moved to 0.0
                # This is useful to produce a binary search-like behaviour wherein letters appearing in exactly
                #  half the remaining words are prioritized highly, so that half of the remaining possible words
                #  can be eliminated on each subsequent guess
                d[k] = 1.0 - (2 * abs(d[k] - 0.5))

            # Sort the values in the dict and take the max in order to normalize
            sorted_items = sorted(d.items(), key=lambda item: item[1], reverse=True)
            return d, sorted_items

        else:
            # Sort the values in the dict and take the max in order to normalize
            sorted_items = sorted(d.items(), key=lambda item: item[1], reverse=True)
            if not max_value:
                max_value = sorted_items[0][1]

            # Normalize values in the dict
            for k in d.keys():
                d[k] /= max_value

            return d, sorted_items

    @staticmethod
    def print_top_k(scores, label, k=3, suppress_output=False):
        if len(scores) <= 0 or suppress_output: return
        print("\nTop {} {}:".format(min(k, len(scores)), label))
        for key, score in scores[:k]:
            print("{}: {:.3f}".format(key, score))
