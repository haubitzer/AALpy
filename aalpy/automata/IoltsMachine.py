from __future__ import annotations

import string
from collections import defaultdict
from copy import deepcopy
from random import choice
from typing import Optional

from aalpy.base import Automaton, AutomatonState


class IoltsState(AutomatonState):
    def __init__(self, state_id):
        super().__init__(state_id)
        # Note: inputs/outputs maps to tuples of possible new state e.g. input => (state1, state2)
        self.inputs = defaultdict(tuple)
        self.outputs = defaultdict(tuple)
        self.quiescence = defaultdict(tuple)
        self.add_quiescence(None)
        # TODO: workaround for ioco, add a two sets to the ioco validator
        self.ioco_status = None

    def get_inputs(self, input: string = None, destination: IoltsState = None) -> list[tuple[str, IoltsState]]:
        assert input is None or input.startswith('?')

        result = [(input, state) for input, states in self.inputs.items() for state in states]
        result = result if input is None else list(filter(lambda elm: elm[0] == input, result))
        result = result if destination is None else list(filter(lambda elm: elm[1] == destination, result))

        return result

    def get_outputs(self, output: string = None, destination: IoltsState = None) -> list[tuple[str, IoltsState]]:
        assert output is None or output.startswith('!')

        result = [(output, state) for output, states in self.outputs.items() for state in states]
        result = result if output is None else list(filter(lambda elm: elm[0] == output, result))
        result = result if destination is None else list(filter(lambda elm: elm[1] == destination, result))

        return result

    def get_quiescence(self) -> list[tuple[str, IoltsState]]:
        if self.quiescence is not None:
            return [(quiescence, state) for quiescence, states in self.quiescence.items() for state in states]

        if self.is_quiescence():
            return [('quiescence', self)]

        return []

    def add_input(self, input: string, new_state: IoltsState):
        assert input.startswith('?')

        new_value = tuple([new_state]) + self.inputs[input] if input in self.inputs else tuple([new_state])
        self.inputs.update({input: new_value})
        self.transitions.update(self.inputs)

    def add_output(self, output: string, new_state):
        assert output.startswith('!')

        new_value = tuple([new_state]) + self.outputs[output] if output in self.outputs else tuple([new_state])
        self.outputs.update({output: new_value})
        self.transitions.update(self.outputs)
        # clear the quiescence entries, the are not valid
        self.quiescence.clear()
        self.transitions.pop('quiescence', None)

    def add_quiescence(self, new_state: IoltsState = None):
        # assert not bool(self.outputs)

        if new_state is None:
            new_state = self

        new_value = tuple([new_state]) + self.quiescence['quiescence'] if 'quiescence' in self.quiescence else tuple(
            [new_state])
        self.quiescence.update({'quiescence': tuple(set(list(new_value)))})
        self.transitions.update(self.quiescence)

    def remove_input(self, input, new_state):
        new_value = list(self.inputs[input])
        if new_state in new_value:
            new_value.remove(new_state)
        self.inputs.update({input: tuple(new_value)})
        self.transitions.update(self.inputs)

    def remove_output(self, output, new_state):
        new_value = list(self.outputs[output])
        if new_state in new_value:
            new_value.remove(new_state)
        self.outputs.update({output: tuple(new_value)})
        self.transitions.update(self.outputs)

    def is_input_enabled(self) -> bool:
        """
        A state is input enabled if an input can trigger an transition.

        Returns:
            bool: input enabled flag
        """
        return any(self.inputs.values())

    def is_input_enabled_for_diff_state(self, ) -> bool:
        return any(self not in states for states in self.inputs.values()) and self.inputs

    def is_quiescence(self) -> bool:
        """
        A state is quiescence if no output transition exists.

        Returns:
            bool: quiescence flag
        """
        return bool(self.quiescence)

    def is_deterministic(self) -> bool:
        deterministic_input = all(len(states) == 1 for states in self.inputs.values())
        deterministic_output = all(len(states) == 1 for states in self.outputs.values())
        return deterministic_input and deterministic_output

    def make_input_complete(self, alphabet: list):
        for letter in alphabet:
            if not self.get_inputs(letter):
                self.add_input(letter, self)


class IoltsMachine(Automaton):
    """
    Input output labeled transition system machine.
    """

    def __init__(self, initial_state: IoltsState, states: list[IoltsState]):
        super().__init__(initial_state, states)
        self.current_state: IoltsState
        self.initial_state: IoltsState
        self.states: list[IoltsState]

    def step(self, letter):
        assert self.is_input_complete()

        input = self._input_step_to(letter, None)
        middle_state = self.current_state
        output = self._output_step_to(None, None)
        return output, middle_state

    def step_to(self, letter: string, destination: IoltsState = None) -> Optional[str]:
        """
        Next step is determined based on a uniform distribution over all transitions with possible by the given 'letter'.

        Returns the letter if a successful transition was executed otherwise returns None
        """

        if letter.startswith("?"):
            return self._input_step_to(letter, destination)

        if letter.startswith("!"):
            return self._output_step_to(letter, destination)

        if letter == 'quiescence':
            return self._quiescence_step_to()

        raise Exception("Unable to match letter")

    def _input_step_to(self, input: str, destination) -> Optional[str]:
        transitions = self.current_state.get_inputs(input, destination)
        if not transitions:
            return None

        (key, self.current_state) = choice(transitions)
        return key

    def _output_step_to(self, output: Optional[str], destination: IoltsState) -> Optional[str]:
        transitions = self.current_state.get_outputs(output, destination)
        if not transitions:
            return None

        (key, self.current_state) = choice(transitions)
        return key

    def _quiescence_step_to(self) -> Optional[str]:
        # Note can quiescence be non deterministic? if so destination is imported.
        transitions = self.current_state.get_quiescence()
        if not transitions:
            return None

        (key, self.current_state) = choice(transitions)
        return key

    def get_input_alphabet(self) -> list:
        """
        Returns the input alphabet
        """
        result: list[str] = []
        for state in self.states:
            result.extend([input for input, _ in state.get_inputs()])

        return list(set(result))

    def get_output_alphabet(self) -> list:
        """
        Returns the output alphabet
        """
        result: list[str] = []
        for state in self.states:
            result.extend([output for output, _ in state.get_outputs()])

        return list(set(result))

    def get_shortest_path(self, origin_state: AutomatonState, target_state: AutomatonState) -> tuple:
        """
        Breath First Search over the automaton

        Args:

            origin_state (AutomatonState): state from which the BFS will start
            target_state (AutomatonState): state that will be reached with the return value

        Returns:

            sequence of inputs that lead from origin_state to target state

        """
        if origin_state not in self.states or target_state not in self.states:
            raise SystemExit("State not in the automaton.")

        explored = []
        queue = [[origin_state]]

        if origin_state == target_state:
            return ()

        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node not in explored:
                neighbours = node.transitions.values()
                for neighbour in neighbours:
                    # TODO get non-deterministic neighbours 
                    neighbour = neighbour[0]
                    new_path = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)
                    # return path if neighbour is goal
                    if neighbour == target_state:
                        acc_seq = new_path[:-1]
                        inputs = []
                        for ind, state in enumerate(acc_seq):
                            inputs.append(next(key for key, value in state.transitions.items()
                                               # TODO get non-deterministic neighbours 
                                               if value[0] == new_path[ind + 1]))
                        return tuple(inputs)

                # mark node as explored
                explored.append(node)
        return ()

    def is_input_complete(self) -> bool:
        """
        Check whether all states have defined transition for all inputs
        :return: true if automaton is input complete

        Returns:

            True if input complete, False otherwise

        """
        alphabet = set(self.get_input_alphabet())
        for state in self.states:
            if state.inputs.keys() != alphabet:
                return False
        return True

    def make_input_complete(self):
        alphabet = self.get_input_alphabet()
        for state in self.states:
            state.make_input_complete(alphabet)


class IocoValidator:

    def __init__(self, specification: IoltsMachine):
        self.specification: IoltsMachine = deepcopy(specification)

        self.states = []
        self.visited = []
        self.state_count = 0

        self.passed_states = set()
        self.failed_states = set()

        self.initial_state = self._new_node_state()
        self._resolve_state(self.specification.initial_state, self.initial_state)

        for state in self.states:
            self._remove_false_state(state)

        self.automata: IoltsMachine = IoltsMachine(self.initial_state, self.states)

    def _new_node_state(self, suffix: str = None):
        self.state_count += 1
        if suffix:
            state = IoltsState(f't{self.state_count} {suffix}')
        else:
            state = IoltsState(f't{self.state_count}')

        self.states.append(state)
        return state

    def _new_passed_state(self):
        state = self._new_node_state("passed")
        self.passed_states.add(state)
        return state

    def _new_failed_state(self):
        state = self._new_node_state("failed")
        self.failed_states.add(state)
        return state

    def _resolve_state(self, original_state: IoltsState, test_state: IoltsState):

        follow_state = dict()

        for input in self.specification.get_input_alphabet():
            destinations = [state for _, state in original_state.get_inputs(input)]
            follow_state.update(self._resolve_inputs(original_state, test_state, destinations, input))

        for output in self.specification.get_output_alphabet():
            destinations = [state for _, state in original_state.get_outputs(output)]
            follow_state.update(self._resolve_outputs(original_state, test_state, destinations, output))

        destinations = [state for _, state in original_state.get_quiescence()]
        follow_state.update(self._resolve_quiescence(original_state, test_state, destinations))

        self.visited.append(original_state)
        for specification_state, new_test_state in follow_state.items():
            if specification_state not in self.visited:
                self._resolve_state(specification_state, new_test_state)

    def _resolve_inputs(self, original_state: IoltsState, test_state: IoltsState, destinations: list[IoltsState],
                        letter: str) -> dict:
        follow_state = dict()

        if not destinations:
            test_state.add_output(input.replace("?", "!"), self._new_failed_state())
        else:
            new_test_state = self._new_node_state()
            for state in destinations:
                if state == original_state:
                    test_state.add_output(letter.replace("?", "!"), test_state)
                else:
                    test_state.add_output(letter.replace("?", "!"), new_test_state)
                    follow_state.update({state: new_test_state})

        return follow_state

    def _resolve_outputs(self, original_state: IoltsState, test_state: IoltsState, destinations: list[IoltsState],
                         letter: str) -> dict:
        follow_state = dict()

        if not destinations:
            test_state.add_input(letter.replace("!", "?"), self._new_failed_state())
        else:
            new_test_state = self._new_node_state()
            for state in destinations:
                if state.is_quiescence() and not state.is_input_enabled_for_diff_state():
                    test_state.add_input(letter.replace("!", "?"), self._new_passed_state())
                else:
                    test_state.add_input(letter.replace("!", "?"), new_test_state)
                    follow_state.update({state: new_test_state})

        return follow_state

    def _resolve_quiescence(self, original_state: IoltsState, test_state: IoltsState,
                            destinations: list[IoltsState]) -> dict:
        follow_state = dict()

        if not destinations:
            test_state.add_input("?quiescence", self._new_failed_state())
        else:
            new_test_state = self._new_node_state()
            for state in destinations:
                if state.is_quiescence() and state.is_input_enabled_for_diff_state() and state not in self.visited:
                    test_state.add_input("?quiescence", new_test_state)
                elif state.is_quiescence():
                    test_state.add_input("?quiescence", self._new_passed_state())

        return follow_state

    def build_automata(self, old_initial_test_state) -> IoltsMachine:

        # reset
        self.state_count = 0
        build_initial_state = None
        build_states = []

        for state in self.states.copy():
            new_state = self._post_processing(state)

            if state == old_initial_test_state:
                build_initial_state = new_state

            build_states.append(new_state)

        return IoltsMachine(build_initial_state, build_states)

    def _post_merging(self, left: IoltsState, right: IoltsState):
        merge_state = None

        left_is_passed = left in self.passed_states
        left_is_failed = left in self.failed_states
        left_is_node = not left_is_passed and not left_is_failed

        right_is_passed = right in self.passed_states
        right_is_failed = right in self.failed_states
        right_is_node = not right_is_passed and not right_is_failed

        if left_is_node and right_is_node:
            merge_state = self._new_node_state()

        if left_is_passed or right_is_passed:
            merge_state = self._new_passed_state()

        if left_is_failed or right_is_failed:
            merge_state = self._new_failed_state()

        if left_is_node and right_is_passed:
            assert "should not happen"

        if left_is_node and right_is_failed:
            assert "should not happen"

        if left_is_passed and right_is_node:
            assert "should not happen"

        if left_is_failed and right_is_node:
            assert "should not happen"

        for input, state in left.get_inputs() + right.get_inputs():
            merge_state.add_input(input, state)

        for output, state in left.get_outputs() + right.get_outputs():
            merge_state.add_input(output, state)

        return merge_state

    def _remove_false_state(self, original_state: IoltsState):
        for input in self.specification.get_input_alphabet():
            destinations = [state for _, state in original_state.get_outputs(input.replace('?', '!'))]

            contains_failed = any(state in self.failed_states for state in destinations)
            contains_non_failed = any(state not in self.failed_states for state in destinations)

            if contains_failed and contains_non_failed:
                for state in self.failed_states:
                    original_state.remove_output(input.replace('?', '!'), state)

        for output in self.specification.get_output_alphabet():
            destinations = [state for _, state in original_state.get_inputs(output.replace('!', '?'))]

            contains_failed = any(state in self.failed_states for state in destinations)
            contains_non_failed = any(state not in self.failed_states for state in destinations)

            if contains_failed and contains_non_failed:
                for state in self.failed_states:
                    original_state.remove_input(output.replace('!', '?'), state)

    def _post_processing(self, original_state: IoltsState):
        if original_state in self.passed_states:
            return self._new_passed_state()

        if original_state in self.failed_states:
            return self._new_failed_state()

        post_state = self._new_node_state()

        for input in self.specification.get_input_alphabet():
            destinations = [state for _, state in original_state.get_inputs(input)]
            while destinations:
                post_state = self._post_merging(post_state, destinations.pop())

        for output in self.specification.get_output_alphabet():
            destinations = [state for _, state in original_state.get_outputs(output)]
            while destinations:
                post_state = self._post_merging(post_state, destinations.pop())

        destinations = [state for _, state in original_state.get_quiescence()]
        while destinations:
            post_state = self._post_merging(post_state, destinations.pop())

        return post_state

    def check(self, sut: IoltsMachine) -> tuple[bool, tuple]:
        """
        Checks if the implementation is ioco to the specification ( i ioco s)

        Args:
            sut: the implementation a.k.a system under test

        Returns: True if ioco holds False if ioco is violated

        """
        assert sut.is_input_complete(), "Implementation needs to be input complete"

        for state in self.automata.states:
            if state not in self.passed_states and state not in self.failed_states:
                continue

            shortest_path = list(self.automata.get_shortest_path(self.automata.initial_state, state))
            resolved_paths = self._resolve_non_deterministic(sut, sut.initial_state.state_id, shortest_path, None, [])
            flattened_paths = self._flatten_resolved_paths(resolved_paths)

            ioco_violation = not all(self.evaluates_path(sut, path, state, shortest_path) for path in flattened_paths)

            if ioco_violation:
                cex = []
                for letter in shortest_path:
                    if letter == '?quiescence':
                        cex.append('QUIESCENCE')
                    elif letter.startswith('?'):
                        cex.append(letter.replace('?', '!'))
                    elif letter.startswith('!'):
                        cex.append(letter.replace('!', '?'))

                return False, tuple(cex)

        return True, tuple()

    def _resolve_non_deterministic(self, sut: IoltsMachine, current_state_id: str, path: list, destination_id: str,
                                   resolved_path: list):
        sut.reset_to_initial()
        sut.current_state = sut.get_state_by_id(current_state_id)

        if destination_id is not None:
            letter = path.pop(0)
            destination: IoltsState = sut.get_state_by_id(destination_id)

            if letter == "?quiescence":
                sut.step_to('quiescence', destination)
            elif letter.startswith("?"):
                sut.step_to(letter.replace("?", "!"), destination)
            elif letter.startswith("!"):
                sut.step_to(letter.replace("!", "?"), destination)

            resolved_path.append((letter, sut.current_state.state_id))

        if not path:
            return resolved_path

        next_letter = path[0]
        current_state_id = sut.current_state.state_id
        possible_destinations = []

        if next_letter == "?quiescence":
            possible_destinations = sut.current_state.get_quiescence()
        elif next_letter.startswith("?"):
            possible_destinations = sut.current_state.get_outputs(next_letter.replace("?", '!'))
        elif next_letter.startswith("!"):
            possible_destinations = sut.current_state.get_inputs(next_letter.replace("!", '?'))

        if not possible_destinations:
            resolved_path.append((next_letter, None))
            return resolved_path

        resolved_path_list = [self._resolve_non_deterministic(sut,
                                                              current_state_id,
                                                              path.copy(),
                                                              destination.state_id,
                                                              resolved_path.copy())
                              for _, destination in possible_destinations]

        return resolved_path_list

    def _flatten_resolved_paths(self, resolved_paths: list) -> list:
        result = []

        if not resolved_paths:
            return result

        if type(resolved_paths[0]) is tuple:
            return [resolved_paths]

        for item in resolved_paths:
            flatted_item = self._flatten_resolved_paths(item)
            if flatted_item and type(flatted_item[0]) is tuple:
                result.append(flatted_item)
            elif flatted_item:
                result.extend(flatted_item)

        return result

    def evaluates_path(self, sut: IoltsMachine, path: list, ioco_state: IoltsState, shortest_path: list):
        sut.reset_to_initial()
        valid_outputs = [key.replace("?", "!") for key in self.automata.get_input_alphabet()]

        for idx, (letter, destination_id) in enumerate(path):
            destination: IoltsState = sut.get_state_by_id(destination_id)

            is_input = letter.startswith("!")
            is_quiescence = letter == "?quiescence"
            is_output = letter.startswith("?") and not is_quiescence

            accepted_input = is_input and bool(sut.step_to(letter.replace("!", "?"), destination))
            accepted_output = is_output and bool(sut.step_to(letter.replace("?", "!"), destination))
            accepted_quiescence = is_quiescence and sut.current_state.is_quiescence()

            accepted_any = accepted_input or accepted_output or accepted_quiescence

            # We only handle and check the expected ioco stat at the end of the path
            is_last_letter = (idx + 1) == len(shortest_path)
            expect_passed = is_last_letter and ioco_state in self.passed_states
            expect_failed = is_last_letter and ioco_state in self.failed_states

            violation_on_expect_passed = expect_passed and not sut.current_state.is_quiescence()
            violation_on_expect_failed = expect_failed and accepted_any

            # If the test case triggers an output that is unknown to the specification, the implantation violates ioco.
            invalid_output = any(output not in valid_outputs for output, _ in sut.current_state.get_outputs())

            # If the implantation doesn't accepted the current letter, there is no reason to continue with the evaluation.
            if not accepted_any:
                break

            if invalid_output or violation_on_expect_passed or violation_on_expect_failed:
                return False

        return True
