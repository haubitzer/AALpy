from aalpy.automata import IoltsMachine


class ModelChecker:
    output_alphabet: list
    input_alphabet: list
    safety_properties: list[str]
    liveness_properties: list[str]

    def __init__(self, input_alphabet: list[str], output_alphabet: list[str]):
        self.input_alphabet = input_alphabet
        self.output_alphabet = output_alphabet

        self.safety_properties = []
        self.liveness_properties = []

    def add_safety_property(self, safety_property: str):
        self.safety_properties.append(safety_property)

    def add_liveness_property(self, liveness_property: str):
        self.liveness_properties.append(liveness_property)

    def check_safety_properties(self, model: IoltsMachine) -> tuple[tuple, tuple[str], str]:
        pass

    def check_liveness_properties(self, model: IoltsMachine) -> tuple[tuple, tuple[str], str]:
        pass
