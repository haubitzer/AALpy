from collections import Counter

from aalpy.SULs import IoltsMachineSUL
from aalpy.learning_algs.approximate.ApproximatedIoltsObservationTable import (
    ApproximatedIoltsObservationTable,
)

from aalpy.learning_algs.deterministic.CounterExampleProcessing import (
    longest_prefix_cex_processing,
)
from aalpy.utils.HelperFunctions import extend_set, print_learning_info, all_prefixes, all_suffixes, \
    print_observation_table


def run_approximated_Iolts_Lstar(
        input_alphabet: list,
        output_alphabet: list,
        sul: IoltsMachineSUL,
        oracle,
):
    """ """
    learning_rounds = 0
    cex_cache_longest_prefix = Counter()
    cex_cache_prefix= Counter()
    cex_cache_suffix= Counter()


    # Initialize (S,E,T)
    observation_table = ApproximatedIoltsObservationTable(
        input_alphabet, output_alphabet, sul
    )

    while True:
        learning_rounds += 1
        if not (learning_rounds < 100):
            raise Exception("Leaning round hit 100")

        is_reducible = True
        while is_reducible:

            # Update (S,E,T)
            observation_table.update_obs_table()

            # Stabilize (S,E,T)
            is_closed = False
            is_consistent = False

            while not (is_closed and is_consistent):
                is_closed, s_set_causes = observation_table.is_globally_closed()
                if not is_closed:
                    print("Closed S set: " + str(extend_set(observation_table.S, s_set_causes)))
                    observation_table.update_obs_table()
                    continue

                is_consistent, e_set_causes = observation_table.is_globally_consistent()
                if not is_consistent:
                    print("Consistent E set: " + str(extend_set(observation_table.E, e_set_causes)))
                    observation_table.update_obs_table()
                    continue

            # Check quiescence reducible
            is_reducible, e_set_reducible = observation_table.is_quiescence_reducible()
            added_e_set = extend_set(observation_table.E, e_set_reducible)
            if added_e_set:
                print(f"Found E by quiescence reducible: {added_e_set}")
            elif is_reducible and not added_e_set:
                print(f"Quiescence reducible failed! {e_set_reducible}")
                break

        # print_observation_table(observation_table, "approximated")

        # 1. Find counter example with ORIGINAL hypothesis
        h_minus = observation_table.gen_hypothesis_minus(False)
        h_plus = observation_table.gen_hypothesis_plus(False)

        all_counter_examples = oracle.find_cex(h_minus, h_plus, observation_table)

        if all_counter_examples is None:
            print("ORIGINAL hypothesis is valid")
            break
        else:
            if resolve(all_counter_examples, observation_table,  cex_cache_longest_prefix, cex_cache_prefix, cex_cache_suffix):
                continue

        print("-------------------------------------")
        # 2. Find counter example with CLEANED hypothesis
        h_minus = observation_table.gen_hypothesis_minus(True)
        h_plus = observation_table.gen_hypothesis_plus(True)
        all_counter_examples = oracle.find_cex(h_minus, h_plus, observation_table)

        if all_counter_examples is None:
            print("CLEANED hypothesis is valid")
            break
        else:
            if resolve(all_counter_examples, observation_table,  cex_cache_longest_prefix, cex_cache_prefix, cex_cache_suffix):
                continue

        print(h_minus)
        print(all_counter_examples)
        print(f"Counter Examples via longest prefix: {cex_cache_longest_prefix}")
        print(f"Counter Examples via prefix: {cex_cache_prefix}")
        print(f"Counter Examples via suffix: {cex_cache_suffix}")
        raise Exception("Error! no new counter example was found!")

    print_observation_table(observation_table, "approximated")

    info = {
        'learning_rounds': learning_rounds,
        'automaton_size': len(h_minus.states),
        'queries_learning': sul.num_queries,
        'steps_learning': sul.num_steps,
        'listens_leaning': sul.num_listens,
        'cache_saved': sul.num_cached_queries,
        'queries_eq_oracle': sul.num_completeness_queries,
        'steps_eq_oracle': sul.num_completeness_steps,
        'listens_eq_oracle': sul.num_completeness_listens,
        'learning_time': 0,
        'eq_oracle_time': 0,
        'total_time': 0,
        'characterization set': observation_table.E
    }

    print(f"Counter Examples via longest prefix: {cex_cache_longest_prefix}")
    print(f"Counter Examples via prefix: {cex_cache_prefix}")
    print(f"Counter Examples via suffix: {cex_cache_suffix}")

    print_learning_info(info)

    return h_minus, h_plus


def resolve(all_counter_examples: list, observation_table, cex_cache_longest_prefix: Counter, cex_cache_prefix, cex_cache_suffix) -> bool:
    for cex in all_counter_examples:
        if resolve_via_longest_prefix_processing(cex, observation_table, cex_cache_longest_prefix):
            return True

    for cex in all_counter_examples:
        if resolve_via_all_prefixes(cex, observation_table, cex_cache_prefix):
            return True

    for cex in all_counter_examples:
        if resolve_via_all_suffixes(cex, observation_table, cex_cache_suffix):
            return True

    return False


def resolve_via_longest_prefix_processing(cex: list, observation_table, cex_cache):
    added_elements = None
    if cex_cache.get(str(cex)) is None:
        cex_cache.update([str(cex)])
        cex_suffixes = longest_prefix_cex_processing(observation_table.S + list(observation_table.s_dot_a()), cex)
        added_elements = extend_set(observation_table.E, cex_suffixes)
        print(f'[Case 1] Added to E: {added_elements}')

    return bool(added_elements)


def resolve_via_all_prefixes(cex: list, observation_table, cex_cache):
    added_elements = None
    if cex_cache.get(str(cex)) is None:
        cex_cache.update([str(cex)])
        added_elements = extend_set(observation_table.S, all_prefixes(cex))
        print(f'[Case 2] Added to S: {added_elements}')

    return bool(added_elements)


def resolve_via_all_suffixes(cex: list, observation_table, cex_cache):
    added_elements = None
    if cex_cache.get(str(cex)) is None:
        cex_cache.update([str(cex)])
        added_elements = extend_set(observation_table.E, all_suffixes(cex))
        print(f'[Case 3] Added to E: {added_elements}')

    return bool(added_elements)

