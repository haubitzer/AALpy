from collections import Counter
from random import choice
from typing import Optional

from aalpy.automata import Dfa, MealyMachine, MooreMachine, Onfsm, Mdp, StochasticMealyMachine, IoltsMachine, \
    MarkovChain, QUIESCENCE
from aalpy.base import SUL


class DfaSUL(SUL):
    """
    System under learning for DFAs.
    """

    def __init__(self, dfa: Dfa):
        super().__init__()
        self.dfa = dfa

    def pre(self):
        """
        Resets the dfa to the initial state.
        """
        self.dfa.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        """
        If the letter is empty/None check is preform to see if the empty string is accepted by the DFA.

        Args:

            letter: single input or None representing the empty string

        Returns:

            output of the dfa.step method (whether the next state is accepted or not)

        """
        if letter is None:
            return self.dfa.initial_state.is_accepting
        return self.dfa.step(letter)


class MdpSUL(SUL):
    def __init__(self, mdp: Mdp):
        super().__init__()
        self.mdp = mdp

    def query(self, word: tuple) -> list:
        initial_output = self.pre()
        out = [initial_output]
        for letter in word:
            out.append(self.step(letter))
        self.post()
        return out

    def pre(self):
        self.mdp.reset_to_initial()
        return self.mdp.current_state.output

    def post(self):
        pass

    def step(self, letter):
        return self.mdp.step(letter)


class McSUL(SUL):
    def __init__(self, mdp: MarkovChain):
        super().__init__()
        self.mc = mdp

    def query(self, word: tuple) -> list:
        initial_output = self.pre()
        out = [initial_output]
        for letter in word:
            out.append(self.step(letter))
        self.post()
        return out

    def pre(self):
        self.mc.reset_to_initial()
        return self.mc.current_state.output

    def post(self):
        pass

    def step(self, letter=None):
        return self.mc.step()


class MealySUL(SUL):
    """
    System under learning for Mealy machines.
    """

    def __init__(self, mm: MealyMachine):
        super().__init__()
        self.mm = mm

    def pre(self):
        """ """
        self.mm.reset_to_initial()

    def post(self):
        """ """
        pass

    def step(self, letter):
        """
        Args:

            letter: single non-Null input

        Returns:

            output of the mealy.step method (output based on the input and the current state)

        """
        return self.mm.step(letter)


class MooreSUL(SUL):
    """
    System under learning for Mealy machines.
    """

    def __init__(self, moore_machine: MooreMachine):
        super().__init__()
        self.mm = moore_machine

    def pre(self):
        """ """
        self.mm.reset_to_initial()

    def post(self):
        """ """
        pass

    def step(self, letter):
        if letter is None:
            return self.mm.initial_state.output
        return self.mm.step(letter)


class OnfsmSUL(SUL):
    def __init__(self, mdp: Onfsm):
        super().__init__()
        self.onfsm = mdp

    def pre(self):
        self.onfsm.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        return self.onfsm.step(letter)


class StochasticMealySUL(SUL):
    def __init__(self, smm: StochasticMealyMachine):
        super().__init__()
        self.smm = smm

    def pre(self):
        self.smm.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        return self.smm.step(letter)


class IoltsMachineSUL(SUL):
    def __init__(self, iolts: IoltsMachine, query_certainty_threshold: float = 0.99, completeness_certainty_threshold: float = 0.99):
        super().__init__()
        self.iolts = iolts
        self.query_certainty_threshold = query_certainty_threshold
        self.completeness_certainty_threshold = completeness_certainty_threshold

        self.cache = dict()
        self.num_listens = 0
        self.num_completeness_queries = 0
        self.num_completeness_steps = 0
        self.num_completeness_listens = 0

    def pre(self):
        self.num_queries += 1
        self.iolts.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        self.num_steps += 1
        return self.iolts.step(letter)

    def has_accepted_input(self):
        return self.iolts.is_healthy()

    def is_input(self, letter):
        return letter in self.iolts.get_input_alphabet()

    def is_output(self, letter):
        return letter in self.iolts.get_output_alphabet()

    @staticmethod
    def is_quiescence(letter):
        return letter is QUIESCENCE

    def listen(self):
        self.num_listens += 1
        return self.iolts.listen()

    def query(self, word: tuple, with_cache: bool = True) -> Optional[str]:
        in_cache, counter = self._cache_lookup(word)
        if in_cache and with_cache:
            self.num_cached_queries += 1
            return choice(list(counter.elements()))

        if in_cache and all(k is None for k in counter.keys()):
            self.num_cached_queries += 1
            return None

        output = self._query_with_step(word)
        self._cache_update(word, output)
        # self._cache_update(self.reduce_trace(word), output)

        return output

    @staticmethod
    def reduce_trace(trace) -> tuple:
        return tuple([letter for letter in trace if letter != QUIESCENCE])

    def get_cache_elements(self, word) -> set:
        in_cache, counter = self._cache_lookup(word)
        if not in_cache:
            return set()

        return set(sorted(list(set(counter.elements()))))

    def _cache_update(self, word, output):
        if word not in self.cache.keys():
            self.cache.update({word: Counter()})

        self.cache.get(word).update([output])

    def _cache_lookup(self, word) -> tuple[bool, Optional[Counter]]:
        from aalpy.utils.HelperFunctions import all_prefixes

        is_unreachable = False
        for prefix in all_prefixes(word):
            if prefix in self.cache.keys():
                is_unreachable = all(k is None for k in self.cache[prefix].keys())

            if is_unreachable:
                self._cache_update(prefix, None)

        if word in self.cache.keys():
            return True, self.cache[word]

        return False, None

    def _query_with_step(self, word) -> Optional[str]:
        is_certain = False
        output = None

        while not is_certain:
            self.pre()
            prefix, suffix = self.split_word(word)

            if not self._step_trace(prefix, tuple()):
                continue

            if not self._step_trace(suffix, prefix):
                is_certain = self.calculate_all_seen_probability(prefix) > self.query_certainty_threshold
                continue

            output = self.listen()
            break

        self.post()
        return output

    def split_word(self, word):
        from aalpy.utils.HelperFunctions import all_prefixes

        for prefix in reversed(all_prefixes(word)):
            in_cache, counter = self._cache_lookup(prefix)
            is_reachable = counter and not all(k is None for k in counter.keys())
            if in_cache and is_reachable:
                if prefix == word:
                    return tuple(prefix), tuple()

                if word[len(prefix)] in counter.keys():
                    new_prefix = prefix + (word[len(prefix)],)
                    return tuple(new_prefix), tuple(word[len(new_prefix):])

                return tuple(prefix), tuple(word[len(prefix):])

        return tuple([]), tuple(word)

    def _step_trace(self, word, cache_prefix) -> bool:
        for i, letter in enumerate(word):
            if self.is_input(letter):
                self.step(letter)
                if not self.has_accepted_input():
                    output = self.listen()
                    self._cache_update(cache_prefix + word[:i], output)
                    return False

            if self.is_output(letter):
                output = self.listen()
                self._cache_update(cache_prefix + word[:i], output)

                if output != letter:
                    return False

            if self.is_quiescence(letter):
                output = self.listen()
                self._cache_update(cache_prefix + word[:i], output)

                if output != letter:
                    return False

        return True

    def completeness_query(self, word: tuple, observed_set: set) -> bool:
        saved_num_steps = self.num_steps
        saved_num_queries = self.num_queries
        saved_num_listens = self.num_listens

        is_complete = True
        while is_complete and not self.completeness_threshold_reached(word):
            if self.query(word, False) in observed_set:
                continue
            else:
                is_complete = False

        self.num_completeness_queries += self.num_queries - saved_num_queries
        self.num_queries = saved_num_queries
        self.num_completeness_steps += self.num_steps - saved_num_steps
        self.num_steps = saved_num_steps
        self.num_completeness_listens += self.num_listens - saved_num_listens
        self.num_listens = saved_num_listens

        return is_complete

    def completeness_threshold_reached(self, word: tuple) -> bool:
        return self.calculate_all_seen_probability(word) >= self.completeness_certainty_threshold

    def calculate_all_seen_probability(self, word: tuple):
        in_cache, counter = self._cache_lookup(word)
        if not in_cache:
            return 0

        num_cached_outputs = sum(counter.values())
        num_unique_outputs = len(counter.keys())
        p_hidden = (1 - 1 / (num_unique_outputs + 1)) ** num_cached_outputs
        return 1 - p_hidden
