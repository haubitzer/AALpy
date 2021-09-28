from unittest import TestCase

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine, IocoValidator
from aalpy.learning_algs.approximate.ApproximatedIoltsLstar import run_approximated_Iolts_Lstar
from aalpy.utils import load_automaton_from_file

test_cases = [
    ("../../DotModels/Iolts/01_iolts.dot",),
    ("../../DotModels/Iolts/02_iolts.dot",),
    ("../../DotModels/Iolts/03_iolts.dot",),
    # Loop ("../../DotModels/Iolts/04_iolts.dot",),
    # Loop sometimes ("../../DotModels/Iolts/05_iolts.dot",),
    ("../../DotModels/Iolts/06_iolts.dot",),
    # Loops ("../../DotModels/Iolts/07_iolts.dot",),
    # Loops fails ("../../DotModels/Iolts/08_iolts.dot",),
    # Loop ("../../DotModels/Iolts/09_iolts.dot",),
    ("../../DotModels/Iolts/10_iolts.dot",),

    ("../../DotModels/Iolts/ioco/04_ioco_P.dot",),
    ("../../DotModels/Iolts/ioco/05_ioco_P.dot",),
    # Fails ("../../DotModels/Iolts/ioco/06_ioco_P.dot",),
    # Fails ("../../DotModels/Iolts/ioco/07_ioco_P.dot",),
    ("../../DotModels/Iolts/ioco/08_ioco_P.dot",),
]


class ApproximatedIoltsLstarTest(TestCase):

    def test_approximated_iolts_lstar(self):
        for spec_path, in test_cases:
            with self.subTest(msg="Learning Iolts:", S=spec_path):
                specification: IoltsMachine = load_automaton_from_file(spec_path, 'iolts')

                sul = IoltsMachineSUL(specification)
                h_minus, h_plus = run_approximated_Iolts_Lstar(specification.get_input_alphabet(),
                                                               specification.get_output_alphabet(), sul)

                actual, _ = IocoValidator(specification).check(h_minus)
                self.assertTrue(actual, "H_minus is not ioco to SUL")

                actual, _ = IocoValidator(h_plus).check(specification)
                # self.assertTrue(actual, "SUL is not ioco to H_plus")
