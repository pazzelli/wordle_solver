import os
from collections import defaultdict

MAX_WORDS = 50000
MAX_GUESSES = 6


class WordleSolver:
    def __init__(self, word_len: int):
        self.tries = 0
        self.max_tries = MAX_GUESSES
        self.word_len = word_len
        self.word_frequencies = defaultdict(int)

        self.incorrectly_placed_letters = dict()
        self.correctly_placed_letters = dict()
        self.required_letter_counts = defaultdict(int)

        self.remaining_words = self._init_remaining_words(word_len)
        self.remaining_word_frequencies = self._calc_remaining_word_frequencies()

    def _get_initial_words(self, path: str = 'resources/en_full.txt'):
        valid_words = []
        dict_path = os.path.join(os.getcwd(), path)
        with open(dict_path, 'r') as f:
            for i, line in enumerate(f):
                if i > MAX_WORDS: break
                word, freq = str(line).strip().split()
                if ',' in word or '.' in word or '\'' in word or '-' in word: continue

                valid_words.append(word)
                self.word_frequencies[word] = int(freq)

        return valid_words

    def _init_remaining_words(self, word_len: int):
        preprocessed_words = set()
        for word in self._get_initial_words():
            # remove words that are not of the word length
            if len(word) != word_len: continue
            preprocessed_words.add(word)

        return preprocessed_words

    @staticmethod
    def _normalize_values(d: defaultdict) -> (defaultdict, list):
        # Sort the values in the dict and take the max in order to normalize
        sorted_items = sorted(d.items(), key=lambda item: item[1], reverse=True)
        max_val = sorted_items[0][1]

        # Normalize values in the dict
        for k in d.keys():
            d[k] /= max_val

        return d, sorted_items

    def _calc_letter_and_position_scores(self) -> (defaultdict, defaultdict):
        # Count occurrences of each letter in all words
        letter_scores = defaultdict(float)
        position_scores = defaultdict(lambda: defaultdict(float))

        for word in self.remaining_words:
            for i, c in enumerate(word):
                letter_scores[c] += 1.0
                position_scores[i][c] += 1.0

        # Normalize frequencies of each letter
        letter_scores, sorted_letter_frequencies = WordleSolver._normalize_values(letter_scores)
        self._print_top_k(sorted_letter_frequencies, label='letter frequencies', k=3)

        # Normalize letter-position distributions
        for i in position_scores.keys():
            _, sorted_position_frequencies = WordleSolver._normalize_values(position_scores[i])
            # self._print_top_k(sorted_position_frequencies, label='letter position #{} frequencies'.format(i+1), k=5)

        return letter_scores, position_scores

    def _calc_word_scores(self):
        word_scores = defaultdict(float)
        letter_scores, position_scores = self._calc_letter_and_position_scores()

        # Score words based on letter frequencies + how likely each letter is to appear in its position within the word
        # Don't score duplicate letters more than once - this prioritizes words with more unique letters
        for word in self.remaining_words:
            used_letters = set()
            word_scores[word] += self.remaining_word_frequencies[word]
            for i, letter in enumerate(word):
                if letter not in used_letters:
                    word_scores[word] += letter_scores[letter]
                used_letters.add(letter)

                word_scores[word] += position_scores[i][letter]

        # Sort words by score and return
        sorted_word_scores = sorted(word_scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_word_scores

    def process_feedback(self, guessed_word, wrongly_placed_letter_positions, correctly_placed_letter_positions):
        total_letter_counts_observed = defaultdict(int)
        temp_letter_set = set()

        for i, letter in enumerate(guessed_word):
            if i+1 in wrongly_placed_letter_positions:
                # these can accumulate between guesses
                self.incorrectly_placed_letters[i] = letter
                total_letter_counts_observed[letter] += 1

            elif i+1 in correctly_placed_letter_positions:
                # these can accumulate between guesses
                self.correctly_placed_letters[i] = letter
                total_letter_counts_observed[letter] += 1

            else:
                # Temporarily track grey / invalid letters to process on next pass
                temp_letter_set.add(letter)

        # Now process the grey letters since the observed letter counts have been tallied up
        # The total # of each of these letters can be inferred from how many appeared in correct / incorrect positions
        # within the word (yellow or green tiles) - this is how duplicate letters can be properly handled
        for letter in temp_letter_set:
            self.required_letter_counts[letter] = total_letter_counts_observed[letter]

        # Now eliminate words based on the cumulative feedback from all previous guesses
        self._eliminate_words(guessed_word)

    def _calc_remaining_word_frequencies(self) -> defaultdict:
        self.remaining_word_frequencies = defaultdict(float)
        for word in self.remaining_words:
            self.remaining_word_frequencies[word] = self.word_frequencies[word]
        WordleSolver._normalize_values(self.remaining_word_frequencies)
        return self.remaining_word_frequencies

    def _eliminate_words(self, guessed_word: str):
        new_remaining_words = set()
        for word in self.remaining_words:
            if word == guessed_word: continue   # skip the word that was just guessed

            invalid_word = False
            found_incorrectly_placed_letters = 0
            tracked_incorrectly_placed_letters = set(self.incorrectly_placed_letters.values())
            letter_counts = defaultdict(int)
            for i, letter in enumerate(word):
                letter_counts[letter] += 1

                if i in self.correctly_placed_letters and self.correctly_placed_letters[i] != letter:
                    invalid_word = True
                    break

                if i in self.incorrectly_placed_letters and self.incorrectly_placed_letters[i] == letter:
                    invalid_word = True
                    break

                if letter in tracked_incorrectly_placed_letters:
                    found_incorrectly_placed_letters += 1

            # Ensure all yellow letters are observed somewhere within this word
            if found_incorrectly_placed_letters < len(tracked_incorrectly_placed_letters):
                invalid_word = True

            # One final check to ensure all the known letter counts have been observed exactly in this word
            for letter in self.required_letter_counts:
                if letter_counts[letter] != self.required_letter_counts[letter]:
                    invalid_word = True

            # Keep tracking this word only if all checks above are passed
            if not invalid_word:
                new_remaining_words.add(word)

        eliminated_word_count = len(self.remaining_words) - len(new_remaining_words)
        self.remaining_words = new_remaining_words
        self._calc_remaining_word_frequencies()

        print("\n*** {} words remaining ({} eliminated) ***".format(len(self.remaining_words), eliminated_word_count))

    def make_guess(self):
        word_scores = self._calc_word_scores()
        WordleSolver._print_top_k(word_scores, label='word scores', k=5)

        self.tries += 1
        return word_scores[0][0]

    @staticmethod
    def _print_top_k(scores, label, k=3):
        print("\nTop {} {}:".format(min(k, len(scores)), label))
        for key, score in scores[:k]:
            print("{}: {:.3f}".format(key, score))
