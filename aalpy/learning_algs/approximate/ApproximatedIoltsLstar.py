from aalpy.SULs import IoltsMachineSUL
from aalpy.learning_algs.approximate.ApproximatedIoltsObservationTable import (
    ApproximatedIoltsObservationTable,
)
from aalpy.learning_algs.deterministic.CounterExampleProcessing import (
    longest_prefix_cex_processing,
)
from aalpy.utils.HelperFunctions import extend_set, print_observation_table, all_suffixes


def run_approximated_Iolts_Lstar(
        input_alphabet: list,
        output_alphabet: list,
        sul: IoltsMachineSUL,
        oracle,
        max_iteration: int = 30,  # TODO remove and throw error in case of max iteration
        print_level=2,
):
    """ """
    h_minus = None
    h_plus = None

    # Initialize (S,E,T)
    observation_table = ApproximatedIoltsObservationTable(
        input_alphabet, output_alphabet, sul
    )

    while True:
        max_iteration -= 1
        if not (max_iteration > 1):
            print("Max iteration in OUTER loop")
            break

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
                extend_set(observation_table.S, s_set_causes)
                observation_table.update_obs_table()

                is_consistent, e_set_causes = observation_table.is_globally_consistent()
                print("Consistent E set: " + str(e_set_causes))
                extend_set(observation_table.E, e_set_causes)
                observation_table.update_obs_table()

                max_iteration -= 1
                if not (max_iteration > 1):
                    print("Max iteration in INNER loop")
                    return h_minus, h_plus

            # Check quiescence reducible
            is_reducible, e_set_reducible = observation_table.is_quiescence_reducible()
            extend_set(observation_table.E, e_set_reducible)
            print("Found E by quiescence reducible: " + str(e_set_reducible))

        print_observation_table(observation_table, "approximated")

        # Construct H- and H+
        h_minus = observation_table.gen_hypothesis_minus()
        h_plus = observation_table.gen_hypothesis_plus()

        # TODO merge quiescence states
        # The h_plus automata may has two state that are connected via an quiescence transition if that is the case we
        # should merge this two states together, this would improve the readability of the automata.

        # TODO check merged states aka. rows for completeness
        # As discussed, there could be the case that a state doesn't lead to the chaos state even if it should,
        # the reason for that is that state is enabled by two different traces but only one is in the observation table represented,
        # The other is not. However, the not-represented trace is never checked for completeness.
        # We should somehow check if a state is enabled by traces not in the observation table and check this traces for completeness.

        # Find counter example with precision oracle
        cex = oracle.find_cex(h_minus, h_plus, observation_table)
        if cex is not None:
            extend_set(observation_table.E, all_suffixes(cex))
            continue
        else:
            # Stop learning loop, hypotheses are good enough.
            break

    print_observation_table(observation_table, "approximated")
    return h_minus, h_plus
