from __future__ import annotations

import itertools
import string
from collections import defaultdict
from random import choice
from typing import Optional

from aalpy.base import Automaton, AutomatonState

QUIESCENCE = 'QUIESCENCE'


class IoltsState(AutomatonState):
    def __init__(self, state_id):
        super().__init__(state_id)
        # Note: inputs/outputs maps to tuples of possible new state e.g. input => (state1, state2)
        self.inputs = defaultdict(tuple)
        self.outputs = defaultdict(tuple)
        self.quiescence = defaultdict(tuple)
        self.add_quiescence(None)

    def get_inputs(
            self, input: string = None, destination: IoltsState = None
    ) -> list[tuple[str, IoltsState]]:
        assert input is None or input.startswith("?")

        result = [
            (input, state) for input, states in self.inputs.items() for state in states
        ]
        result = (
            result
            if input is None
            else list(filter(lambda elm: elm[0] == input, result))
        )
        result = (
            result
            if destination is None
            else list(filter(lambda elm: elm[1] == destination, result))
        )

        return result

    def get_outputs(
            self, output: string = None, destination: IoltsState = None
    ) -> list[tuple[str, IoltsState]]:
        assert output is None or output.startswith("!")

        result = [
            (output, state)
            for output, states in self.outputs.items()
            for state in states
        ]
        result = (
            result
            if output is None
            else list(filter(lambda elm: elm[0] == output, result))
        )
        result = (
            result
            if destination is None
            else list(filter(lambda elm: elm[1] == destination, result))
        )

        return result

    def get_quiescence(self, destination: IoltsState = None) -> list[tuple[str, IoltsState]]:

        result = [
            (quiescence, state)
            for quiescence, states in self.quiescence.items()
            for state in states
        ]

        result = (
            result
            if destination is None
            else list(filter(lambda elm: elm[1] == destination, result))
        )

        return result

    def add_input(self, input: string, new_state: IoltsState):
        assert input.startswith("?")

        new_value = (
            tuple([new_state]) + self.inputs[input]
            if input in self.inputs
            else tuple([new_state])
        )
        self.inputs.update({input: new_value})
        self.transitions.update(self.inputs)

    def add_output(self, output: string, new_state):
        assert output.startswith("!")

        new_value = (
            tuple([new_state]) + self.outputs[output]
            if output in self.outputs
            else tuple([new_state])
        )
        self.outputs.update({output: new_value})
        self.transitions.update(self.outputs)
        # clear the quiescence entries, the are not valid
        self.quiescence.clear()
        self.transitions.pop(QUIESCENCE, None)

    def add_quiescence(self, new_state: IoltsState = None):
        if new_state is None:
            new_state = self

        new_value = (
            tuple([new_state]) + self.quiescence[QUIESCENCE]
            if QUIESCENCE in self.quiescence
            else tuple([new_state])
        )
        self.quiescence.update({QUIESCENCE: tuple(set(list(new_value)))})
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

    def remove_quiescence(self, new_state):
        new_value = list(self.quiescence[QUIESCENCE])
        if new_state in new_value:
            new_value.remove(new_state)
        self.quiescence.update({QUIESCENCE: tuple(new_value)})
        self.transitions.update(self.quiescence)

    def is_input_enabled(self) -> bool:
        """
        A state is input enabled if an input can trigger an transition.

        Returns:
            bool: input enabled flag
        """
        return any(self.inputs.values())

    def is_input_enabled_for_diff_state(
            self,
    ) -> bool:
        return (
                any(self not in states for states in self.inputs.values()) and self.inputs
        )

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

    def get_diff_state_transitions(self) -> list:
        """
        Returns a list of transitions that lead to new states, not same-state transitions.
        """
        transitions = []
        for trans, states in self.transitions.items():
            if self not in states:
                transitions.append(trans)
        return transitions


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
        assert letter.startswith("?")
        return self.step_to(letter, None)

    def step_to(self, letter: string, destination: IoltsState = None) -> Optional[str]:
        """
        Next step is determined based on a uniform distribution over all transitions which are possible by the given 'letter'.

        Returns the letter if a successful transition was executed otherwise returns None
        """

        if letter.startswith("?"):
            return self._input_step_to(letter, destination)

        if letter.startswith("!"):
            return self._output_step_to(letter, destination)

        if letter == QUIESCENCE:
            return self._quiescence_step_to()

        raise Exception("Unable to match letter")

    def listen(self):
        return self._output_step_to(None, None) or QUIESCENCE

    def random_unroll_step(self) -> tuple[list[str], list[IoltsState]]:
        """
        This step function make a self loop transition if possible and a random transition to a different state.
        Quiescence does not count as transition. Non-det may lead to an exception.

        If no transition are possible the function return two empty lists.
        """
        same_state_trans = self.current_state.get_same_state_transitions()
        diff_state_trans = self.current_state.get_diff_state_transitions()

        if QUIESCENCE in same_state_trans: same_state_trans.remove(QUIESCENCE)
        if QUIESCENCE in diff_state_trans: diff_state_trans.remove(QUIESCENCE)

        trace = []
        visited = []

        if same_state_trans:
            letter = choice(same_state_trans)
            self.step_to(letter, self.current_state)
            trace.append(letter)
            visited.append(self.current_state)

        if diff_state_trans:
            old_current_state = self.current_state
            letter = choice(diff_state_trans)
            self.step_to(letter)
            trace.append(letter)
            visited.append(self.current_state)

            if old_current_state == self.current_state:
                raise Exception("Different state transition was not successful")

        return trace, visited

    def query(self, word: tuple, iterations: int = 30) -> Optional[str]:
        is_valid = False

        for _ in range(iterations):
            self.reset_to_initial()
            is_valid = True
            for letter in word:
                is_valid = is_valid and self.step_to(letter) is not None
            if is_valid:
                break

        if not is_valid:
            self.reset_to_initial()
            return None

        output = self._output_step_to(None, None)
        self.reset_to_initial()

        return output if output is not None else QUIESCENCE

    def _input_step_to(
            self, input: str, destination: IoltsState = None
    ) -> Optional[str]:
        transitions = self.current_state.get_inputs(input, destination)
        if not transitions:
            return None

        (key, self.current_state) = choice(transitions)
        return key

    def _output_step_to(
            self, output: Optional[str], destination: IoltsState = None
    ) -> Optional[str]:
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

    def get_shortest_path(
            self, origin_state: AutomatonState, target_state: AutomatonState
    ) -> tuple:
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
                            inputs.append(
                                next(
                                    key
                                    for key, value in state.transitions.items()
                                    # TODO get non-deterministic neighbours
                                    if value[0] == new_path[ind + 1]
                                )
                            )
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
        return all(state.inputs.keys() == alphabet for state in self.states)

    def make_input_complete(self):
        """
        Adds self-loops for missing input transition to make the automata input complete.
        This process is also called Angelic completion.
        """
        for state, letter in itertools.product(self.states, self.get_input_alphabet()):
            if not state.get_inputs(letter):
                state.add_input(letter, state)

    def remove_self_loops_from_non_quiescence_states(self):
        for state, letter in itertools.product(self.states, self.get_input_alphabet()):
            if not state.is_quiescence():
                state.remove_input(letter, state)

    def merge_into(self, target, source):
        state: IoltsState
        for state, letter in itertools.product(self.states, self.get_input_alphabet()):
            if state.get_inputs(letter, source):
                state.remove_input(letter, source)
                state.add_input(letter, target)

        for state, letter in itertools.product(self.states, self.get_output_alphabet()):
            if state.get_outputs(letter, source):
                state.remove_output(letter, source)
                state.add_output(letter, target)

        for state in self.states:
            if state.get_quiescence(source):
                state.remove_quiescence(source)
                state.add_quiescence(target)

        self.states.remove(source)
