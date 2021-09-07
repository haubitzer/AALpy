import itertools
from collections import defaultdict

from aalpy.SULs import IotsMachineSUL
from aalpy.automata import Dfa, DfaState, MealyState, MealyMachine, MooreMachine, MooreState
from aalpy.base import Automaton

QUIESCENCE = tuple(["QUIESCENCE"])
EMPTY_WORD = tuple()


class ApproximatedIotsObservationTable:
    def __init__(self, alphabet: list, sul: IotsMachineSUL):
        """
        Constructor of the observation table. Initial queries are asked in the constructor.

        Args:

            alphabet: input alphabet
            sul: system under learning
            automaton_type: automaton type, one of ['dfa', 'mealy', 'moore']

        Returns:

        """
        assert alphabet is not None and sul is not None

        self.sul = sul

        self.A = [tuple([a]) for a in alphabet] + [QUIESCENCE]
        self.S = list()
        self.S_dot_A = []
        self.E = []
        self.T = defaultdict(lambda: defaultdict(set))
        self.T_completed = defaultdict(lambda: defaultdict(bool))

        self.S.append(EMPTY_WORD)
        self.E.append(EMPTY_WORD)

    def is_defined(self, s):
        suffix = None
        prefix = None

        if len(s) > 1:
            suffix = s[:-1]
            prefix = tuple([s[-1]])
        else:
            suffix = EMPTY_WORD
            prefix = s

        if prefix == EMPTY_WORD:
            return True
        if prefix[0][0].startswith("?"):
            return suffix == EMPTY_WORD or suffix[-1][0].startswith("!") or suffix[-1] == QUIESCENCE
        if prefix[0][0].startswith("!"):
            return prefix in self.T[suffix][EMPTY_WORD]
        if prefix == QUIESCENCE:
            return QUIESCENCE is self.T[suffix][EMPTY_WORD] and suffix == EMPTY_WORD or tuple([s[-1]]) != QUIESCENCE

        raise Exception("Unknown case")

    def is_globally_closed(self):
        rows_to_close = []

        for s1, a in itertools.product(self.S, self.A):
            if not self.is_defined(s1 + a):
                continue

            for s2 in self.S:
                if self.T[s1 + a] != self.T[s2]:
                    rows_to_close.append(s1 + a)
                elif self.T_completed[s1 + a] != self.T_completed[s2]:
                    rows_to_close.append(s1 + a)

        return len(rows_to_close) == 0, list(set(rows_to_close))

    def is_globally_consistent(self):
        causes_of_inconsistency = []

        for s1, s2 in itertools.product(self.S, self.S):
            if s1 == s2 or self.T[s1] != self.T[s2]:
                continue
            for a, e in itertools.product(self.A, self.E):
                if not self.is_defined(s1 + a):
                    continue

                if not self.is_defined(s2 + a):
                    continue

                if self.T[s1 + a][e] != self.T[s2 + a][e]:
                    causes_of_inconsistency.append(a + e)

        for s1, s2 in itertools.product(self.S, self.S):
            if self.T[s1] != self.T[s2]:
                continue
            if self.T_completed[s1] != self.T_completed[s2]:
                continue
            for a, e in itertools.product(self.A, self.E):
                if not self.is_defined(s1 + a):
                    continue

                if not self.is_defined(s2 + a):
                    continue

                if self.T[s1 + a][e] != self.T[s2 + a][e]:
                    causes_of_inconsistency.append(a + e)
                if self.T_completed[s1 + a][e] != self.T_completed[s2 + a][e]:
                    causes_of_inconsistency.append(a + e)

        return len(causes_of_inconsistency) == 0, list(set(causes_of_inconsistency))

    def s_dot_a(self):
        """
        Helper generator function that returns extended S, or S.A set.
        """
        print(self.S)
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
            if not self.is_defined(s):
                continue

            if self.T_completed[s][e]:
                continue

            # if a trace ends with quiescence only an input can enable an output, so we mark the cell as completed
            if len(s + e) > 0 and (s + e)[-1] == QUIESCENCE:
                self.T[s][e] = QUIESCENCE
                self.T_completed[s][e] = True
                continue

            # if s ends with Q and s[-1] enables only Q than row(s + Q) == row(s)
            longest_prefix = s[:-1]
            ends_with_quiescence = len(s) > 0 and s[-1] == QUIESCENCE
            enable_quiescence = self.T[longest_prefix][EMPTY_WORD] == QUIESCENCE
            prefix_completed = self.T_completed[s][EMPTY_WORD]

            #if ends_with_quiescence and enable_quiescence and prefix_completed:
            #    self.T[s][e] = self.T[longest_prefix][e]
            #    if self.T_completed[longest_prefix][e]:
            #        self.T_completed[s][e] = True
            #    continue

            out, last_state = self.sul.query(s + e)

            last_output = out[-1]
            if last_output is None:
                self.T[s][e] = QUIESCENCE
            else:
                self.T[s][e].add(last_output)

            valid_outputs = [key for key, _ in last_state.get_outputs()]

            if not valid_outputs and self.T[s][e] == QUIESCENCE:
                self.T_completed[s][e] = True
                continue

            if all(elm in self.T[s][e] for elm in valid_outputs):
                self.T_completed[s][e] = True
                continue

    def gen_hypothesis(self, check_for_duplicate_rows=False) -> Automaton:
        """
        Generate automaton based on the values found in the observation table.
        :return:

        Args:

            check_for_duplicate_rows:  (Default value = False)

        Returns:

            Automaton of type `automaton_type`

        """
        state_distinguish = dict()
        states_dict = dict()
        initial_state = None
        automaton_class = {'dfa': Dfa, 'mealy': MealyMachine, 'moore': MooreMachine}

        # delete duplicate rows, only possible if no counterexample processing is present
        # counterexample processing removes the need for consistency check, as it ensures
        # that no two rows in the S set are the same
        if check_for_duplicate_rows:
            rows_to_delete = set()
            for i, s1 in enumerate(self.S):
                for s2 in self.S[i + 1:]:
                    if self.T[s1] == self.T[s2]:
                        rows_to_delete.add(s2)

            for row in rows_to_delete:
                self.S.remove(row)

        # create states based on S set
        stateCounter = 0
        for prefix in self.S:
            state_id = f's{stateCounter}'

            if self.automaton_type == 'dfa':
                states_dict[prefix] = DfaState(state_id)
                states_dict[prefix].is_accepting = self.T[prefix][0]
            elif self.automaton_type == 'moore':
                states_dict[prefix] = MooreState(state_id, output=self.T[prefix][0])
            else:
                states_dict[prefix] = MealyState(state_id)

            states_dict[prefix].prefix = prefix
            state_distinguish[tuple(self.T[prefix])] = states_dict[prefix]

            if not prefix:
                initial_state = states_dict[prefix]
            stateCounter += 1

        # add transitions based on extended S set
        for prefix in self.S:
            for a in self.A:
                state_in_S = state_distinguish[self.T[prefix + a]]
                states_dict[prefix].transitions[a[0]] = state_in_S
                if self.automaton_type == 'mealy':
                    states_dict[prefix].output_fun[a[0]] = self.T[prefix][self.E.index(a)]

        automaton = automaton_class[self.automaton_type](initial_state, list(states_dict.values()))
        automaton.characterization_set = self.E

        return automaton
