import itertools
from collections import defaultdict, Counter
from typing import Union, Tuple, List, Any

from sortedcontainers import SortedSet, SortedList, SortedDict

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsState, IoltsMachine, QUIESCENCE
from aalpy.utils.HelperFunctions import all_prefixes, all_suffixes

EMPTY_WORD = tuple()
QUIESCENCE_TUPLE = tuple([QUIESCENCE])


class ApproximatedIoltsObservationTable:
    def __init__(
            self, input_alphabet: list, output_alphabet: list, sul: IoltsMachineSUL
    ):
        """
        Constructor of the observation table. Initial queries are asked in the constructor.
        """
        assert input_alphabet is not None
        assert output_alphabet is not None
        assert sul is not None

        self.sul = sul

        self.cache_for_is_defined = set()
        self.cache_for_row = dict()
        self.cache_for_row_plus = dict()

        self.A_input = [tuple([a]) for a in input_alphabet]
        self.A_output = [tuple([a]) for a in output_alphabet]
        self.A = self.A_input + self.A_output + [QUIESCENCE_TUPLE]

        self.S = list()
        self.S_dot_A = []
        self.E = []
        self.T = dict(dict())
        self.T_completed = dict(dict())

        self.S.append(EMPTY_WORD)
        self.E.append(EMPTY_WORD)

    def is_defined(self, word):
        if word in self.cache_for_is_defined:
            return True

        for prefix in all_prefixes(word):
            if prefix in self.cache_for_is_defined:
                continue

            if not self._prefix_is_defined(prefix):
                return False

            self.cache_for_is_defined.add(prefix)

        return True

    def _prefix_is_defined(self, s: tuple):
        if s == EMPTY_WORD:
            return True
        elif len(s) == 1:
            prev = None
            next = s[0]
        else:
            prev = s[-2]
            next = s[-1]

        if prev is None:
            return next.startswith("?") or next == QUIESCENCE

        prev_is_input = prev.startswith("?")
        prev_is_output = prev.startswith("!")
        prev_is_quiescence = prev == QUIESCENCE
        quiescence_in_cell = self.cell_contains(s[:-1], EMPTY_WORD, QUIESCENCE)

        next_is_input = next.startswith("?")
        next_is_output = next.startswith("!")
        next_is_quiescence = next == QUIESCENCE
        next_in_cell = self.cell_contains(s[:-1], EMPTY_WORD, next)

        valid_input = (prev_is_output or prev_is_quiescence or quiescence_in_cell) and next_is_input
        valid_output = (prev_is_input or prev_is_output) and next_is_output and next_in_cell
        valid_quiescence = (quiescence_in_cell and not prev_is_quiescence and next_is_quiescence)

        is_defined = valid_input or valid_output or valid_quiescence

        return is_defined

    def row(self, s):
        if s in self.cache_for_row:
            return self.cache_for_row[s]

        result = SortedDict(SortedSet)
        for e in self.E:
            result[e] = SortedSet(self.T[s][e])

        self.cache_for_row[s] = result
        return result

    def row_plus(self, s):
        if s in self.cache_for_row_plus:
            return self.cache_for_row_plus[s]

        result = SortedDict(tuple)
        for e in self.E:
            result[e] = (SortedSet(self.T[s][e]), self.T_completed[s][e])

        self.cache_for_row_plus[s] = result
        return result

    def row_equals(self, s1, s2) -> bool:
        return all(self.T[s1][e] == self.T[s2][e] for e in self.E)

    def row_plus_equals(self, s1, s2, skip_row_equals: bool = False) -> bool:
        return (skip_row_equals or self.row_equals(s1, s2)) and all(
            self.T_completed[s1][e] == self.T_completed[s2][e] for e in self.E)

    def cell_contains(self, s, e, out):
        if s not in self.T:
            return False
        if e not in self.T[s]:
            return False
        return out in self.T[s][e]

    def is_globally_closed(self):
        rows_to_close = SortedList()

        for s1, a in itertools.product(self.S, self.A):
            if not self.is_defined(s1 + a):
                continue

            if not any(self.row_plus_equals(s1 + a, s2) for s2 in self.S):
                rows_to_close.add(s1 + a)
                break

        if rows_to_close:
            return False, [rows_to_close[0]]
        else:
            return True, []

    def is_globally_consistent(self):
        e_for_consistency = SortedList()
        cause = None

        for s1, s2 in itertools.product(self.S, self.S):
            for a, e in itertools.product(self.A, self.E):
                if not self.is_defined(s1 + a) or not self.is_defined(s2 + a):
                    continue

                is_row_equals = self.row_equals(s1, s2)

                if is_row_equals and self.row(s1 + a)[e] != self.row(s2 + a)[e]:
                    e_for_consistency.add(a + e)
                    cause = f"{s1} + {a} + {e} => {self.row_plus(s1 + a)[e]} \n {s2} + {a} + {e} => {self.row_plus(s2 + a)[e]}"
                    break

                if is_row_equals and self.row_plus_equals(s1, s2, True) and self.row_plus(s1 + a)[e] != \
                        self.row_plus(s2 + a)[e]:
                    e_for_consistency.add(a + e)
                    cause = f"{s1} + {a} + {e} => {self.row_plus(s1 + a)[e]} \n {s2} + {a} + {e} => {self.row_plus(s2 + a)[e]}"
                    break

        if e_for_consistency:
            return False, [e_for_consistency[0]], cause
        else:
            return True, [], None

    def is_quiescence_reducible(self) -> Union[tuple[bool, list[Any], str], tuple[bool, list[Any], None]]:
        for s1, s2 in itertools.product(self.S, self.S):
            if not self.is_defined(s1) or not self.is_defined(s2):
                continue
            if not self.cell_contains(s1, EMPTY_WORD, QUIESCENCE):
                continue
            if not self.row_equals(s1 + QUIESCENCE_TUPLE, s2):
                continue

            wait = [(s1, s2, EMPTY_WORD)]
            past = []

            while wait:
                s1, s2, t = wait.pop(0)

                s1_cell_values = SortedList((out,) for out in self.row(s1)[EMPTY_WORD]) + self.A_input
                s2_cell_values = SortedList((out,) for out in self.row(s2)[EMPTY_WORD]) + self.A_input

                for a in s2_cell_values:
                    if a not in s1_cell_values:
                        cause = f"{s1} + {EMPTY_WORD} => {self.row_plus(s1)[EMPTY_WORD]} \n {s2} + {EMPTY_WORD} => {self.row_plus(s2)[EMPTY_WORD]} / {a} | t = {t}"
                        return True, [t], cause

                    s_prime_1 = None
                    s_prime_2 = None
                    for s in self.S:
                        if self.row_equals(s, s1 + a):
                            s_prime_1 = s
                        if self.row_equals(s, s2 + a):
                            s_prime_2 = s

                    if (
                            s_prime_1 != s_prime_2
                            and (s_prime_1, s_prime_2) not in past
                            and s_prime_1 is not None
                            and s_prime_2 is not None
                    ):
                        wait.append((s_prime_1, s_prime_2, t + a))

                past.append((s1, s2))

        return False, [], None

    def s_dot_a(self):
        """
        Helper generator function that returns extended S, or S.A set.
        """
        s_set = set(self.S)
        for s, a in itertools.product(self.S, self.A):
            if s + a not in s_set:
                yield s + a

    def get_quiescence_traces(self, word):
        extended_word = list(itertools.chain.from_iterable([[letter, QUIESCENCE] for letter in word]))
        all_indexes = sorted(set([tuple(set(prod)) for prod in
                                  itertools.product(range(1, len(extended_word), 2), repeat=len(extended_word))]))

        for indexes in all_indexes:
            trace = extended_word.copy()
            for index in sorted(indexes, reverse=True):
                del trace[index]
            yield tuple(trace)

    def update_obs_table(self, s_set: list = None, e_set: list = None):
        """
        Perform the membership queries.

        Args:

            s_set: Prefixes of S set on which to preform membership queries. If None, then whole S set will be used.

            e_set: Suffixes of E set on which to perform membership queries. If None, then whole E set will be used.

        Returns:

        """
        self.cache_for_row.clear()
        self.cache_for_row_plus.clear()

        update_S = s_set if s_set is not None else list(self.S) + list(self.s_dot_a())
        update_E = e_set if e_set is not None else self.E

        for s, e in itertools.product(update_S, update_E):
            if s not in self.T:
                self.T[s] = dict()
                self.T_completed[s] = dict()

            if e not in self.T[s]:
                self.T[s][e] = set()
                self.T_completed[s][e] = False

        for s, e in itertools.product(update_S, update_E):
            if not self.is_defined(s + e):
                continue

            # If cell is marked as completed the loop can continue
            if self.T_completed[s][e]:
                # self.T_completed[s][e] = self.sul.completeness_query(s + e, self.T[s][e])
                # TODO updating cell after completed mark creates huge problems!!!
                # self.T[s][e].update(self.sul.get_cache_elements(s + e))
                continue

            # if a trace ends with quiescence only an input can enable an value in T, so we mark the cell as completed
            if len(s + e) > 0 and tuple([(s + e)[-1]]) == QUIESCENCE_TUPLE:
                self.T[s][e].add(QUIESCENCE)
                self.T_completed[s][e] = True
                continue

            # if s ends with Q and s[-1] enables only Q than row(s + Q) == row(s)
            longest_prefix = s[:-1]
            ends_with_quiescence = len(s) > 0 and s[-1] == QUIESCENCE_TUPLE
            enable_quiescence = QUIESCENCE in self.T[longest_prefix][EMPTY_WORD]
            prefix_completed = self.T_completed[s][EMPTY_WORD]

            if ends_with_quiescence and enable_quiescence and prefix_completed:
                self.T[s][e] = self.T[longest_prefix][e]
                if self.T_completed[longest_prefix][e]:
                    self.T_completed[s][e] = True
                continue

            # Note looks like that doesn't work well
            # if self.T[s][e] < self.sul.get_cache_elements(s + e):
            #    self.T[s][e].update(self.sul.get_cache_elements(s + e))
            # else:
            #    self.sul.query(s + e, False)
            #    self.T[s][e].update(self.sul.get_cache_elements(s + e))

            output = self.sul.query(s + e, False)

            if output is None:
                continue

            self.T[s][e].update(self.sul.get_cache_elements(s + e))

            # TODO this is two slow, need to find a better solution!!!
            # Maybe cache the caching in a way, that only the clean trace is used as a key...
            # All quiescence traces needs to be update, otherwise the observation table doesn't have the same data.
            # (s + e) => sQ + eQ

            # for quiescence_trace in self.get_quiescence_traces(s + e):
            #    self.T[s][e].update(self.sul.get_cache_elements(quiescence_trace))

            self.T_completed[s][e] = self.sul.completeness_query(s + e, self.T[s][e])

        for s, e in itertools.product(update_S, update_E):
            self.T[s][e] = set(filter(None, self.T[s][e]))
            self.T[s].update(dict(sorted(self.T[s].items())))
            self.T_completed[s].update(dict(sorted(self.T_completed[s].items())))

    def get_row_key(self, s) -> str:
        return str(sorted(self.row(s).items()))

    def get_row_plus_key(self, s) -> str:
        return str(sorted(self.row_plus(s).items()))

    def gen_hypothesis_minus(self) -> IoltsMachine:
        state_distinguish = dict()
        states_dict = dict()
        initial_state = None

        chaos_quiescence_state = IoltsState("Xq")
        chaos_quiescence_state.add_quiescence(chaos_quiescence_state)

        # create states based on S set
        for stateCounter, s in enumerate(self.S):
            state = IoltsState(f"s{stateCounter}")
            state.prefix = s

            states_dict[s] = state
            state_distinguish[self.get_row_key(s)] = state

            if s == EMPTY_WORD:
                initial_state = state

        # add transitions based on extended S set
        for s in self.S:
            state = states_dict[s]
            for i in self.A_input:
                row = self.get_row_key(s + i)
                if row in state_distinguish:
                    state.add_input(i[0], state_distinguish.get(row))

            for o in self.row(s)[EMPTY_WORD]:
                if o is not QUIESCENCE:
                    destination_state = state_distinguish[self.get_row_key(s + tuple([o]))]
                    state.add_output(o, destination_state)

        automaton = IoltsMachine(
            initial_state, list(states_dict.values()) + [chaos_quiescence_state]
        )

        automaton.remove_not_connected_states()

        return automaton

    def gen_hypothesis_plus(self, with_chaos_state: bool = True) -> IoltsMachine:
        state_distinguish = dict()
        states_dict = dict()
        initial_state = None

        chaos_state = IoltsState("Chaos")
        chaos_quiescence_state = IoltsState("ChaosQuiescence")

        for output in self.A_output:
            chaos_state.add_output(output[0], chaos_state)

        chaos_state.add_quiescence(chaos_quiescence_state)
        chaos_quiescence_state.add_quiescence(chaos_quiescence_state)

        # create states based on S set
        for stateCounter, s in enumerate(self.S):
            state = IoltsState(f"s{stateCounter}")
            state.prefix = s
            states_dict[s] = state
            state_distinguish[self.get_row_plus_key(s)] = state

            if s == EMPTY_WORD:
                initial_state = state

        # add transitions based on extended S set
        for s in self.S:
            state = states_dict[s]
            for i in self.A_input:
                row = self.get_row_plus_key(s + i)
                if row in state_distinguish:
                    state.add_input(i[0], state_distinguish.get(row))

            for output_tuple in self.A_output + [QUIESCENCE_TUPLE]:
                output = output_tuple[0]

                if not self.row(s)[EMPTY_WORD]:
                    pass

                if self.cell_contains(s, EMPTY_WORD, output):
                    row = self.get_row_plus_key(s + output_tuple)
                    if output_tuple == QUIESCENCE_TUPLE:
                        state.add_quiescence(state_distinguish.get(row))
                    else:
                        state.add_output(output, state_distinguish.get(row))
                elif not self.row_plus(s)[EMPTY_WORD][1] and with_chaos_state:
                    if output_tuple == QUIESCENCE_TUPLE:
                        state.add_quiescence(chaos_quiescence_state)
                    else:
                        state.add_output(output, chaos_state)

        automaton = IoltsMachine(
            initial_state,
            list(states_dict.values()) + [chaos_quiescence_state, chaos_state],
        )

        automaton.remove_not_connected_states()

        return automaton

    def gen_hypothesis_star(self) -> IoltsMachine:
        automaton = self.gen_hypothesis_plus(False)

        states_to_remove = Counter()

        for (trace, elements) in self.sul.cache.items():
            if all(out is None for out in elements):
                automaton.reset_to_initial()
                for letter in trace:
                    automaton.step_to(letter)

                states_to_remove.update([automaton.current_state.state_id])

        for (state_id, _) in states_to_remove.items():
            automaton.remove_state(automaton.get_state_by_id(state_id))

        return automaton

    def trim(self, h: IoltsMachine):
        prefix_to_state_set = set([state.prefix for state in h.states])

        to_remove = set(self.S) - prefix_to_state_set

        for s in to_remove:
            print(f"Remove: {s}")
            self.S.remove(s)
