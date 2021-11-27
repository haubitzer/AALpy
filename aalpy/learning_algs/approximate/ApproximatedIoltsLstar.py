from aalpy.SULs import IoltsMachineSUL
from aalpy.learning_algs.approximate.ApproximatedIoltsObservationTable import (
    ApproximatedIoltsObservationTable,
)
from aalpy.learning_algs.approximate.PrecisionOracle import HotSpotPrecisionOracle
from aalpy.learning_algs.deterministic.CounterExampleProcessing import (
    longest_prefix_cex_processing,
)
from aalpy.utils.HelperFunctions import extend_set, print_observation_table, all_suffixes, print_learning_info


def run_approximated_Iolts_Lstar(
        input_alphabet: list,
        output_alphabet: list,
        sul: IoltsMachineSUL,
        oracle,
        max_iteration: int = 100,  # TODO remove and throw error in case of max iteration
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

        # print_observation_table(observation_table, "approximated")

        # Construct H- and H+
        h_minus = observation_table.gen_hypothesis_minus()
        h_plus = observation_table.gen_hypothesis_plus()

        # TODO check merged states aka. rows for completeness
        # As discussed, there could be the case that a state doesn't lead to the chaos state even if it should,
        # the reason for that is that state is enabled by two different traces but only one is in the observation table represented,
        # The other is not. However, the not-represented trace is never checked for completeness.
        # We should somehow check if a state is enabled by traces not in the observation table and check this traces for completeness.

        # Idea, if a state has two transition with different letters to the same state, we should check the following trace:
        # prefix of fork state + letter + n * postfix,
        # against the SUL or the completeness query

        # It may could happen that states are falsely marked as completed, because the prefix trace was not part of the observation table

        # Find counter example with precision oracle
        cex = oracle.find_cex(h_minus, h_plus, observation_table)
        if cex is not None:
            cex_suffixes = longest_prefix_cex_processing(observation_table.S + list(observation_table.s_dot_a()), cex)
            print(cex_suffixes)
            extend_set(observation_table.E, cex_suffixes)
            continue

        cex = HotSpotPrecisionOracle(sul).find_cex(h_minus, h_plus, observation_table)
        if cex is not None:
            cex_suffixes = longest_prefix_cex_processing(observation_table.S + list(observation_table.s_dot_a()), cex)
            extend_set(observation_table.E, cex_suffixes)
            continue

        # Stop learning loop, hypotheses are good enough.
        break

    print_observation_table(observation_table, "approximated")

    info = {
        'learning_rounds': 0,
        'automaton_size': len(h_minus.states),
        'queries_learning': sul.num_queries,
        'steps_learning': sul.num_steps,
        'queries_eq_oracle': sul.num_completeness_queries,
        'steps_eq_oracle': sul.num_completeness_steps,
        'learning_time': 0,
        'eq_oracle_time': 0,
        'total_time': 0,
        'characterization set': observation_table.E
    }

    print_learning_info(info)

    return h_minus, h_plus
