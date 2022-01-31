import argparse
from wordle_solver import WordleSolver


def play_game(wordle_solver):
    while True:
        best_guess: str = wordle_solver.make_guess()
        if not best_guess:
            print("\n**** ERROR: NO WORDS REMAINING ****\n")
            break

        print("\nBest guess: {}\n".format(best_guess.upper()))

        wrongly_placed_letter_positions = input("Input positions of YELLOW letters (valid but in wrong place) - e.g. \"2 5\"\n  start from 1, separate by a space (or press ENTER for none):\n")
        wrongly_placed_letter_positions = list(map(int, filter(lambda w: len(w) > 0, wrongly_placed_letter_positions.split())))

        correctly_placed_letter_positions = input("\nInput positions of GREEN letters (valid and in correct place) - e.g. \"2 5\"\n  start from 1, separate by a space (or press ENTER for none):\n")
        correctly_placed_letter_positions = list(map(int, filter(lambda w: len(w) > 0, correctly_placed_letter_positions.split())))

        if len(correctly_placed_letter_positions) >= wordle_solver.word_len:
            print("\n *** YOU WIN!! - {} ***".format(best_guess.upper()))
            break

        if wordle_solver.tries >= wordle_solver.max_tries:
            print("\n *** YOU LOSE!! *** - Too many tries")
            break

        wordle_solver.process_feedback(best_guess, wrongly_placed_letter_positions, correctly_placed_letter_positions)


def main() -> int:
    parser = argparse.ArgumentParser(description='Solve today\'s Wordle!')
    parser.add_argument('--letter_count', nargs='?', const=5, type=int, default=5,
                        help='# of letters in today\'s puzzle (default: 5)')
    args = parser.parse_args()

    # Init solver using words in the text file
    wordle_solver = WordleSolver(args.letter_count)

    play_game(wordle_solver)
    return 0


if __name__ == "__main__":
    main()
