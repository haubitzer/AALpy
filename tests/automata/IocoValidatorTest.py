from unittest import TestCase

from aalpy.automata import IoltsMachine, IocoValidator
from aalpy.utils import load_automaton_from_file

test_cases = [
    ("../../DotModels/Iolts/ioco/01_ioco_S.dot", "../../DotModels/Iolts/ioco/01_ioco_P.dot", True),
    ("../../DotModels/Iolts/ioco/02_ioco_S.dot", "../../DotModels/Iolts/ioco/02_ioco_P.dot", True),
    ("../../DotModels/Iolts/ioco/03_ioco_S.dot", "../../DotModels/Iolts/ioco/03_ioco_P.dot", False),
    ("../../DotModels/Iolts/ioco/04_ioco_S.dot", "../../DotModels/Iolts/ioco/04_ioco_P.dot", True),
    ("../../DotModels/Iolts/ioco/05_ioco_S.dot", "../../DotModels/Iolts/ioco/05_ioco_P.dot", True),
    ("../../DotModels/Iolts/ioco/06_ioco_S.dot", "../../DotModels/Iolts/ioco/06_ioco_P.dot", False),
    ("../../DotModels/Iolts/ioco/07_ioco_S.dot", "../../DotModels/Iolts/ioco/07_ioco_P.dot", True),
    ("../../DotModels/Iolts/ioco/08_ioco_S.dot", "../../DotModels/Iolts/ioco/08_ioco_P.dot", True),
]


class IocoValidatorTest(TestCase):

    def test_ioco_check(self):
        for spec_path, impl_path, expect in test_cases:
            with self.subTest(msg="Checking if ioco relation between:", S=spec_path, P=impl_path, E=expect):
                specification: IoltsMachine = load_automaton_from_file(spec_path, 'iolts')
                implementation: IoltsMachine = load_automaton_from_file(impl_path, 'iolts')
                actual, _ = IocoValidator(specification).check(implementation)

                self.assertEqual(actual, expect)
