import csv
import random
import pandas

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine
from aalpy.learning_algs.approximate.ApproximatedIoltsLstar import run_approximated_Iolts_Lstar
from aalpy.learning_algs.approximate.PrecisionOracle import ModelCheckerPrecisionOracle
from aalpy.utils import load_automaton_from_file, Mcrl2ModelChecker


# SETTINGS
number_of_runs = 20
query_certainty_threshold = 0.99999
completeness_certainty_threshold = 0.99999
enforce_quiescence_reduced = False
enforce_quiescence_self_loops = False
enforce_threshold = True

# Note


def get_non_det_car_alarm() -> tuple[IoltsMachineSUL, Mcrl2ModelChecker]:
    specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/car_alarm_system/02_b_car_alarm.dot", "iolts")
    sul = IoltsMachineSUL(specification, query_certainty_threshold, completeness_certainty_threshold, enforce_threshold=enforce_threshold)

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
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/06_requirement_2.mcf", [])

    return sul, checker


def get_det_car_alarm() -> tuple[IoltsMachineSUL, Mcrl2ModelChecker]:
    specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/car_alarm_system/03_car_alarm.dot", "iolts")
    sul = IoltsMachineSUL(specification, query_certainty_threshold, completeness_certainty_threshold)

    checker = Mcrl2ModelChecker(sul)
    checker.add_liveness_property("./DotModels/Iolts/car_alarm_system/liveness_property.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_1.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_2.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_3.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/01_requirement_4.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/02_requirement_1.mcf", [])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/02_requirement_2.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/03_requirement_1.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/04_requirement_1.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/05_requirement_1.mcf", [('?close',), ('!opticalAlarm_OFF', '?close')])
    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/05_requirement_2.mcf", [])

    checker.add_safety_property("./DotModels/Iolts/car_alarm_system/06_requirement_1.mcf", [])
    # checker.add_safety_property("./DotModels/Iolts/car_alarm_system/06_requirement_2.mcf", [])

    # checker.add_safety_property("./DotModels/Iolts/car_alarm_system/07_requirement_5.mcf", [])

    return sul, checker


def get_tftp_download() -> tuple[IoltsMachineSUL, Mcrl2ModelChecker]:
    specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/tftp_download/00_download.dot", "iolts")
    sul = IoltsMachineSUL(specification, query_certainty_threshold,completeness_certainty_threshold )

    checker = Mcrl2ModelChecker(sul)
    checker.add_liveness_property("./DotModels/Iolts/tftp_download/liveness_property.mcf", [('?ACK',), ('!DATA',)])
    checker.add_safety_property("./DotModels/Iolts/tftp_download/01_requirement_2.mcf", [('?ACK',), ('!DATA',)])
    checker.add_safety_property("./DotModels/Iolts/tftp_download/01_requirement_3.mcf", [])

    return sul, checker


def get_tftp_upload() -> tuple[IoltsMachineSUL, Mcrl2ModelChecker]:
    specification: IoltsMachine = load_automaton_from_file("DotModels/Iolts/tftp_upload/00_upload.dot", "iolts")
    sul = IoltsMachineSUL(specification, query_certainty_threshold,completeness_certainty_threshold )

    checker = Mcrl2ModelChecker(sul)
    checker.add_liveness_property("./DotModels/Iolts/tftp_upload/liveness_property.mcf", [('?SEND',), ('!ACK_RESP',)])
    checker.add_safety_property("./DotModels/Iolts/tftp_upload/01_requirement_2.mcf", [('?SEND',), ('!ACK_RESP',)])
    checker.add_safety_property("./DotModels/Iolts/tftp_upload/01_requirement_3.mcf", [])

    return sul, checker

def run():
    sul, checker = get_tftp_download()

    oracle = ModelCheckerPrecisionOracle(sul, checker)

    _, cause = oracle.find_safety_cex(sul.iolts)
    if cause:
        print(cause)
        exit(1)

    _, cause = oracle.find_liveness_cex(sul.iolts)
    if cause:
        print(cause)
        exit(1)

    return run_approximated_Iolts_Lstar(
        sul.iolts.get_input_alphabet(),
        sul.iolts.get_output_alphabet(),
        sul,
        oracle,
        enforce_quiescence_reduced=enforce_quiescence_reduced,
        enforce_quiescence_self_loops=enforce_quiescence_self_loops,
        print_level=3
    )


def sava_results_as_csv(data):
    with open('results.csv', mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    df = pandas.read_csv('results.csv')
    pandas.set_option('display.max_columns', None)
    pandas.set_option('display.width', 1000)

    print("####################################################")

    print("Total steps")
    total_steps = df["steps_learning"] + df["steps_completeness"]
    print(list(total_steps))
    print(total_steps.describe())

    print("Total Listens")
    total_listens = df["listens_learning"] + df["listens_completeness"]
    print(list(total_listens))
    print(total_listens.describe())

    print("Output query interactions")
    total_interactions =  df["steps_learning"] +  df["listens_learning"]
    print(list(total_interactions))
    print(total_interactions.describe())

    print("Completeness interactions")
    total_interactions =  df["steps_completeness"] +  df["listens_completeness"]
    print(list(total_interactions))
    print(total_interactions.describe())

    print("Total interactions")
    total_interactions = total_steps + total_listens
    print(list(total_interactions))
    print(total_interactions.describe())

    print("####################################################")

    print(df)

def main():
    data = []
    for i in range(1, number_of_runs + 1):
        print(f"''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''' RUN: {i}")
        try:
            h_minus, h_plus, h_star, info = run()
            print(h_minus)
            print(h_plus)
            print(h_star)
            info["run"] = f"{i} / {number_of_runs}"
            data.append(info)
        except Exception as e:
            print(f"[ERROR] Threw exception: \n {e}")

    sava_results_as_csv(data)

if __name__ == "__main__":
    random.seed(1)
    main()
