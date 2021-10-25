import os
from typing import Union

from aalpy.automata import IoltsMachine, IoltsState


class Mcrl2ModelChecker:
    safety_properties: list[str]
    liveness_properties: list[str]

    def __init__(self):
        self.safety_properties = []
        self.liveness_properties = []

    def add_safety_property(self, safety_property: str):
        self.safety_properties.append(safety_property)

    def add_liveness_property(self, liveness_property: str):
        self.liveness_properties.append(liveness_property)

    def check_safety_properties(self, model: IoltsMachine) -> Union[tuple[bool, tuple, str], tuple[bool, None, None]]:
        for property in self.safety_properties:
            if Mcrl2Runner.run(model, property) is False:
                return False, tuple(), property

        return True, None, None

    def check_liveness_properties(self, model: IoltsMachine) -> tuple[bool, tuple[str], str]:
        pass


class Mcrl2Converter:
    model: IoltsMachine

    def __init__(self, model: IoltsMachine):
        self.model = model

    def _act(self) -> str:
        # Note add a convert function to the get_alphabet function
        safe_input = list(map(lambda input: input.replace('?', 'in_'), self.model.get_input_alphabet()))
        safe_output = list(map(lambda output: output.replace('!', 'out_'), self.model.get_output_alphabet()))

        return f"act{os.linesep}{', '.join(safe_input)},{os.linesep}{', '.join(safe_output)},{os.linesep}quiescence;{os.linesep}"

    def _proc(self) -> str:
        processes = [self._convert_to_process(state) for state in self.model.states]
        return f"proc{os.linesep}{''.join(processes)}"

    def _convert_to_process(self, state: IoltsState) -> str:
        transitions: list[str] = list()

        for letter, destination in state.get_inputs():
            transitions.append(f"{letter.replace('?', 'in_')} . {destination.state_id}")

        for letter, destination in state.get_outputs():
            transitions.append(f"{letter.replace('!', 'out_')} . {destination.state_id}")

        for letter, destination in state.get_quiescence():
            transitions.append(f"{letter} . {destination.state_id}")

        return f"{state.state_id} = {' + '.join(transitions)}; {os.linesep}"

    def _init(self) -> str:
        return f"init{os.linesep} {self.model.initial_state.state_id};{os.linesep}"

    def write(self, file):
        pass

    def convert(self) -> str:
        return f"{self._act()}{self._proc()}{self._init()}"


class Mcrl2Runner:

    @staticmethod
    def run(model: IoltsMachine, property: str):
        echo = f"echo \"{Mcrl2Converter(model).convert()}\" "
        mcrl22lps = f"mcrl22lps"
        lps2pbes = f"lps2pbes -f {property}"
        pbessolve = f"pbessolve"

        output = os.popen(f"{echo} | {mcrl22lps} | {lps2pbes} | {pbessolve}").read()

        return output.rstrip() == "true"
