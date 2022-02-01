import os
from collections import defaultdict
from unittest import TestCase

from wordle_solver import WordleSolver


class TestWordleSolver(TestCase):
    @staticmethod
    def get_historical_words(word_len: int = 5, path: str = 'resources/historical_answers.txt') -> list:
        valid_words = []

        # Load the historical words list
        historical_answers_path = os.path.join(os.getcwd(), path)
        with open(historical_answers_path, 'r') as f:
            for i, line in enumerate(f):
                word = str(line).strip()
                if len(word) != word_len: continue
                valid_words.append(word)
        return valid_words

    @staticmethod
    def calc_feedback(word: str, guess_word: str) -> (list, list):
        # Determine which letters are correctly placed (green) or incorrectly placed (yellow)
        # given the target word and guessed word
        wrongly_placed_letter_positions = []
        correctly_placed_letter_positions = []

        # Loop over letters in target word and determine which ones match exactly (green)
        # Track remaining letters in a separate dictionary
        remaining_letter_counts = defaultdict(int)
        for i, letter in enumerate(word):
            if guess_word[i] == letter:
                correctly_placed_letter_positions.append(i + 1)
            else:
                remaining_letter_counts[letter] += 1

        # Loop over letters in guessed word and determine if any should be set to yellow based on the dictionary
        for i, letter in enumerate(guess_word):
            if i + 1 in correctly_placed_letter_positions: continue
            if remaining_letter_counts[letter] > 0:
                wrongly_placed_letter_positions.append(i + 1)
                remaining_letter_counts[letter] -= 1

        return wrongly_placed_letter_positions, correctly_placed_letter_positions

    @staticmethod
    def run_simulation(historical_words, letter_freq_score_factor, letter_pos_freq_score_factor, eng_word_freq_score_factor):
        # Plays a single game of Wordle for each historical word and determines the average # of guesses across
        # all historical words
        # historical_words = TestWordleSolver.get_historical_words()
        guess_counts = []
        failed_words = []

        try:
            for word in historical_words:
                wordle_solver = WordleSolver(word_len=len(word), letter_freq_score_factor=letter_freq_score_factor, letter_pos_freq_score_factor=letter_pos_freq_score_factor, eng_word_freq_score_factor=eng_word_freq_score_factor, suppress_output=True)
                # wordle_solver.play_game()
                # print("\n*** Word is: {}".format(word.upper()))

                for guess_num in range(1, wordle_solver.max_tries + 1):
                    best_guess = wordle_solver._make_guess()
                    if not best_guess:
                        # print("*** No more guesses remaining for word: {} ***".format(word.upper()))
                        guess_counts.append(wordle_solver.max_tries + 5)
                        failed_words.append(word)
                        break
                    # print("Guess word: {}".format(best_guess.upper()))

                    wrongly_placed_letter_positions, correctly_placed_letter_positions = TestWordleSolver.calc_feedback(word, best_guess)
                    wordle_solver._process_feedback(best_guess, wrongly_placed_letter_positions, correctly_placed_letter_positions)

                    if wordle_solver.is_game_won():
                        # print("{} - {} guesses".format(word.upper(), guess_num))
                        guess_counts.append(guess_num)
                        break

                    if wordle_solver.is_game_lost():
                        # print("*** Too many tries for word: {} ***".format(word.upper()))
                        guess_counts.append(wordle_solver.max_tries + 5)
                        failed_words.append(word)
                        break

                # if len(guess_counts) % 100 == 0:
                #     print("\nWords guessed: {}, Avg guess count: {:.4f}\n".format(len(guess_counts), sum(guess_counts) / float(len(guess_counts))))

        except (InterruptedError, KeyboardInterrupt):
            pass

        avg_guess_count = sum(guess_counts) / float(len(guess_counts))
        # print("\nMissing words: {}\n".format(failed_words))
        # print("\nWords guessed: {}, Avg guess count: {:.4f}\n".format(len(guess_counts), avg_guess_count))
        return avg_guess_count, len(failed_words)

    def test_optimize_scoring_model(self):
        # Optimizes the scoring system by trying different weighting values for each of the scoring components
        # Outputs to the console in a CSV format (tab-delimited)
        historical_words = TestWordleSolver.get_historical_words()
        print("\nletter_freq_score_factor\tletter_pos_freq_score_factor\teng_word_freq_score_factor\tavg_guess_count\tfailed_word_count")

        for letter_freq_score_factor in range(2, 5, 1):
            # for letter_pos_freq_score_factor in range(0, 3, 1):
            letter_pos_freq_score_factor = 0.5
            for eng_word_freq_score_factor_loop_var in range(5, 30, 5):
                eng_word_freq_score_factor = float(eng_word_freq_score_factor_loop_var) / 10.0

                # print("\nRunning simulation: letter_freq_score_factor = {:.1f}, letter_pos_freq_score_factor = {:.1f}, eng_word_freq_score_factor = {:.1f} ...".format(letter_freq_score_factor, letter_pos_freq_score_factor, eng_word_freq_score_factor))
                avg_guess_count, failed_word_count = TestWordleSolver.run_simulation(historical_words, letter_freq_score_factor, letter_pos_freq_score_factor, eng_word_freq_score_factor)

                print("{}\t{}\t{}\t{:.4f}\t{}".format(letter_freq_score_factor, letter_pos_freq_score_factor, eng_word_freq_score_factor, avg_guess_count, failed_word_count))

