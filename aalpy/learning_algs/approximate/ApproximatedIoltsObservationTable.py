import itertools
from collections import defaultdict

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsState, IoltsMachine, QUIESCENCE

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

        self.A_input = [tuple([a]) for a in input_alphabet]
        self.A_output = [tuple([a]) for a in output_alphabet]
        self.A = self.A_input + self.A_output + [QUIESCENCE_TUPLE]

        self.S = list()
        self.S_dot_A = []
        self.E = []
        self.T = defaultdict(lambda: defaultdict(set))
        self.T_completed = defaultdict(lambda: defaultdict(bool))

        self.S.append(EMPTY_WORD)
        self.E.append(EMPTY_WORD)

    def row_is_defined(self, s: tuple, prefix=None):
        if prefix:
            s = s + prefix

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
        quiescence_in_T = QUIESCENCE in self.row(s[:-1])[EMPTY_WORD]

        next_is_input = next.startswith("?")
        next_is_output = next.startswith("!")
        next_is_quiescence = next == QUIESCENCE
        next_in_T = next in self.row(s[:-1])[EMPTY_WORD]

        valid_input = (
                              prev_is_output or prev_is_quiescence or quiescence_in_T
                      ) and next_is_input
        valid_output = (prev_is_input or prev_is_output) and next_is_output and next_in_T
        valid_quiescence = (
                quiescence_in_T and not prev_is_quiescence and next_is_quiescence
        )

        return valid_input or valid_output or valid_quiescence

    def row(self, s):
        # assert self.row_is_defined(s)
        result = defaultdict(frozenset)
        for (key, t) in self.T[s].items():
            result[key] = frozenset(t)

        return result

    def row_plus(self, s):
        # assert self.row_is_defined(s)

        result = defaultdict(tuple)
        for (key, t), (_, c) in zip(self.T[s].items(), self.T_completed[s].items()):
            result[key] = (frozenset(t), c)

        return result

    def is_globally_closed(self):
        rows_to_close = []

        for s1, a in itertools.product(self.S, self.A):
            if not self.row_is_defined(s1 + a):
                continue

            if not any(self.row_plus(s1 + a) == self.row_plus(s2) for s2 in self.S):
                rows_to_close.append(s1 + a)
                return len(rows_to_close) == 0, list(set(rows_to_close))

        return len(rows_to_close) == 0, list(set(rows_to_close))

    def is_globally_consistent(self):
        causes_of_inconsistency = []

        for s1, s2 in itertools.product(self.S, self.S):
            for a, e in itertools.product(self.A, self.E):
                if not self.row_is_defined(s1 + a) or not self.row_is_defined(s2 + a):
                    continue

                if (
                        self.row(s1) == self.row(s2)
                        and self.row(s1 + a)[e] != self.row(s2 + a)[e]
                ):
                    causes_of_inconsistency.append(a + e)
                    return len(causes_of_inconsistency) == 0, list(
                        set(causes_of_inconsistency)
                    )

                if (
                        self.row_plus(s1) == self.row_plus(s2)
                        and self.row_plus(s1 + a)[e] != self.row_plus(s2 + a)[e]
                ):
                    causes_of_inconsistency.append(a + e)
                    return len(causes_of_inconsistency) == 0, list(
                        set(causes_of_inconsistency)
                    )

        return len(causes_of_inconsistency) == 0, list(set(causes_of_inconsistency))

    def is_quiescence_reducible(self) -> tuple[bool, list]:
        for s1, s2 in itertools.product(self.S, self.S):
            if QUIESCENCE not in self.row(s1)[EMPTY_WORD]:
                continue
            if self.row_plus(s1 + QUIESCENCE_TUPLE) != self.row_plus(s2):
                continue

            wait = [(s1, s2, EMPTY_WORD)]
            past = []

            while wait:
                s1, s2, t = wait.pop(0)

                s1_cell_values = [
                                     (out,) for out in self.row(s1)[EMPTY_WORD]
                                 ] + self.A_input
                s2_cell_values = [
                                     (out,) for out in self.row(s2)[EMPTY_WORD]
                                 ] + self.A_input

                for a in s2_cell_values:
                    if a not in s1_cell_values:
                        return True, [t]

                    s_prime_1 = None
                    s_prime_2 = None
                    for s in self.S:
                        if self.row_plus(s) == self.row_plus(s1 + a):
                            s_prime_1 = s
                        if self.row_plus(s) == self.row_plus(s2 + a):
                            s_prime_2 = s

                    if (
                            s_prime_1 != s_prime_2
                            and (s_prime_1, s_prime_2) not in past
                            and s_prime_1 is not None
                            and s_prime_2 is not None
                    ):
                        wait.append((s_prime_1, s_prime_2, t + a))

                past.append((s1, s2))

        return False, []

    def s_dot_a(self):
        """
        Helper generator function that returns extended S, or S.A set.
        """
        s_set = set(self.S)
        for s, a in itertools.product(self.S, self.A):
            if s + a not in s_set:
                yield s + a

    def update_obs_table(self, s_set: list = None, e_set: list = None):
        """
        Perform the membership queries.

        Args:

            s_set: Prefixes of S set on which to preform membership queries. If None, then whole S set will be used.

            e_set: Suffixes of E set on which to perform membership queries. If None, then whole E set will be used.

        Returns:

        """

        update_S = s_set if s_set is not None else list(self.S) + list(self.s_dot_a())
        update_E = e_set if e_set is not None else self.E

        for s, e in itertools.product(update_S, update_E):

            # If cell is marked as completed the loop can continue
            if self.T_completed[s][e]:
                # update every via the cache
                self.T[s][e].update(filter(None, self.sul.receive_cache(s + e)))
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

            output = self.sul.query(s + e, False)

            if output is None:
                continue

            self.T[s][e].update(self.sul.receive_cache(s + e))
            self.T_completed[s][e] = self.sul.completeness_query(s + e, self.T[s][e])

        # Sorts the set of T(s,e) to be deterministic
        for s, e in itertools.product(update_S, update_E):
            self.T[s].update(dict(sorted(self.T[s].items())))

    def get_row_key(self, s) -> tuple:
        return tuple(sorted(self.row(s).items()))

    def get_row_plus_key(self, s) -> tuple:
        return tuple(sorted(self.row_plus(s).items()))

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

                if output in self.row(s)[EMPTY_WORD]:
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

        # TODO find a good solution to merge to states.
        #if not with_chaos_state:
        #    for state in reversed(automaton.states):
        #        for _, destination in state.get_quiescence():
        #            if state != destination and state != chaos_state:
        #                automaton.merge_into(state, destination)

        return automaton
