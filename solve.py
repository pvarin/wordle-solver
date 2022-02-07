import enum
import numpy as np
import argparse
from english_words import english_words_lower_set


def lowercase_letters():
    return [chr(i) for i in range(97, 97 + 26)]


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
    ), f"The guess is {len(guess)} letters, but the word is {len(word)} letters long."

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
            if len(l) > 1:
                return False
        return True


class WordleSolver:

    def __init__(self):
        self.words = english_words_lower_set.copy()
        self.state = WordleState()
        self.update_words()

    def add_clue(self, clue):
        self.state.add_clue(clue)

    def next_guess(self):
        highest_entropy = -np.inf
        best_guess = ""
        for guess in self.words:
            word_entropy = entropy(guess, self.words)
            if word_entropy > highest_entropy:
                best_guess = guess
                highest_entropy = word_entropy
        return best_guess

    def update_words(self):
        self.words = set(filter(self.state.matches, self.words))

    def is_solved(self):
        return self.state.is_solved()


def solve(word, verbose=False):
    solver = WordleSolver()

    guess = "slate"
    iteration = 1
    while not solver.is_solved():
        print(f"Guess {iteration}: {guess}")
        clue = get_clue(word, guess)
        solver.add_clue(get_clue(word, guess))
        solver.update_words()

        if verbose:
            if len(solver.words) < 20:
                print(solver.words)
            else:
                print(f"{len(solver.words)} possible words")
        guess = solver.next_guess()
        iteration += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "word",
        nargs="?",
        type=str,
        help=
        "The solution. In this mode the solver prints the guesses that would have resulted in the solution."
    )
    args = parser.parse_args()

    if args.word:
        solve(args.word)
