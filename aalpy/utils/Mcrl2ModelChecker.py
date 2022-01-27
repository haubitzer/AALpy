import os
import subprocess
import time
from pathlib import Path
from typing import Union

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine, IoltsState, QUIESCENCE
from aalpy.utils import load_automaton_from_file


class Mcrl2ModelChecker:
    safety_properties: list[tuple[str, list[tuple]]]
    liveness_properties: list[tuple[str, list[tuple]]]
    sul: IoltsMachineSUL

    def __init__(self, sul):
        self.safety_properties = []
        self.liveness_properties = []
        self.sul = sul

    def add_safety_property(self, safety_property: str, suffixes: list[tuple]):
        assert os.path.isfile(safety_property), "Path is not a file"
        self.safety_properties.append((safety_property, suffixes))

    def add_liveness_property(self, liveness_property: str, suffixes: list[tuple]):
        assert os.path.isfile(liveness_property), "Path is not a file"
        self.liveness_properties.append((liveness_property, suffixes))

    def check_safety_properties(self, model: IoltsMachine) -> tuple[bool, list[tuple[tuple, str, list[tuple]]]]:
        mcrl2 = Mcrl2Interface(model, self.sul)
        is_safe = True
        data = []

        for prop, suffixes in self.safety_properties:
            is_satisfied, cex = mcrl2.holds(prop)
            if not is_satisfied:
                is_safe = False
                data.append((cex, prop, suffixes))

        return is_safe, data

    def check_liveness_properties(self, model: IoltsMachine) -> tuple[bool, list[tuple[tuple, str, list[tuple]]]]:
        mcrl2 = Mcrl2Interface(model, self.sul)
        is_live = True
        data = []

        for prop, suffixes in self.liveness_properties:
            is_satisfied, cex = mcrl2.holds(prop)
            if not is_satisfied:
                is_live = False
                data.append((cex, prop, suffixes))

        return is_live, data


class Mcrl2Converter:
    model: IoltsMachine
    sul: IoltsMachineSUL

    def __init__(self, model: IoltsMachine, sul):
        self.model = model
        self.sul = sul

    def _act(self) -> str:
        safe_input = list(map(lambda input: input.replace('?', 'in_'), self.sul.iolts.get_input_alphabet()))
        safe_output = list(map(lambda output: output.replace('!', 'out_'), self.sul.iolts.get_output_alphabet())) + [
            QUIESCENCE]

        return f"act{os.linesep}{', '.join(safe_input)},{os.linesep}{', '.join(safe_output)};{os.linesep}"

    def _proc(self) -> str:
        processes = [self._convert_to_process(state) for state in self.model.states]
        return f"proc{os.linesep}{''.join(processes)}"

    @staticmethod
    def _convert_to_process(state: IoltsState) -> str:
        transitions: list[str] = list()

        for letter, destination in state.get_inputs():
            transitions.append(f"{letter.replace('?', 'in_')} . {destination.state_id}")

        for letter, destination in state.get_outputs():
            transitions.append(f"{letter.replace('!', 'out_')} . {destination.state_id}")

        for letter, destination in state.get_quiescence():
            transitions.append(f"{letter} . {destination.state_id}")

        if transitions:
            return f"{state.state_id} = {' + '.join(transitions)}; {os.linesep}"
        else:
            return ""

    def _init(self) -> str:
        return f"init{os.linesep} {self.model.initial_state.state_id};{os.linesep}"

    def convert(self) -> str:
        return f"{self._act()}{self._proc()}{self._init()}"


class Mcrl2Interface:

    def __init__(self, model: IoltsMachine, sul):
        self.model_as_mcrl2 = Mcrl2Converter(model, sul).convert()

    def holds(self, prop: str) -> Union[tuple[bool, None], tuple[bool, list[str]]]:
        name = Path(prop).stem
        folder = f"tmp/{name}_{time.time()}/"

        make_new_folder = f"mkdir -p {folder} && rm -r {folder} && mkdir {folder}"
        convert_to_lps = f"echo \"{self.model_as_mcrl2}\" | mcrl22lps > {folder}{name}.lps"
        convert_to_pbes = f"lps2pbes -m -s -c --formula={prop} {folder}{name}.lps {folder}{name}.pbes"
        solve_pbes = f"pbessolve --search-strategy=breadth-first --solve-strategy=1 --file={folder}{name}.lps {folder}{name}.pbes"
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

        cmd = f"{make_new_folder} && {convert_to_lps} && {convert_to_pbes} && {solve_pbes} && {cex_to_lts} && {lts_to_dot} && {replace_in} && {replace_out} && {add_start0} && {remove_empty_label} && {remove_old_start_node}"

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        result = stdout.decode("utf-8").rstrip()

        if result == "true":
            return True, None
        elif result == "false":
            if not self.get_counter_example(f"{folder}{name}.pbes.evidence.dot"):
                self.get_counter_example(f"{folder}{name}.pbes.evidence.dot")

            return False, self.get_counter_example(f"{folder}{name}.pbes.evidence.dot")
        else:

            print(cmd)
            print(stderr)
            print(stdout)
            raise Exception("Something went wrong in the mcrl2 part!")

    @staticmethod
    def get_counter_example(path: str) -> list[str]:
        trace = list()
        visited = set()
        automaton: IoltsMachine = load_automaton_from_file(path, "iolts")

        while True:
            visited.add(automaton.initial_state)

            letters, states = automaton.random_unroll_step()

            if letters:
                trace.extend(letters)
            else:
                return trace

            if visited != set(automaton.states):
                for state in states:
                    visited.add(state)
            else:
                return trace
