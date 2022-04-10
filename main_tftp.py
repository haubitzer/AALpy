import random

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine
from aalpy.learning_algs.approximate.ApproximatedIoltsLstar import run_approximated_Iolts_Lstar
from aalpy.learning_algs.approximate.PrecisionOracle import ModelCheckerPrecisionOracle
from aalpy.utils import load_automaton_from_file, Mcrl2ModelChecker

specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/tftp_download/00_download.dot", "iolts")

print(specification)

sul = IoltsMachineSUL(specification, 0.90, 0.90)

checker = Mcrl2ModelChecker(sul)
checker.add_liveness_property("./DotModels/Iolts/tftp_download/liveness_property.mcf", [('?ACK',),('!DATA',)])
checker.add_safety_property("./DotModels/Iolts/tftp_download/01_requirement_1.mcf", [])
checker.add_safety_property("./DotModels/Iolts/tftp_download/01_requirement_2.mcf", [('?ACK',), ('!DATA',)])
checker.add_safety_property("./DotModels/Iolts/tftp_download/01_requirement_3.mcf", [])
checker.add_safety_property("./DotModels/Iolts/tftp_download/01_requirement_4.mcf", [])

sul_holds, data = checker.check_safety_properties(specification)

if not sul_holds:
    print(data)
    exit(1)

sul_holds, data = checker.check_liveness_properties(specification)

if not sul_holds:
    print(data)
    exit(1)

print("Specification is correct!")
print("---------------------")

oracle = ModelCheckerPrecisionOracle(sul, checker)

h_minus, h_plus, h_star = run_approximated_Iolts_Lstar(specification.get_input_alphabet(), specification.get_output_alphabet(),
                                               sul, oracle)

print(h_minus)
print(h_plus)
print(h_star)

