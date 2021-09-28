from aalpy.utils.HelperFunctions import extend_set, print_observation_table
from .ApproximatedIoltsObservationTable import ApproximatedIoltsObservationTable
from ..deterministic.CounterExampleProcessing import longest_prefix_cex_processing
from ...SULs import IoltsMachineSUL
from ...automata import IocoValidator, IoltsMachine


def run_approximated_Iolts_Lstar(input_alphabet: list, output_alphabet: list, sul: IoltsMachineSUL, max_iteration: int = 30, print_level=2):
    """

    """

    # Initialize (S,E,T)
    observation_table = ApproximatedIoltsObservationTable(input_alphabet, output_alphabet, sul)

    while True:
        if not (max_iteration > 1):
            print("Max iteration")
            break

        max_iteration = max_iteration - 1
        is_reducible = False

        while not is_reducible:

            # Update (S,E,T)
            observation_table.update_obs_table()

            # Stabilize (S,E,T)
            is_closed = False
            is_consistent = False

            while not (is_closed and is_consistent):
                is_closed, s_set_causes = observation_table.is_globally_closed()
                print("Closed S set: " + str(s_set_causes))
                # TODO only add the shortest row that should improve the performancen
                extend_set(observation_table.S, s_set_causes)
                observation_table.update_obs_table()

                is_consistent, e_set_causes = observation_table.is_globally_consistent()
                print("Consistent E set: " + str(e_set_causes))
                extend_set(observation_table.E, e_set_causes)
                observation_table.update_obs_table()

            # Check quiescence reducible
            is_reducible, e_set_reducible = observation_table.is_quiescence_reducible()
            extend_set(observation_table.E, e_set_reducible)
            print("Found E by quiescence reducible: " + str(e_set_reducible))

        print_observation_table(observation_table, "approximated")

        # Construct H- and H+
        h_minus = observation_table.gen_hypothesis_minus()
        h_plus = observation_table.gen_hypothesis_plus()

        # Use the Ioco validator to find counter examples
        is_ioco_minus, cex = IocoValidator(sul.iolts).check(h_minus)
        if not is_ioco_minus:
            print("Found ioco counter example (SUL ioco H_minus): " + str(cex))
            cex_suffixes = longest_prefix_cex_processing(observation_table.S + list(observation_table.s_dot_a()), cex)
            extend_set(observation_table.E, cex_suffixes)
            continue

        is_ioco_plus, cex = IocoValidator(h_plus).check(sul.iolts)
        if not is_ioco_plus:
            print("Found ioco counter example (H_plus ioco SUL ): " + str(cex))
            cex_suffixes = longest_prefix_cex_processing(observation_table.S + list(observation_table.s_dot_a()), cex)
            extend_set(observation_table.E, cex_suffixes)
            continue

        break

    return h_minus, h_plus
