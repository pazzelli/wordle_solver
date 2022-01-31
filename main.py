import argparse
from wordle_solver import WordleSolver


def main() -> int:
    parser = argparse.ArgumentParser(description='Solve today\'s Wordle!')
    parser.add_argument('--letter_count', nargs='?', const=5, type=int, default=5,
                        help='# of letters in today\'s puzzle (default: 5)')
    args = parser.parse_args()

    # Init solver and start the game!
    wordle_solver = WordleSolver(args.letter_count)
    return wordle_solver.play_game()


if __name__ == "__main__":
    main()
