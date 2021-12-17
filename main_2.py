from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine
from aalpy.learning_algs.approximate.ApproximatedIoltsLstar import run_approximated_Iolts_Lstar
from aalpy.learning_algs.approximate.PrecisionOracle import ModelCheckerPrecisionOracle
from aalpy.utils import load_automaton_from_file, Mcrl2ModelChecker

specification: IoltsMachine = load_automaton_from_file("cas_diamond_chaos_dontcare/cas_diamond_openwait_chaos.dot", "iolts")

print(specification)

specification.make_input_complete()
specification.remove_self_loops_from_non_quiescence_states()

print(specification)

sul = IoltsMachineSUL(specification, 0.95, 0.95)

checker = Mcrl2ModelChecker(sul)
#checker.add_liveness_property("./DotModels/Iolts/car_alarm_system/liveness_property.mcf")
#checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_1.mcf")
#checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_2.mcf")
#checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_3.mcf")
#checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_4.mcf")
# checker.add_safety_property("./DotModels/Iolts/car_alarm_system/02_requirement_1.mcf")
# checker.add_safety_property("./DotModels/Iolts/car_alarm_system/02_requirement_2.mcf")
# checker.add_safety_property("./DotModels/Iolts/car_alarm_system/03_requirement_1.mcf")
# checker.add_safety_property("./DotModels/Iolts/car_alarm_system/04_requirement_2.mcf")

checker.add_safety_property("./cas_diamond_chaos_dontcare/cas_diamond_openclosed_armed_chaos_checking.mcf")

print(checker.check_safety_properties(specification))


