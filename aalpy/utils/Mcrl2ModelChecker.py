import os
from typing import Union
from pathlib import Path
from random import choices

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine, IoltsState
from aalpy.utils import load_automaton_from_file


class Mcrl2ModelChecker:
    safety_properties: list[str]
    liveness_properties: list[str]
    sul: IoltsMachineSUL

    def __init__(self, sul):
        self.safety_properties = []
        self.liveness_properties = []
        self.sul = sul

    def add_safety_property(self, safety_property: str):
        # TODO check if path exits
        self.safety_properties.append(safety_property)

    def add_liveness_property(self, liveness_property: str):
        self.liveness_properties.append(liveness_property)

    def check_safety_properties(self, model: IoltsMachine) -> Union[tuple[bool, tuple, str], tuple[bool, None, None]]:
        mcrl2 = Mcrl2Interface(model, self.sul)

        # results = [mcrl2.holds(property) for property in self.safety_properties]

        for property in self.safety_properties:
            is_satisfied, cex = mcrl2.holds(property)
            if not is_satisfied:
                return False, cex, property

        return True, None, None

    def check_liveness_properties(self, model: IoltsMachine) -> Union[tuple[bool, tuple, str], tuple[bool, None, None]]:
        mcrl2 = Mcrl2Interface(model, self.sul)

        for property in self.liveness_properties:
            is_satisfied, cex = mcrl2.holds(property)
            if not is_satisfied:
                return False, cex, property

        return True, None, None


class Mcrl2Converter:
    model: IoltsMachine
    sul: IoltsMachineSUL

    def __init__(self, model: IoltsMachine, sul):
        self.model = model
        self.sul = sul

    def _act(self) -> str:
        # Note add a convert function to the get_alphabet function
        safe_input = list(map(lambda input: input.replace('?', 'in_'), self.sul.iolts.get_input_alphabet()))
        safe_output = list(map(lambda output: output.replace('!', 'out_'), self.sul.iolts.get_output_alphabet())) + ['quiescence']

        return f"act{os.linesep}{', '.join(safe_input)},{os.linesep}{', '.join(safe_output )};{os.linesep}"

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

    def convert(self) -> str:
        return f"{self._act()}{self._proc()}{self._init()}"


class Mcrl2Interface:

    def __init__(self, model: IoltsMachine, sul):
        self.model_as_mcrl2 = Mcrl2Converter(model, sul).convert()

    def holds(self, property: str) -> Union[tuple[bool, None], tuple[bool, tuple[str]]]:
        name = Path(property).stem
        folder = "tmp/"

        make_new_folder = f"mkdir -p {folder} && rm -r {folder} && mkdir {folder}"
        convert_to_lps = f"echo \"{self.model_as_mcrl2}\" | mcrl22lps > {folder}{name}.lps"
        convert_to_pbes = f"lps2pbes -m -c --formula={property} {folder}{name}.lps {folder}{name}.pbes"
        solve_pbes = f"pbessolve --search-strategy=depth-first --solve-strategy=3 --file={folder}{name}.lps {folder}{name}.pbes"
        cex_to_lts = f"lps2lts {folder}{name}.pbes.evidence.lps {folder}{name}.pbes.evidence.lts"
        lts_to_dot = f"ltsconvert {folder}{name}.pbes.evidence.lts {folder}{name}.pbes.evidence.dot"
        replace_in = f"sed -i 's/in_/?/g' {folder}{name}.pbes.evidence.dot"
        replace_out = f"sed -i 's/out_/!/g' {folder}{name}.pbes.evidence.dot"
        add_start0 = f"sed -i 's/}}/" \
                     f"__start0 [label=\"\", shape=none];" \
                     f"__start0 -> s0  [label=\"\"];" \
                     f"}}/g' {folder}{name}.pbes.evidence.dot"

        remove_empty_label = f"sed -i 's/ \[label=\"()\"\];/;/g' {folder}{name}.pbes.evidence.dot"
        remove_old_start_node = f"sed -i 's/node \[ width=0.25, height=0.25, label=\"\" \];//g' {folder}{name}.pbes.evidence.dot"

        output = os.popen(
            f"{make_new_folder} && {convert_to_lps} && {convert_to_pbes} && {solve_pbes} && {cex_to_lts} && {lts_to_dot} && {replace_in} && {replace_out} && {add_start0} && {remove_empty_label} && {remove_old_start_node}").read().rstrip()

        print(output)

        if output == "true":
            return True, None
        else:
            print(property)
            return False, self.getCounterexample(f"{folder}{name}.pbes.evidence.dot")

    def getCounterexample(self, path: str) -> tuple[str]:
        trace = list()
        visited = set()
        automaton: IoltsMachine = load_automaton_from_file(path, "iolts")

        print(automaton)

        while True:
            letters, states = automaton.random_unroll_step()

            if letters:
                trace.extend(letters)

            for state in states:
                visited.add(state)

            if not letters or visited == set(automaton.states):
                return trace
