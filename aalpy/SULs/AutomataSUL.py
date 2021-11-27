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
    def __init__(self, iolts: IoltsMachine):
        super().__init__()
        self.iolts = iolts
        self.cache = dict()
        self.num_completeness_queries = 0
        self.num_completeness_steps = 0

    def pre(self):
        self.num_queries += 1
        self.iolts.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        self.num_steps += 1
        return self.iolts.step(letter)

    # TODO remove step_to function or make it opt_in
    def step_to(self, letter):
        self.num_steps += 1
        return self.iolts.step_to(letter)

    def query(self, word: tuple, with_cache: bool = True) -> Optional[str]:
        # TODO cache needs to store more than one output.
        in_cache, output = self._cache_lookup(word)
        if in_cache and with_cache:
            return output

        iterations = self._approximated_iterations(word)
        output = self._query_with_step_to(word, iterations)
        self.cache.update({word: output})

        return output

    def _cache_lookup(self, word) -> tuple[bool, Optional[str]]:
        from aalpy.utils.HelperFunctions import all_prefixes

        for prefix in all_prefixes(word):
            if prefix in self.cache.keys() and self.cache[prefix] is None:
                return True, None

        if word in self.cache.keys():
            return True, self.cache[word]

        return False, None

    def _approximated_iterations(self, word) -> int:
        # TODO find good retry rate
        # First check how long the prefix is that is not in the cache,
        # For each step in the prefix we assume that there is an "no rare event" rate maybe something like (1/num_outputs)
        # we probability that the prefix happen is len(suffix) * rate.
        # The prefix is possible and we know that. We need to take that into account but not sure how yet,
        # because the same trace could lead to different states.

        # However, if the suffix is longer than 1 and the first step was successful we need to recalculate the iterations.

        from aalpy.utils.HelperFunctions import all_prefixes

        len_prefix = len(word)
        for i, prefix in enumerate(all_prefixes(word)):
            if prefix not in self.cache.keys():
                len_prefix = len(word) - i
                break

        propability = len_prefix * 1 / len(self.iolts.get_output_alphabet())

        population_size = len(self.iolts.get_output_alphabet()) ** len_prefix

        # print(population_size)

        return 1

    def _query_with_step_to(self, word, iterations) -> Optional[str]:
        for _ in range(iterations):
            self.pre()
            if self._step_trace(word):
                # TODO wrap this function
                output = self.iolts._output_step_to(None, None) or QUIESCENCE
                self.post()
                return output
            else:
                self.post()

        return None

    def _step_trace(self, word) -> bool:
        for i, letter in enumerate(word):
            if self.step_to(letter) is None:
                return False
        return True

    def completeness_query(self, word: tuple, observed_set: set) -> bool:
        # TODO don't use cache
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

        num_iterations = 0
        p_all_seen = 0
        # TODO replace with counter
        seen_outputs = set()

        while p_all_seen < 0.9:
            output = self.query(word, False)
            seen_outputs.add(output)
            if output not in observed_set:
                self.num_completeness_queries += self.num_queries - saved_num_queries
                self.num_queries = saved_num_queries
                self.num_completeness_steps += self.num_steps - saved_num_steps
                self.num_steps = saved_num_steps

                return False
            else:
                num_iterations += 1
                num_seen_outputs = len(seen_outputs)
                p_hidden = (1 - 1 / (num_seen_outputs + 1)) ** num_iterations
                p_all_seen = 1 - p_hidden

        self.num_completeness_queries += self.num_queries - saved_num_queries
        self.num_queries = saved_num_queries
        self.num_completeness_steps += self.num_steps - saved_num_steps
        self.num_steps = saved_num_steps

        return True
