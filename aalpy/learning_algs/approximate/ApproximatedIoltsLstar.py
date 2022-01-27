import random
import time
from collections import Counter


from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine
from aalpy.learning_algs.approximate.ApproximatedIoltsObservationTable import (
    ApproximatedIoltsObservationTable,
)
from aalpy.learning_algs.deterministic.CounterExampleProcessing import (
    longest_prefix_cex_processing,
)
from aalpy.utils.HelperFunctions import extend_set, all_prefixes, all_suffixes, \
    print_observation_table, print_learning_info_approximate_lstar


def run_approximated_Iolts_Lstar(
        input_alphabet: list,
        output_alphabet: list,
        sul: IoltsMachineSUL,
        oracle,
        print_level=2,
) -> tuple[IoltsMachine, IoltsMachine, IoltsMachine, object]:
    """ """
    start_time = time.time()
    learning_time = 0

    learning_rounds = 0

    cex_cache_longest_prefix = Counter()
    cex_cache_prefix = Counter()
    cex_cache_suffix = Counter()

    # Initialize (S,E,T)
    observation_table = ApproximatedIoltsObservationTable(
        input_alphabet, output_alphabet, sul
    )

    while True:
        learning_start = time.time()
        learning_rounds += 1
        print(f"Learning round: {learning_rounds}")
        if not (learning_rounds < 25):
            return None, None, None, None
            # raise Exception("Leaning round hit 100")

        is_reducible = True
        while is_reducible:
            # Update (S,E,T)
            observation_table.update_obs_table()

            # Stabilize (S,E,T)
            is_closed = False
            is_consistent = False

            stabilizing_rounds = 0
            while not (is_closed and is_consistent):
                print(".", end='')
                stabilizing_rounds += 1
                if not (stabilizing_rounds < 40):
                    # print_observation_table(observation_table, "approximated")
                    raise Exception("Dead lock")

                is_closed, s_set_causes = observation_table.is_globally_closed()
                if not is_closed:
                    added_s_set = extend_set(observation_table.S, s_set_causes)
                    if print_level > 1:
                        print("Closed S set: " + str(added_s_set))
                    observation_table.update_obs_table()
                    continue

                is_consistent, e_set_causes = observation_table.is_globally_consistent()
                if not is_consistent:
                    added_e_set = extend_set(observation_table.E, e_set_causes)
                    if print_level > 1:
                        print("Consistent E set: " + str(added_e_set))
                    observation_table.update_obs_table()
                    continue

            print(f" Stabilizing rounds: {stabilizing_rounds}")
            # Check quiescence reducible
            is_reducible, e_set_reducible = observation_table.is_quiescence_reducible()
            added_e_set = extend_set(observation_table.E, e_set_reducible)
            if added_e_set:
                if print_level > 1:
                    print(f"Found E by quiescence reducible: {added_e_set}")
            elif is_reducible and not added_e_set:
                if print_level > 1:
                    print(f"Quiescence reducible failed! {e_set_reducible}")
                break

        learning_time += time.time() - learning_start

        # Create hypothesis
        h_minus = observation_table.gen_hypothesis_minus()
        h_plus = observation_table.gen_hypothesis_plus(False)
        h_star = observation_table.gen_hypothesis_star()

        all_cex_from_minus_and_plus = oracle.find_cex(h_minus, h_plus, observation_table)
        all_cex_from_minus_and_star = oracle.find_cex(h_minus, h_star, observation_table)

        if not all_cex_from_minus_and_plus or not all_cex_from_minus_and_star:
            break

        all_counter_examples = [list(x) for x in
                                set(tuple(x) for x in all_cex_from_minus_and_plus + all_cex_from_minus_and_star)]

        if resolve(all_counter_examples, observation_table, cex_cache_longest_prefix, cex_cache_prefix, cex_cache_suffix):
            continue
        else:
            raise Exception("Error! no new counter example was found that would improve the observation table!")

    if print_level > 3:
        print_observation_table(observation_table, "approximated")

    total_time = round(time.time() - start_time, 2)
    learning_time = round(learning_time, 2)
    checking_time = round(total_time - learning_time, 2)
    info = {
        'learning_rounds': learning_rounds,
        'automaton_size_h_minus': len(h_minus.states),
        'automaton_size_h_plus': len(h_plus.states),
        'automaton_size_h_star': len(h_star.states),
        'cache_size': len(sul.cache.keys()),
        's_size': len(observation_table.S),
        'e_size': len(observation_table.E),

        'total_time': total_time,
        'learning_time': learning_time,
        'checking_time': checking_time,

        'queries_learning': sul.num_queries,
        'steps_learning': sul.num_steps,
        'listens_leaning': sul.num_listens,
        'query_certainty_probability': sul.query_certainty_probability,

        'queries_completeness': sul.num_completeness_queries,
        'steps_completeness': sul.num_completeness_steps,
        'listens_completeness': sul.num_completeness_listens,
        'completeness_certainty_probability': sul.completeness_certainty_probability,
    }

    print_learning_info_approximate_lstar(info)

    return h_minus, h_plus, h_star, info


def resolve(all_counter_examples: list, observation_table, cex_cache_longest_prefix: Counter, cex_cache_prefix,
            cex_cache_suffix) -> bool:
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
