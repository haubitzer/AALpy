from unittest import TestCase

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine, IocoValidator
from aalpy.learning_algs.approximate.ApproximatedIoltsLstar import run_approximated_Iolts_Lstar
from aalpy.utils import load_automaton_from_file, save_automaton_to_file

test_cases = [
    ("../../DotModels/Iolts/01_iolts.dot",),
    ("../../DotModels/Iolts/02_iolts.dot",),
    ("../../DotModels/Iolts/03_iolts.dot",),
    # Loop ("../../DotModels/Iolts/04_iolts.dot",),
    # Loop sometimes ("../../DotModels/Iolts/05_iolts.dot",),
    ("../../DotModels/Iolts/06_iolts.dot",),
    ("../../DotModels/Iolts/07_iolts.dot",),
    ("../../DotModels/Iolts/08_iolts.dot",),
    ("../../DotModels/Iolts/09_iolts.dot",),
    ("../../DotModels/Iolts/10_iolts.dot",),

]


class ApproximatedIoltsLstarTest(TestCase):

    def test_approximated_iolts_lstar(self):
        for spec_path, in test_cases:
            print('#################################################################')
            print("Start testing: " + spec_path)
            specification: IoltsMachine = load_automaton_from_file(spec_path, 'iolts')

            sul = IoltsMachineSUL(specification)

            h_minus = None
            h_plus = None

            with self.subTest(msg="Build H+ and H-", S=spec_path.split('/')[-1]):
                h_minus, h_plus = run_approximated_Iolts_Lstar(specification.get_input_alphabet(),
                                                               specification.get_output_alphabet(), sul)

            with self.subTest(msg="SUL ioco SUL:", S=spec_path.split('/')[-1]):
                actual, cex = IocoValidator(specification).check(specification)
                self.assertTrue(actual, "SUL is not ioco to SUL: " + str(cex))

            with self.subTest(msg="H- ioco SUL:", S=spec_path.split('/')[-1]):
                actual, cex = IocoValidator(specification).check(h_minus)
                self.assertTrue(actual, "H_minus is not ioco to SUL: " + str(cex))

            with self.subTest(msg="SUL ioco H+:", S=spec_path.split('/')[-1]):
                actual, cex = IocoValidator(h_plus).check(specification)
                self.assertTrue(actual, "SUL is not ioco to H_plus: " + str(cex))
