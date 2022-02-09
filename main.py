import argparse
from wordle_solver import WordleSolver
from wordle_optimizer import WordleOptimizer


def main() -> int:
    parser = argparse.ArgumentParser(description='Solve today\'s Wordle!')
    parser.add_argument('--hard_mode', dest='hard_mode', action='store_true',
                        help='hard mode (program can only choose a guess from the remaining list of possible words')
    # parser.add_argument('--optimize', dest='optimize', action='store_true',
    parser.add_argument('--optimize', nargs='?', const=50, type=int, default=0,
                        help='run model optimizer using random parameter values for N iterations (default: 50)')
    args = parser.parse_args()

    # Init solver and start the game!
    if args.optimize:
        WordleOptimizer.optimize_scoring_model(args.hard_mode, args.optimize)
        return 0
    else:
        return WordleSolver(hard_mode=args.hard_mode).play_game()


if __name__ == "__main__":
    main()
