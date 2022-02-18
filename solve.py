import enum
import numpy as np
import matplotlib.pyplot as plt
import argparse
from english_words import english_words_lower_set

def lowercase_letters():
    return [chr(i) for i in range(97, 97 + 26)]

def contains_only(word, allowable_characters):
    for l in word:
        if l not in allowable_characters:
            return False
    return True

def all_candidate_words(length=5):
    letters = lowercase_letters()
    return [w for w in english_words_lower_set if len(w) == length and contains_only(w, letters)]

class TileStatus(enum.Enum):
    Incorrect = enum.auto()
    PartialMatch = enum.auto()
    Correct = enum.auto()


def entropy(guess, words):
    clue_probs = dict()
    prob = 1.0 / len(words)
    for word in words:
        clue = get_clue(word, guess)
        if clue in clue_probs:
            clue_probs[clue] += prob
        else:
            clue_probs[clue] = prob

    entropy = 0
    for p in clue_probs.values():
        entropy -= p * np.log(p)

    return entropy


def get_clue(word, guess):
    assert len(word) == len(
        guess
    ), f"The guess ({guess}) is {len(guess)} letters, but the solution  ({word}) is {len(word)} letters long."

    clue = []
    for w, g in zip(word, guess):
        status = TileStatus.Incorrect
        if w == g:
            status = TileStatus.Correct
        elif g in word:
            status = TileStatus.PartialMatch
        clue.append((g, status))

    return tuple(clue)


class WordleState:

    def __init__(self):
        self.letters = [set(lowercase_letters()) for _ in range(5)]
        self.correct_letters = set()

    def __str__(self):
        string = "Positions:\n"
        for i, l in enumerate(self.letters):
            string += f"{i}: {sorted(list(l))}\n"
        string += f"Correct letters: {self.correct_letters}"
        return string

    def add_clue(self, clue):
        for i, c in enumerate(clue):
            letter, status = c
            if status == TileStatus.Incorrect:
                assert letter not in self.correct_letters, f"Letter {l} was previously clued to be true."
                for l in self.letters:
                    l.discard(letter)
            elif status == TileStatus.PartialMatch:
                self.letters[i].discard(letter)
                self.correct_letters.add(letter)
            elif status == TileStatus.Correct:
                assert letter in self.letters[
                    i], f"Letter {l} was previously clued NOT to be in position {i}"
                self.letters[i] = set([letter])
                self.correct_letters.add(letter)
            else:
                assert ("Bad TileStatus")

    def matches(self, word):
        if len(word) != len(self.letters):
            return False
        for letter in self.correct_letters:
            if letter not in word:
                return False
        for i, letter in enumerate(word):
            if letter not in self.letters[i]:
                return False
        return True

    def is_solved(self):
        for l in self.letters:
            if len(l) != 1:
                return False
        return True

    def is_impossible(self):
        for l in self.letters:
            if len(l) == 0:
                return True
        return False


class WordleSolver:

    def __init__(self, guess_all_words=False):
        self.guess_all_words = guess_all_words
        self.total_word_set = all_candidate_words()
        self.words = self.total_word_set.copy()
        self.state = WordleState()
        self.update_words()

    def add_clue(self, clue):
        self.state.add_clue(clue)

    def next_guess(self):
        highest_entropy = -np.inf
        best_guess = ""
        if len(self.words) == 1:
            return next(iter(self.words))
        guesses = self.total_word_set if self.guess_all_words else self.words
        for guess in guesses:
            word_entropy = entropy(guess, self.words)
            if word_entropy > highest_entropy:
                best_guess = guess
                highest_entropy = word_entropy
        return best_guess

    def update_words(self):
        self.words = set(filter(self.state.matches, self.words))

    def is_impossible(self):
        if len(self.words) == 0:
            return True
        return self.state.is_impossible()

    def is_solved(self):
        return self.state.is_solved()

def solve_interactive():

    tile_status_from_character = {
        '-':TileStatus.Incorrect,
        'y':TileStatus.PartialMatch,
        'g':TileStatus.Correct
    }
    print("Input: '-' if the letter is not a match (gray)\n"
          "       'y' if the letter is not a partial match (yellow)\n"
          "       'g' if the letter is not a match (green)")

    def get_clue_from_user(guess):
        while True:
            clue_string = input(f"Guess the word {guess} and input the clue string:")

            # Check that the number of characters is correct
            if len(clue_string) != len(guess):
                print("Incorrect number of letters. Try again.")
                continue

            # Check that the characters are valid
            characters_are_valid = True
            for c in clue_string:
                if c not in tile_status_from_character.keys():
                    print(f"Unknown tile status: {c}")
                    characters_are_valid = False
                    break
            if not characters_are_valid:
                continue
                
            return [(l, tile_status_from_character[c]) for l, c in zip(guess, clue_string)]
    
    solver = WordleSolver()
    guess = "slate"
    while True:
        clue = get_clue_from_user(guess)
        solver.add_clue(clue)
        solver.update_words() 
        
        if solver.is_solved():
            print(f"The solution is {solver.next_guess()}")
            break
        if solver.is_impossible():
            print(f"Cannot find a solution. The word may not be in my dictionary.")
            break

        guess = solver.next_guess()

def solve(word, verbose=False, guess_all_words=False):
    assert word in english_words_lower_set, f"The word '{word}' is not in my dictionary"

    solver = WordleSolver(guess_all_words=guess_all_words)

    guess = "slate"
    iteration = 0
    while not solver.is_solved():
        iteration += 1
        clue = get_clue(word, guess)
        solver.add_clue(clue)
        solver.update_words()

        if verbose:
            print(f"Guess {iteration}: {guess}")
            if len(solver.words) < 20:
                print(solver.words)
            else:
                print(f"{len(solver.words)} possible words")
        guess = solver.next_guess()

    return iteration

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["solve", "perf", "test"])
    parser.add_argument(
        "word",
        nargs="?",
        type=str,
        help=
        "In 'test' mode this is the solution that the solver must find. Otherwise this argument is ignored."
    )
    parser.add_argument("--guess_all_words", action="store_true", help="Allow the solver to guess words that have already been ruled out.")
    args = parser.parse_args()

    if args.mode == "test":
        assert args.word, "You must add a word in 'test' mode. Rerun with the option --help for more information"
        solve(args.word, verbose=True, guess_all_words=args.guess_all_words)
    elif args.mode == "solve":
        solve_interactive()
    elif args.mode == "perf":
        iterations = dict()
        iterations = {word: solve(word, guess_all_words=args.guess_all_words) for word in all_candidate_words()}
        plt.hist(iterations.values())
        plt.show()