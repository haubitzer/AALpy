from __future__ import annotations
from collections import OrderedDict, defaultdict
from random import choice
import string

from aalpy.base import Automaton, AutomatonState


class IotsState(AutomatonState):
    def __init__(self, state_id):
        super().__init__(state_id)
        # Note: inputs/outputs maps to tuples of possible new state e.g. input => (state1, state2)
        self.inputs = defaultdict(tuple)
        self.outputs = defaultdict(tuple)

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
            new_state) + self.inputs[input] if input in self.inputs else tuple([new_state])
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
            bool: inputenabled flag
        """
        return bool(self.inputs)

    def is_quiescence(self) -> bool:
        """
        A state is quiescence if no output transition exists.

        Returns:
            bool: quiescence flag
        """
        return not bool(self.outputs)

    def is_determistic(self) -> bool:
        determistic_input = all(
            len(states) == 1 for states in self.inputs.values())
        determistic_output = all(
            len(states) == 1 for states in self.outputs.values())
        return determistic_input and determistic_output


class IotsMachine(Automaton):
    """
    Input output transition system machine.
    """

    def __init__(self, initial_state: IotsState, states: list[IotsState]):
        super().__init__(initial_state, states)
        self.current_state: IotsState
        self.states: list[IotsState]

    def step(self, input: string) -> list[str]:
        """
        Next step is determined based on a uniform distribution over all transitions with the input 'letter'.

        TODO
        I am not sure if the step() function should also work for outputs given by the caller,
        so the user can chose if the automaton steps on an input or output edge. Maybe we trigger
        always an output on the destination state, this would works very well if we restrict
        the automaton to an strict input-output chain (Martin recommend that for the beginning).
        """

        assert input.startswith('?')

        result = []

        transitions = self.current_state.get_inputs(input)

        if not transitions:
            return None

        (_, self.current_state) = choice(transitions)

        while not self.current_state.is_input_enabled():
            # TODO what happens when it never stops? because of an loop. 
            (output, self.current_state) = choice(self.current_state.get_outputs())
            result.append(output)

        return result

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
