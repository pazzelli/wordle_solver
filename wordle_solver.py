from itertools import compress
from collections import defaultdict
from wordle_helper import WordleHelper

MAX_GUESSES = 6

optimal_score_settings = {
    False: (2.287, 1.628, 0.653, 0.017, 0.409),
    True: (1.053, 1.808, 1.219, 0.748, 0)
}

INIT_WORD_FREQ_CACHE = {}


class WordleSolver:
    def __init__(
            self,
            hard_mode: bool = True,
            # The scoring multiplier to apply to base letter frequency score values (anywhere in each word)
            letter_freq_score_factor: float = None,

            # The scoring multiplier to apply to base letter frequency score values (in specific positions in each word)
            letter_pos_freq_score_factor: float = None,

            # The scoring multiplier to apply to the base word frequency score in the English language
            eng_word_freq_score_factor: float = None,

            # The scoring multiplier to apply to letter scores for YELLOW letters (i.e. it exists in the target
            #   word, but the exact position is unknown
            incorrect_pos_letter_score_factor: float = None,

            # The scoring multiplier to apply to base letter frequency score values
            best_word_score_cutoff_factor: float = None,

            # Do not display terminal output (useful when optimizing the scoring model)
            suppress_output: bool = False
    ):
        self.tries = 0
        self.max_tries = MAX_GUESSES
        self.correctly_guessed = False
        self.hard_mode = hard_mode
        self.suppress_output = suppress_output

        self.incorrectly_placed_letters = dict()
        self.correctly_placed_letters = dict()
        self.required_letter_counts_exact = defaultdict(int)
        self.required_letter_counts_min = defaultdict(int)
        self.guessed_words = set()
        self.eliminated_word_count = 0

        self.letter_freq_score_factor = letter_freq_score_factor if letter_freq_score_factor else optimal_score_settings[hard_mode][0]
        self.letter_pos_freq_score_factor = letter_pos_freq_score_factor if letter_pos_freq_score_factor else optimal_score_settings[hard_mode][1]
        self.eng_word_freq_score_factor = eng_word_freq_score_factor if eng_word_freq_score_factor else optimal_score_settings[hard_mode][2]
        self.incorrect_pos_letter_score_factor = incorrect_pos_letter_score_factor if incorrect_pos_letter_score_factor else optimal_score_settings[hard_mode][3]
        self.best_word_score_cutoff_factor = best_word_score_cutoff_factor if best_word_score_cutoff_factor else optimal_score_settings[hard_mode][4]

        self.remaining_words = WordleSolver.load_words()

        if not self.suppress_output:
            print("\n*** Wordle Solver - {} mode ***".format('HARD' if self.hard_mode else 'EASY'))

    @staticmethod
    def load_words() -> dict:
        global INIT_WORD_FREQ_CACHE
        if INIT_WORD_FREQ_CACHE:
            return INIT_WORD_FREQ_CACHE.copy()

        words_and_frequencies = WordleHelper.load_words()
        WordleHelper.normalize_values(words_and_frequencies)
        INIT_WORD_FREQ_CACHE = words_and_frequencies.copy()
        return words_and_frequencies

    def is_game_won(self):
        return self.correctly_guessed

    def is_game_lost(self):
        return self.tries >= self.max_tries

    def _calc_letter_and_position_scores(self) -> (defaultdict, defaultdict):
        # Count occurrences of each letter in all words
        letter_scores = defaultdict(float)
        position_scores = defaultdict(lambda: defaultdict(float))
        incorrectly_placed_letter_set = set(self.incorrectly_placed_letters.values())

        for word in self.remaining_words:
            seen_letters = set()
            for i, c in enumerate(word):
                # Skip any letter in a GREEN position - they shouldn't add weight to the scoring since they will exist
                # in every remaining word, and doing so makes them more likely to appear in undetermined positions
                # (duplicate letters become the norm rather than the exception)
                if i in self.correctly_placed_letters: continue

                score_val = self.incorrect_pos_letter_score_factor if c in incorrectly_placed_letter_set else 1.0
                position_scores[i][c] += score_val
                if c not in seen_letters:
                    letter_scores[c] += score_val
                    seen_letters.add(c)

        # print(list(letter_scores.items()))
        # print("total words: {}".format(len(self.remaining_words)))

        # Normalize frequencies of each letter
        letter_scores, sorted_letter_frequencies = WordleHelper.normalize_values(letter_scores, len(self.remaining_words), norm_to_middle=True)
        WordleHelper.print_top_k(sorted_letter_frequencies, label='letter frequencies', k=15, suppress_output=self.suppress_output)
        # WordleHelper.print_top_k(sorted_letter_frequencies, label='letter frequencies', k=8, suppress_output=self.suppress_output)

        # Normalize letter-position distributions
        for i in position_scores.keys():
            _, sorted_position_frequencies = WordleHelper.normalize_values(position_scores[i], len(self.remaining_words), norm_to_middle=True)
            # WordleHelper.print_top_k(sorted_position_frequencies, label='letter position #{} frequencies'.format(i+1), k=10, suppress_output=self.suppress_output)

        return letter_scores, position_scores

    # Score words based on letter frequencies + how likely each letter is to appear in its position within the word
    # Don't score duplicate letters more than once - this prioritizes words with more unique letters
    def _score_word(self, word: str, letter_scores: defaultdict, position_scores: defaultdict, word_frequencies: dict) -> float:
        if word in self.guessed_words:
            return 0.0

        # 1. Score this word based on its use frequency in the English language (more frequently-used words in
        #   English are given slightly higher scores).  This is mainly used for tie-breaking
        word_freq_score = word_frequencies[word] * self.eng_word_freq_score_factor

        letter_score = 0.0
        position_score = 0.0
        used_letters = set()
        for i, letter in enumerate(word):
            # 2. Score each letter based on its frequency within the remaining set of words
            #   but don't score duplicate letters more than once
            if letter not in used_letters:
                # score += letter_scores[letter] * self.letter_freq_score_factor
                letter_score += letter_scores[letter]
                used_letters.add(letter)

            # 3. Score based on likelihood of each letter appearing in each position within the remaining word set
            # score += position_scores[i][letter] * self.letter_pos_freq_score_factor
            position_score += position_scores[i][letter]

        return word_freq_score + (letter_score * self.letter_freq_score_factor) + (position_score * self.letter_pos_freq_score_factor)

    def _calc_word_scores(self):
        letter_scores, position_scores = self._calc_letter_and_position_scores()

        # Score remaining words first based on all 3 scoring components
        # rem_word_scores = dict(map(lambda w: (w, self._score_word(w, letter_scores, position_scores, self.remaining_word_frequencies)), self.remaining_words))
        rem_word_scores = dict(map(lambda w: (w, self._score_word(w, letter_scores, position_scores, self.remaining_words)), self.remaining_words))
        rem_sorted_word_scores = sorted(filter(lambda t: t[1] > 0, rem_word_scores.items()), key=lambda item: item[1], reverse=True)

        # If playing in hard mode, we can only guess from this list
        # If in easy mode, choose from this list when only 1-2 choices remain, or if one word is a clear winner
        if self.hard_mode or len(self.remaining_words) <= 2 or rem_sorted_word_scores[0][1] >= (rem_sorted_word_scores[1][1] * (1 + self.best_word_score_cutoff_factor)):
            # print("\n*** CHOSE FROM REMAINING LIST ***")
            return rem_sorted_word_scores, None

        # For 'easy' mode where there is no clear winning remaining word, choose a word from the larger / initial list
        #  In that case, use the letter frequencies from just the remaining words (try to eliminate as many remaining
        #  words as possible) but use word frequencies from the initial list and ignore position frequencies entirely
        # all_word_scores = dict(map(lambda w: (w, self._score_word(w, letter_scores, defaultdict(lambda: defaultdict(float)), INIT_WORD_FREQ_CACHE[self.word_len])), INIT_WORD_CACHE[self.word_len]))

        all_word_scores = dict(map(lambda w: (w, self._score_word(w, letter_scores, position_scores, INIT_WORD_FREQ_CACHE)), INIT_WORD_FREQ_CACHE.keys()))
        all_sorted_word_scores = sorted(filter(lambda t: t[1] > 0, all_word_scores.items()), key=lambda item: item[1], reverse=True)
        # print("\n*** CHOSE FROM COMPLETE LIST ***")

        return rem_sorted_word_scores, all_sorted_word_scores

    def _process_feedback(self, guessed_word, wrongly_placed_letter_positions, correctly_placed_letter_positions):
        self.guessed_words.add(guessed_word)

        total_letter_counts_observed = defaultdict(int)
        temp_letter_set = set()
        total_correctly_placed = 0

        for i, letter in enumerate(guessed_word):
            if i+1 in wrongly_placed_letter_positions:
                # these can accumulate between guesses
                self.incorrectly_placed_letters[i] = letter
                total_letter_counts_observed[letter] += 1

            elif i+1 in correctly_placed_letter_positions:
                # these can accumulate between guesses
                self.correctly_placed_letters[i] = letter
                total_letter_counts_observed[letter] += 1
                total_correctly_placed += 1

            else:
                # Temporarily track grey / invalid letters to process on next pass
                temp_letter_set.add(letter)

        # Now process the grey letters since the observed letter counts have been tallied up
        # The total # of each of these letters can be inferred from how many appeared in correct / incorrect positions
        # within the word (yellow or green tiles) - this is how duplicate letters can be properly handled
        for letter in temp_letter_set:
            self.required_letter_counts_exact[letter] = total_letter_counts_observed[letter]

        # Can also infer that the minimum # of a given letter must be equal to the total # of yellow + green
        # instances of that letter
        for letter in total_letter_counts_observed:
            self.required_letter_counts_min[letter] = max(total_letter_counts_observed[letter], self.required_letter_counts_min[letter])

        if total_correctly_placed >= len(guessed_word):
            self.correctly_guessed = True

        # Now eliminate words based on the cumulative feedback from all previous guesses
        if not self.is_game_won():
            self._eliminate_words(guessed_word)

    def _calc_remaining_word_frequencies(self):
        for word in self.remaining_words:
            self.remaining_words[word] = INIT_WORD_FREQ_CACHE[word]
        WordleHelper.normalize_values(self.remaining_words)

    def _is_valid_word(self, word) -> bool:
        letter_counts = defaultdict(int)
        for i, letter in enumerate(word):
            # Track the total # of each letter observed in this word
            letter_counts[letter] += 1

            # Ensure green letters are found in this word exactly
            if i in self.correctly_placed_letters and self.correctly_placed_letters[i] != letter:
                return False

            # Ensure that this word does not contain a misplaced letter in a yellow space (i.e. does not
            # place another L onto a yellow L space)
            if i in self.incorrectly_placed_letters and self.incorrectly_placed_letters[i] == letter:
                return False

        # Ensure this word contains at least the same number of yellow + green letters observed so far
        for letter in self.required_letter_counts_min:
            if letter_counts[letter] < self.required_letter_counts_min[letter]:
                return False

        # One final check to ensure all the known letter counts have been observed exactly in this word
        for letter in self.required_letter_counts_exact:
            if letter_counts[letter] != self.required_letter_counts_exact[letter]:
                return False

        # Keep tracking this word only if all checks above are passed
        return True

    def _eliminate_words(self, guessed_word: str):
        # Produce new list of remaining words by removing the guessed word and filtering down to only those
        # that are still valid based on the new feedback
        new_remaining_words = dict(compress(self.remaining_words.items(), map(lambda w: w != guessed_word and self._is_valid_word(w), self.remaining_words)))

        self.eliminated_word_count = len(self.remaining_words) - len(new_remaining_words)
        self.remaining_words = new_remaining_words

        # Update calcs of word frequencies for remaining words only
        self._calc_remaining_word_frequencies()

        # if not self.suppress_output:
        #     print("\n*** {} words remaining ({} eliminated) ***".format(len(self.remaining_words), eliminated_word_count))

    def _make_guess(self):
        # Score the words & print out the top K
        rem_word_scores, all_word_scores = self._calc_word_scores()
        WordleHelper.print_top_k(rem_word_scores, label='remaining word scores', k=10, suppress_output=self.suppress_output)
        if all_word_scores:
            WordleHelper.print_top_k(all_word_scores, label='all word scores', k=10, suppress_output=self.suppress_output)

        self.tries += 1

        if not self.suppress_output:
            print("\n*** {} words remaining ({} eliminated) ***".format(len(self.remaining_words), self.eliminated_word_count))

        # Return the best word, if at least 1 remains
        return all_word_scores[0][0] if all_word_scores else (rem_word_scores[0][0] if len(rem_word_scores) > 0 else None)

    def play_game(self) -> int:
        while True:
            best_guess: str = self._make_guess()
            if not best_guess:
                print("\n**** ERROR: NO WORDS REMAINING ****\n")
                return -1

            print("\nBest guess: {}\n".format(best_guess.upper()))

            wrongly_placed_letter_positions = input("Input positions of YELLOW letters (valid but in wrong place) - e.g. \"2 5\"\n  start from 1, separate by a space (or press ENTER for none):\n")
            wrongly_placed_letter_positions = list(map(int, filter(lambda w: len(w) > 0, wrongly_placed_letter_positions.split())))

            correctly_placed_letter_positions = input("\nInput positions of GREEN letters (valid and in correct place) - e.g. \"2 5\"\n  start from 1, separate by a space (or press ENTER for none):\n")
            correctly_placed_letter_positions = list(map(int, filter(lambda w: len(w) > 0, correctly_placed_letter_positions.split())))

            self._process_feedback(best_guess, wrongly_placed_letter_positions, correctly_placed_letter_positions)

            if self.is_game_won():
                print("\n *** YOU WIN!! - {} ***".format(best_guess.upper()))
                return 0

            if self.is_game_lost():
                print("\n *** YOU LOSE!! *** - Too many tries")
                return 0

