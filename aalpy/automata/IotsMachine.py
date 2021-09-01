from __future__ import annotations

import string
from collections import defaultdict
from copy import deepcopy
from random import choice
from typing import Optional

from aalpy.base import Automaton, AutomatonState


class IotsState(AutomatonState):
    def __init__(self, state_id):
        super().__init__(state_id)
        # Note: inputs/outputs maps to tuples of possible new state e.g. input => (state1, state2)
        self.inputs = defaultdict(tuple)
        self.outputs = defaultdict(tuple)
        # Note: workaround for ioco
        self.ioco_status = None

    def get_inputs(self, input: string = None, destination: IotsState = None) -> list[tuple[str, IotsState]]:
        assert input is None or input.startswith('?')

        result = [(input, state)
                  for input, states in self.inputs.items() for state in states]
        result = result if input is None else list(
            filter(lambda elm: elm[0] == input, result))
        result = result if destination is None else list(
            filter(lambda elm: elm[1] == destination, result))

        return result

    def get_outputs(self, output: string = None, destination: IotsState = None) -> list[tuple[str, IotsState]]:
        assert output is None or output.startswith('!')

        result = [(output, state)
                  for output, states in self.outputs.items() for state in states]
        result = result if output is None else list(
            filter(lambda elm: elm[0] == output, result))
        result = result if destination is None else list(
            filter(lambda elm: elm[1] == destination, result))

        return result

    def add_input(self, input: string, new_state: IotsState):
        assert input.startswith('?')

        new_value = tuple(
            [new_state]) + self.inputs[input] if input in self.inputs else tuple([new_state])
        self.inputs.update({input: new_value})
        self.transitions.update(self.inputs)

    def add_output(self, output: string, new_state):
        assert output.startswith('!')

        new_value = tuple(
            new_state) + self.outputs[output] if output in self.outputs else tuple([new_state])
        self.outputs.update({output: new_value})
        self.transitions.update(self.outputs)

    def is_input_enabled(self) -> bool:
        """
        A state is input enabled if an input can trigger an transition.

        Returns:
            bool: input enabled flag
        """
        return any(self.inputs.values())

    def is_input_enabled_for_diff_state(self) -> bool:
        return all(self not in states for states in self.inputs.values())

    def is_quiescence(self) -> bool:
        """
        A state is quiescence if no output transition exists.

        Returns:
            bool: quiescence flag
        """
        return not any(self.outputs.values())

    def is_deterministic(self) -> bool:
        deterministic_input = all(
            len(states) == 1 for states in self.inputs.values())
        deterministic_output = all(
            len(states) == 1 for states in self.outputs.values())
        return deterministic_input and deterministic_output


class IotsMachine(Automaton):
    """
    Input output transition system machine.
    """

    def __init__(self, initial_state: IotsState, states: list[IotsState]):
        super().__init__(initial_state, states)
        self.current_state: IotsState
        self.initial_state: IotsState
        self.states: list[IotsState]

    def step(self, letter: string, destination: IotsState = None) -> Optional[str]:
        """
        Next step is determined based on a uniform distribution over all transitions with possible by the given 'letter'.

        Returns the key if a successful transition was executed otherwise returns None
        """

        def input_step(input: str, destination) -> Optional[str]:
            transitions = self.current_state.get_inputs(input, destination)
            if not transitions:
                return None

            (key, self.current_state) = choice(transitions)
            return key

        def output_step(output: str, destination) -> Optional[str]:
            transitions = self.current_state.get_outputs(output, destination)
            if not transitions:
                return None

            (key, self.current_state) = choice(transitions)
            return key

        if letter.startswith("?"):
            return input_step(letter, destination)

        if letter.startswith("!"):
            return output_step(letter, destination)

        # Add support for step without requiring a letter from the caller
        raise Exception("Unable to match letter")

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


class IocoValidator:

    def __init__(self, specification: IotsMachine):
        self.specification: IotsMachine = deepcopy(specification)

        self.states = []
        self.visited = []
        self.state_count = 0

        self.initial_state = self._new_test_state()
        self._resolve_state(self.specification.initial_state, self.initial_state)

        self.automata: IotsMachine = IotsMachine(self.initial_state, self.states)

    def _new_test_state(self):
        self.state_count += 1
        state = IotsState(f't{self.state_count}')
        state.ioco_status = "test"
        self.states.append(state)
        return state

    def _new_passed_state(self):
        state = self._new_test_state()
        state.ioco_status = "passed"
        state.state_id += " passed"
        return state

    def _new_failed_state(self):
        state = self._new_test_state()
        state.ioco_status = "failed"
        state.state_id += " failed"
        return state

    def _resolve_state(self, original_state: IotsState, test_state: IotsState):
        self.visited.append(original_state)

        follow_state = dict()

        for input in self.specification.get_input_alphabet():
            states = original_state.inputs[input]

            if not states:
                test_state.add_output(input.replace("?", "!"), self._new_failed_state())
            else:
                new_test_state = self._new_test_state()
                result = self._resolve_outputs(new_test_state, states)

                follow_state.update(result)
                test_state.add_output(input.replace("?", "!"), new_test_state)

        self._resolve_outputs(test_state, [original_state])

        for specification_state, ioco_state in follow_state.items():
            if specification_state not in self.visited:
                self._resolve_state(specification_state, ioco_state)

    def _resolve_outputs(self, test_state, states) -> dict:
        follow_state = dict()
        for destination in states:

            if destination.is_quiescence() and destination.is_input_enabled_for_diff_state() and destination not in self.visited:
                new_test_state = self._new_test_state()
                test_state.add_input("?quiescence", new_test_state)
                follow_state.update({destination: new_test_state})
            elif destination.is_quiescence() and destination.is_input_enabled_for_diff_state():
                test_state.add_input("?quiescence", self._new_passed_state())
            else:
                test_state.add_input("?quiescence", self._new_failed_state())

            for output in self.specification.get_output_alphabet():
                transitions = destination.outputs[output]

                if not transitions:
                    test_state.add_input(output.replace("!", "?"), self._new_failed_state())

                for state in transitions:
                    if state.is_quiescence() and not state.is_input_enabled_for_diff_state():
                        test_state.add_input(output.replace("!", "?"), self._new_passed_state())
                    else:
                        new_test_state = self._new_test_state()
                        test_state.add_input(output.replace("!", "?"), new_test_state)
                        follow_state.update({state: new_test_state})

        return follow_state

    def check(self, sut: IotsMachine) -> bool:
        """
        Checks if the implementation is ioco to the specification ( i ioco s)

        Args:
            sut: the implementation a.k.a system under test

        Returns: True if ioco holds False if ioco is violated

        """
        for state in self.automata.states:
            if state.ioco_status == "test":
                continue

            shortest_path = list(self.automata.get_shortest_path(self.automata.initial_state, state))
            resolved_paths = self._resolve_non_deterministic(sut, sut.initial_state.state_id, shortest_path, None, [])
            flattened_paths = self._flatten_resolved_paths(resolved_paths)

            ioco_violation = not all(self.evaluates_path(sut, path, state, shortest_path) for path in flattened_paths)

            if ioco_violation:
                return False

        return True

    def _resolve_non_deterministic(self, sut: IotsMachine, current_state_id: str, path: list, destination_id: str,
                                   resolved_path: list):
        sut.reset_to_initial()
        sut.current_state = sut.get_state_by_id(current_state_id)

        if destination_id is not None:
            letter = path.pop(0)
            destination = sut.get_state_by_id(destination_id)

            if letter == "?quiescence":
                pass
            elif letter.startswith("?"):
                sut.step(letter.replace("?", "!"), destination)
            elif letter.startswith("!"):
                sut.step(letter.replace("!", "?"), destination)

            resolved_path.append((letter, sut.current_state.state_id))

        if not path:
            return resolved_path

        next_letter = path[0]
        current_state_id = sut.current_state.state_id
        possible_destinations = []

        if next_letter == "?quiescence":
            possible_destinations = [(next_letter, sut.current_state)]
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

    def evaluates_path(self, sut: IotsMachine, path: list, ioco_state: IotsState, shortest_path: list):
        sut.reset_to_initial()
        valid_outputs = [key.replace("?", "!") for key in self.automata.get_input_alphabet()]

        for idx, (letter, destination_id) in enumerate(path):
            destination: IotsState = sut.get_state_by_id(destination_id)

            is_input = letter.startswith("!")
            is_quiescence = letter == "?quiescence"
            is_output = letter.startswith("?") and not is_quiescence

            accepted_input = is_input and bool(sut.step(letter.replace("!", "?"), destination))
            accepted_output = is_output and bool(sut.step(letter.replace("?", "!"), destination))
            accepted_quiescence = is_quiescence and sut.current_state.is_quiescence()

            accepted_any = accepted_input or accepted_output or accepted_quiescence

            # We only handle and check the expected ioco stat at the end of the path
            is_last_letter = (idx + 1) == len(shortest_path)
            expect_passed = is_last_letter and ioco_state.ioco_status == "passed"
            expect_failed = is_last_letter and ioco_state.ioco_status == "failed"

            violation_on_expect_passed = expect_passed and not accepted_quiescence
            violation_on_expect_failed = expect_failed and accepted_any
            
            # If the test case triggers an output that is unknown to the specification, the implantation violates ioco.
            invalid_output = any(output not in valid_outputs for output, _ in sut.current_state.get_outputs())

            if invalid_output or violation_on_expect_passed or violation_on_expect_failed:
                return False
           
            # If the implantation doesn't accepted the current letter, there is no reason to continue with the evaluation.
            if not accepted_any:
                break

        return True
