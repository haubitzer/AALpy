import time
from collections import Counter

from sortedcontainers import SortedSet

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine
from aalpy.learning_algs.approximate.ApproximatedIoltsObservationTable import (
    ApproximatedIoltsObservationTable,
)
from aalpy.learning_algs.approximate.PrecisionOracle import ModelCheckerPrecisionOracle
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
        enforce_quiescence_reduced: bool = True,
        enforce_quiescence_self_loops: bool = True,
        enable_reset: bool = True,
        print_level=2,
) -> tuple[IoltsMachine, IoltsMachine, IoltsMachine, object]:
    """ """
    start_time = time.time()
    learning_time = 0
    learning_rounds = 0
    number_of_resets = 0

    h_minus, h_plus, h_star = None, None, None

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
        print("-------------------------------------------------------------------------------------------------------")
        print(f"Learning round: {learning_rounds}")
        if not (learning_rounds < 400):
            raise Exception("Leaning rounds hit 400")

        if h_star:
            pass
            # observation_table.trim(h_star)

        is_reducible = True
        while is_reducible:
            # Update (S,E,T)
            observation_table.update_obs_table()

            # Stabilize (S,E,T)
            is_closed = False
            is_consistent = False

            stabilizing_rounds = 0
            while not (is_closed and is_consistent):
                stabilizing_rounds += 1

                # observation_table.remove_redundant_rows()

                if not (stabilizing_rounds < 200):
                    print("Stabilizing rounds hit 200")
                    break


                is_closed, rows_to_close = observation_table.is_globally_closed()
                if not is_closed:
                    added_s_set = extend_set(observation_table.S, rows_to_close)
                    if print_level > 1:
                        print("Closed S set: " + str(added_s_set))
                    observation_table.update_obs_table()
                    continue

                is_consistent, e_for_consistency, cause = observation_table.is_globally_consistent()
                if not is_consistent:
                    added_e_set = extend_set(observation_table.E, e_for_consistency)

                    if not added_e_set:
                        if enable_reset:
                            print(f"[INFO] Could not resolve inconsistent observation table!")
                            print("+++++ RESET ++++")
                            number_of_resets += 1
                            observation_table.clear()
                            cex_cache_suffix.clear()
                            cex_cache_prefix.clear()
                            cex_cache_longest_prefix.clear()
                            observation_table.update_obs_table()
                            continue
                        else:
                            raise Exception(f"[ERROR] Could not resolve inconsistent observation table! May increase certainty_probability. \n {cause}")

                    if print_level > 1:
                        print(f"Consistent E set: {added_e_set}")

                    observation_table.update_obs_table()
                    continue

            print(f" Stabilizing rounds: {stabilizing_rounds}")
            # Check quiescence reducible
            is_reducible, e_set_reducible, cause = observation_table.is_quiescence_reducible()

            if is_reducible:
                print(f" Found quiescence reducible cause: {e_set_reducible} \n {cause}")

            if not enforce_quiescence_reduced:
                break
            else:
                added_e_set = extend_set(observation_table.E, e_set_reducible)
                if added_e_set:
                    if print_level > 1:
                        print(f"Found E by quiescence reducible: {added_e_set} \n {cause}")
                elif is_reducible and not added_e_set:
                    print(f"Quiescence reducible failed! {e_set_reducible} \n {cause}")
                    break
                    # raise Exception(f"Quiescence reducible failed! {e_set_reducible} \n {cause}")


        learning_time += time.time() - learning_start

        # Create hypothesis
        h_minus = observation_table.gen_hypothesis_minus()
        h_plus = observation_table.gen_hypothesis_plus(False, enforce_quiescence_self_loops)
        h_star = observation_table.gen_hypothesis_star(enforce_quiescence_self_loops)

        h_minus_cex = []
        h_plus_cex = []
        h_star_cex = []

        oracle: ModelCheckerPrecisionOracle

        h_minus_cex, cause = oracle.find_liveness_cex(h_minus)
        if h_minus_cex and print_level > 1:
            print(cause)

        try:
            h_star_cex_liveness, cause = oracle.find_liveness_cex(h_star)
            if h_star_cex_liveness and print_level > 1:
                print(cause)
            h_star_cex_safety, cause = oracle.find_safety_cex(h_star)
            if h_star_cex_safety and print_level > 1:
                print(cause)

            h_star_cex = h_star_cex_liveness + h_star_cex_safety
        except Exception as e:
            print(f"[ERROR] H* failed: \n {e}")

            h_plus_cex, cause = oracle.find_safety_cex(h_plus)
            if h_plus_cex and print_level > 1:
                print(cause)

        all_counter_examples = sorted(
            [list(unique_cex) for unique_cex in SortedSet(tuple(cex) for cex in h_minus_cex + h_plus_cex + h_star_cex)])

        if not all_counter_examples:
            break

        if not resolve(all_counter_examples,
                       observation_table,
                       cex_cache_longest_prefix,
                       cex_cache_prefix,
                       cex_cache_suffix):
            print(h_star)
            if enable_reset:
                print("[INFO] No new counter example was found that would improve the observation table!")
                print("+++++ RESET ++++")
                number_of_resets += 1
                observation_table.clear()
                cex_cache_suffix.clear()
                cex_cache_prefix.clear()
                cex_cache_longest_prefix.clear()
                continue
            else:
                raise Exception("Error! no new counter example was found that would improve the observation table!")

    if print_level > 3:
        print_observation_table(observation_table, "approximated")

    total_time = round(time.time() - start_time, 2)
    learning_time = round(learning_time, 2)
    checking_time = round(total_time - learning_time, 2)

    if not enforce_quiescence_self_loops:
        h_star_with_self_loops = observation_table.gen_hypothesis_star(True)
        _, cause = oracle.find_safety_cex(h_star_with_self_loops)
        if cause is None:
            h_star = h_star_with_self_loops
        else:
            print(f"Found violation in self-loop Hstar: {cause}")

    info = {
        'learning_rounds': learning_rounds,
        'number_of_resets': number_of_resets,
        'automaton_size_h_minus': len(h_minus.states),
        'automaton_size_h_plus': len(h_plus.states),
        'automaton_size_h_star': len(h_star.states),
        'cache_size': len(sul.cache.keys()),
        's_size': len(observation_table.S),
        'e_size': len(observation_table.E),
        'quiescence_reduced': not is_reducible,

        'total_time': total_time,
        'learning_time': learning_time,
        'checking_time': checking_time,

        'queries_learning': sul.num_queries,
        'steps_learning': sul.num_steps,
        'listens_learning': sul.num_listens,
        'query_certainty_probability': sul.query_certainty_threshold,

        'queries_completeness': sul.num_completeness_queries,
        'steps_completeness': sul.num_completeness_steps,
        'listens_completeness': sul.num_completeness_listens,
        'completeness_certainty_probability': sul.completeness_certainty_threshold,
        'debug': cause
    }

    print_learning_info_approximate_lstar(info)

    return h_minus, h_plus, h_star, info


def resolve(all_counter_examples: list, observation_table, cex_cache_longest_prefix: Counter, cex_cache_prefix,
            cex_cache_suffix) -> bool:

    for cex in all_counter_examples:
        if resolve_via_longest_prefix_processing(cex, observation_table, cex_cache_longest_prefix):
            return True

    for cex in all_counter_examples:
        if resolve_via_all_suffixes(cex, observation_table, cex_cache_suffix):
            return True

    for cex in all_counter_examples:
        if resolve_via_all_prefixes(cex, observation_table, cex_cache_prefix):
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

def resolve_via_all_suffixes(cex: list, observation_table, cex_cache):
    added_elements = None
    if cex_cache.get(str(cex)) is None:
        cex_cache.update([str(cex)])
        added_elements = extend_set(observation_table.E, all_suffixes(cex))
        print(f'[Case 2] Added to E: {added_elements}')

    return bool(added_elements)


def resolve_via_all_prefixes(cex: list, observation_table, cex_cache):
    added_elements = None
    if cex_cache.get(str(cex)) is None:
        cex_cache.update([str(cex)])
        added_elements = extend_set(observation_table.S, all_prefixes(cex))
        print(f'[Case 3] Added to S: {added_elements}')

    return bool(added_elements)
