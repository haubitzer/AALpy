import random
import time
import csv
import pandas

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine
from aalpy.learning_algs.approximate.ApproximatedIoltsLstar import run_approximated_Iolts_Lstar
from aalpy.learning_algs.approximate.PrecisionOracle import ModelCheckerPrecisionOracle
from aalpy.utils import load_automaton_from_file, Mcrl2ModelChecker


def get_non_det_car_alarm() -> tuple[IoltsMachineSUL, Mcrl2ModelChecker]:
    specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/car_alarm_system/02_car_alarm.dot", "iolts")
    sul = IoltsMachineSUL(specification, 0.999, 0.999)

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

    return sul, checker


def get_det_car_alarm() -> tuple[IoltsMachineSUL, Mcrl2ModelChecker]:
    specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/car_alarm_system/02_car_alarm.dot", "iolts")
    sul = IoltsMachineSUL(specification, 0.99, 0.99)

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

    return sul, checker


def get_tftp() -> tuple[IoltsMachineSUL, Mcrl2ModelChecker]:
    specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/tftp_client/00_client.dot", "iolts")
    sul = IoltsMachineSUL(specification, 0.99, 0.99)

    checker = Mcrl2ModelChecker(sul)
    checker.add_liveness_property("./DotModels/Iolts/tftp_client/liveness_property.mcf", [('?ACK',),('!DATA',)])
    checker.add_safety_property("./DotModels/Iolts/tftp_client/01_requirement_1.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/tftp_client/01_requirement_2.mcf", [('?ACK',), ('!DATA',)])
    checker.add_safety_property("./DotModels/Iolts/tftp_client/01_requirement_3.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/tftp_client/01_requirement_4.mcf", [])

    return sul, checker


def run():
    sul, checker = get_non_det_car_alarm()
    oracle = ModelCheckerPrecisionOracle(sul, checker)
    return run_approximated_Iolts_Lstar(
        sul.iolts.get_input_alphabet(),
        sul.iolts.get_output_alphabet(),
        sul, oracle)


def sava_results_as_csv(data):
    with open('results.csv', mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    pandas.set_option('display.max_columns', None)
    pandas.set_option('display.width', 200)
    print(pandas.read_csv('results.csv'))


def main():
    data = []
    for i in range(1, 5):
        print("'''''''''''''''''''''''''''")
        print(f"Run: {i}")

        _, _, h_star, info = run()
        print(h_star)
        info["run"] = i
        data.append(info)


    sava_results_as_csv(data)


if __name__ == "__main__":
    # random.seed(1)
    main()
