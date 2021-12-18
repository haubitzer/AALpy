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
    def __init__(self, iolts: IoltsMachine, query_certainty_probability: float = 0.8, completeness_certainty_probability: float = 0.8):
        super().__init__()
        self.iolts = iolts
        self.query_certainty_probability = query_certainty_probability
        self.completeness_certainty_probability = completeness_certainty_probability

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

    def is_healthy(self):
        return self.iolts.is_healthy()

    def listen(self):
        self.num_listens += 1
        return self.iolts.listen()

    def query(self, word: tuple, with_cache: bool = True) -> Optional[str]:
        in_cache, counter = self._cache_lookup(word)
        if in_cache and with_cache:
            self.num_cached_queries += 1
            return choice(list(counter.elements()))

        if in_cache and all(k is None for k in counter.keys()):
            return None

        output = self._query_with_step(word)
        self._cache_update(word, output)

        return output

    def receive_cache(self, word) -> set:
        in_cache, counter = self._cache_lookup(word)
        if not in_cache:
            return set()

        return set(counter.elements())

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
                is_certain = self.calculate_all_seen_probability(prefix) > self.query_certainty_probability
                continue

            output = self.listen()
            break

        self.post()
        return output

    def split_word(self, word):
        from aalpy.utils.HelperFunctions import all_prefixes

        for prefix in reversed(all_prefixes(word)):
            in_cache, counter = self._cache_lookup(prefix)
            if in_cache and not all(k is None for k in counter.keys()):
                return tuple(prefix), tuple(word[len(prefix):])

        return tuple([]), tuple(word)

    def _step_trace(self, word, cache_prefix) -> bool:
        for i, letter in enumerate(word):
            if letter.startswith("?"):
                self.step(letter)
                if not self.is_healthy():
                    output = self.listen()
                    self._cache_update(cache_prefix + word[:i], output)
                    return False

            if letter.startswith("!"):
                output = self.listen()
                self._cache_update(cache_prefix + word[:i], output)

                if output != letter:
                    return False

            if letter == QUIESCENCE:
                output = self.listen()
                self._cache_update(cache_prefix + word[:i], output)

                if output != letter:
                    return False

        return True

    def calculate_all_seen_probability(self, word: tuple):
        in_cache, counter = self._cache_lookup(word)
        if not in_cache:
            return 0

        num_cached_outputs = sum(counter.values())
        num_unique_outputs = len(counter.keys())
        p_hidden = (1 - 1 / (num_unique_outputs + 1)) ** num_cached_outputs
        return 1 - p_hidden

    def completeness_query(self, word: tuple, observed_set: set) -> bool:
        # The completeness query should not use the cache system.
        # It should always make the real queries on the SUL.
        # The number of real queries is hard to guess, so we let the user assume a number.

        # However, the query can use the cache to find early False,

        # ----

        # Make the query and look at the outcome, make the query again and remember what you saw.
        # We make queries until the chance that the outcome we don't know it lower than some probability given by the user

        # The idea: we calculate the probability it would take that an unknown output that is possible didn't happen.
        # We assume always that there is an unknown output, and that all outputs have the same probability.
        # If the calculate probability is higher than the given one from the user, the function can stop.

        # Example with seen 2 Outputs and a stop_rate 0.9 => would stop after 6 queries.
        # 1 - (1-1/(2 + 1)) ** 6 = 0.912 > 0.9

        # P_GIVEN_BY_USER = 0.9                                     -- the user wants to have a 90% probability that the result is correct
        # NUM_QUERIES = 0
        # NUM_SEEN_OUTPUTS = 0                                      -- maybe len(observed_set)
        #
        # while true
        #   (1 - 1 / (NUM_SEEN_OUTPUTS + 1)) ^ NUM_QUERIES = P_HIDDEN -- probability that we_missed an output
        #   1 - P_HIDDEN = P_ALL_SEEN                                 -- probability that we saw all outputs
        #   if P_ALL_SEEN > P_GIVEN_BY_USER:
        #        return TRUE                                            -- we are sure 90 % that the observed_set is complete
        #   else:
        #       make query and check against observed set               -- query the SUL to get a new output
        #       update NUM_SEEN_OUTPUTS
        #       NUM_QUERIES = + 1

        saved_num_steps = self.num_steps
        saved_num_queries = self.num_queries
        saved_num_listens = self.num_listens
        is_complete = True

        while self.calculate_all_seen_probability(word) < self.query_certainty_probability:
            output = self.query(word, False)
            if output not in observed_set:
                is_complete = False
                break

        self.num_completeness_queries += self.num_queries - saved_num_queries
        self.num_queries = saved_num_queries
        self.num_completeness_steps += self.num_steps - saved_num_steps
        self.num_steps = saved_num_steps
        self.num_completeness_listens += self.num_listens - saved_num_listens
        self.num_listens = saved_num_listens

        return is_complete
