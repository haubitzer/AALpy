import random
import time

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine
from aalpy.learning_algs.approximate.ApproximatedIoltsLstar import run_approximated_Iolts_Lstar
from aalpy.learning_algs.approximate.PrecisionOracle import ModelCheckerPrecisionOracle
from aalpy.utils import load_automaton_from_file, Mcrl2ModelChecker


def get_sul():
    specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/car_alarm_system/02_car_alarm.dot", "iolts")
    return IoltsMachineSUL(specification, 0.99, 0.99)


def get_model_checker(sul):
    checker = Mcrl2ModelChecker(sul)
    checker.add_liveness_property("./DotModels/Iolts/car_alarm_system/liveness_property.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_1.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_2.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_3.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_4.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/02_requirement_1.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/02_requirement_2.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/03_requirement_1.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/05_requirement_1.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/05_requirement_2.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/06_requirement_1.mcf", [])
    # checker.add_safety_property("./DotModels/Iolts/car_alarm_system/06_requirement_2.mcf", [])

    return checker


def run():
    sul = get_sul()
    checker = get_model_checker(sul)
    oracle = ModelCheckerPrecisionOracle(sul, checker)
    return run_approximated_Iolts_Lstar(
        sul.iolts.get_input_alphabet(),
        sul.iolts.get_output_alphabet(),
        sul, oracle)


def print_data(data):
    for i, info in enumerate(data):
        print(f"Result: {i} {str(info)}")


def main():
    data = []
    for i in range(1, 2):
        print("'''''''''''''''''''''''''''")
        print(f"Run: {i}")
        _, _, _, info = run()

        if info:
            data.append(info)
        else:
            print("[ERROR] Info object was empty")
            data.append(None)

    print_data(data)


if __name__ == "__main__":
    main()
