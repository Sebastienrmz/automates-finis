import contextlib
import io
import random
import tempfile
import unittest
from collections import deque
from copy import deepcopy
from pathlib import Path

from automates import (Automaton, read_automaton, display_automaton, standardize,
    determinize, minimize, complement, recognize, check_standard,
    check_deterministic, check_complete, complete_aut)

ROOT = Path(__file__).resolve().parents[1]


def closure(a, states):
    result = set(states)
    while True:
        expanded = result | {t for s in result for t in a.transitions.get(s, {}).get('*', ())}
        if expanded == result:
            return frozenset(result)
        result = expanded


def step(a, states, symbol):
    return closure(a, {t for s in states for t in a.transitions.get(s, {}).get(symbol, ())})


def equivalent(left, right, inverted=False, starts=None):
    """Compare exactement les langages par exploration du produit atteignable."""
    initial = starts or (closure(left, left.initial_states), closure(right, right.initial_states))
    pending, visited = deque([initial]), {initial}
    while pending:
        a, b = pending.popleft()
        accepted_a = bool(set(a) & set(left.terminal_states))
        accepted_b = bool(set(b) & set(right.terminal_states))
        if (accepted_a == accepted_b) == inverted:
            return False
        for symbol in left.alphabet:
            pair = (step(left, a, symbol), step(right, b, symbol))
            if pair not in visited:
                visited.add(pair)
                pending.append(pair)
    return True


class AutomatesTests(unittest.TestCase):
    def check_transformations(self, a):
        original = deepcopy(a.__dict__)
        with contextlib.redirect_stdout(io.StringIO()):
            standard = standardize(a)
            deterministic, _, _ = determinize(a)
            minimal, _, _ = minimize(deterministic)
            opposite = complement(minimal)
            display_automaton(a)
        self.assertTrue(check_standard(standard)[0])
        for transformed in [standard, deterministic, minimal]:
            self.assertTrue(equivalent(a, transformed))
        self.assertTrue(equivalent(a, opposite, inverted=True))
        self.assertTrue(check_deterministic(minimal)[0])
        self.assertTrue(check_complete(minimal)[0])
        for i, left in enumerate(minimal.states):
            for right in minimal.states[i + 1:]:
                self.assertFalse(equivalent(minimal, minimal,
                    starts=(frozenset([left]), frozenset([right]))))
        self.assertEqual(a.__dict__, original)

    def test_provided_examples(self):
        paths = sorted((ROOT / 'data').glob('*.txt'))
        self.assertEqual(len(paths), 45)
        for path in paths:
            with self.subTest(file=path.name):
                self.check_transformations(read_automaton(path))

    def test_random_automata(self):
        rng = random.Random(2026)
        for case in range(80):
            with self.subTest(case=case):
                a = Automaton()
                a.states = list(range(rng.randint(1, 6)))
                a.nb_states = len(a.states)
                a.alphabet = list('abc'[:rng.randint(0, 3)])
                a.nb_symbols = len(a.alphabet)
                a.initial_states = [s for s in a.states if rng.random() < .4]
                a.terminal_states = [s for s in a.states if rng.random() < .4]
                for source in a.states:
                    for symbol in [*a.alphabet, '*']:
                        for target in a.states:
                            if rng.random() < .12:
                                a.add_transition(source, symbol, target)
                                a.has_epsilon |= symbol == '*'
                self.check_transformations(a)

    def read_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.txt'
            path.write_text(text, encoding='utf-8')
            return read_automaton(path)

    def test_malformed_files(self):
        malformed = ['', '-1\n1\n1 0\n0\n0', '27\n1\n1 0\n0\n0',
            '1\n0\n0\n0\n0', '1\n1\n2 0\n0\n0', '1\n1\n1 2\n0\n0',
            '1\n1\n2 0 0\n0\n0', '1\n1\n1 0\n0\n-1', '1\n1\n1 0\n0\n1',
            '1\n1\n1 0\n0\n0\n0 a 0', '1\n1\n1 0\n0\n1\n0 b 0',
            '1\n1\n1 0\n0\n1\n0 a 2', '1\n1\n1 0\n0\n1\n0 a 0 surplus']
        for text in malformed:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.read_text(text)

    def test_compact_multi_digit_states_and_bom(self):
        a = self.read_text('\ufeff1\n13\n1 12\n1 0\n1\n12a0\n')
        self.assertEqual(a.get(12, 'a'), {0})
        self.assertEqual(recognize('a', a), (True, None))

    def test_epsilon_into_initial_state_is_not_standard(self):
        a = self.read_text('1\n2\n1 0\n1 1\n1\n1 * 0')
        self.assertFalse(check_standard(a)[0])

    def test_unreachable_state_is_removed(self):
        a = self.read_text('1\n2\n1 0\n1 1\n2\n0 a 0\n1 a 1')
        with contextlib.redirect_stdout(io.StringIO()):
            result, _, _ = minimize(a)
        self.assertEqual(result.nb_states, 1)
        self.assertTrue(equivalent(a, result))

    def test_complement_requires_complete_input(self):
        a = self.read_text('1\n1\n1 0\n0\n0')
        with self.assertRaises(ValueError):
            complement(a)
        with contextlib.redirect_stdout(io.StringIO()):
            completed, _, changed = complete_aut(a)
        self.assertTrue(changed)
        self.assertTrue(equivalent(a, complement(completed), inverted=True))

    def test_empty_word_and_invalid_symbol(self):
        a = read_automaton(ROOT / 'data/01.txt')
        self.assertEqual(recognize('', a), (True, None))
        self.assertIsNotNone(recognize('x', a)[1])


if __name__ == '__main__':
    unittest.main()
