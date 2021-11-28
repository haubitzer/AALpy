from collections import Counter
from time import sleep
from typing import Optional

from aalpy.SULs import IoltsMachineSUL
from aalpy.automata import IoltsMachine, IoltsState
from aalpy.base import SUL
from aalpy.utils import IocoChecker, Mcrl2ModelChecker
from aalpy.utils import visualize_automaton


class IocoPrecisionOracle:
    """ Use the Ioco Checker to find counter examples """

    def __init__(self, sul: IoltsMachineSUL, ioco_checker: IocoChecker = None):
        self.sul = sul
        self.ioco_checker = ioco_checker if ioco_checker else IocoChecker(sul.iolts)

    def find_cex(self, h_minus: IoltsMachine, h_plus: IoltsMachine, _observation_table=None) -> Optional[tuple]:
        h_minus.make_input_complete()
        h_plus.make_input_complete()

        is_ioco_minus, cex = self.ioco_checker.check(h_minus)
        if not is_ioco_minus:
            print("Found ioco counter example (H_minus ioco SUL): " + str(cex))
            return cex[:-1]

        is_ioco_plus, cex = self.ioco_checker.check(self.sul.iolts)
        if not is_ioco_plus:
            print("Found ioco counter example (SUL ioco H_plus): " + str(cex))
            return cex[:-1]

        return None


class UserInputPrecisionOracle:
    """
    Interactive precision oracle.
    """

    def __init__(self, sul: SUL, alphabet: list):
        self.alphabet = alphabet
        self.sul = sul
        self.curr_hypothesis = 0

    def find_cex(self, h_minus: IoltsMachine, h_plus: IoltsMachine, _observation_table=None) -> Optional[tuple]:

        self.curr_hypothesis += 1
        trace = []

        h_minus.make_input_complete()
        h_plus.make_input_complete()

        visualize_automaton(h_minus, path=f'Hypothesis_minus_{self.curr_hypothesis}')
        sleep(1)
        visualize_automaton(h_plus, path=f'Hypothesis_plus_{self.curr_hypothesis}')
        sleep(1)

        while True:
            inp = input('Please provide an input: ')
            if inp == 'help':
                print(
                    'Use one of following commands [print alphabet, print trace, return cex, stop, reset] or provide an input/output')
                continue
            if inp == 'print alphabet':
                print(self.alphabet)
                continue
            if inp == 'print trace':
                print(trace if trace else "trace is empty")
                continue
            if inp == 'return cex':
                if trace:
                    self.sul.post()
                    return trace
            if inp == 'stop':
                return None
            if inp == 'reset':
                trace.clear()
                h_minus.reset_to_initial()
                h_plus.reset_to_initial()
                self.sul.post()
                print('You are back in the initial state. Please provide an input: ')
                continue
            if inp in self.alphabet:
                trace.append(inp)
                if self.is_cex(trace, h_minus) or self.is_cex(trace, h_plus):
                    print('Counterexample found.\nIf you want to return it, type \'return cex\'.')
                else:
                    print('No counterexample found yet.')
                continue

            if inp not in self.alphabet:
                print("Provided input is not in the input alphabet. Type \'help\' for more information.")
                continue

    def is_cex(self, trace: list, hypothesis: IoltsMachine):
        for _ in range(1):
            self.sul.pre()
            breaker = False
            for letter in trace:
                out_hyp = hypothesis.step(letter)
                out_sul = self.sul.step(letter)

                print("Output H: " + str(out_hyp))
                print("Output Sul: " + str(out_sul))
                if out_hyp != out_sul:
                    breaker = True

            if breaker is False:
                return False

        return True


class ModelCheckerPrecisionOracle:
    """
    Uses the model checker to find counter examples
    """

    def __init__(self, sul: SUL, model_checker: Mcrl2ModelChecker):
        self.sul = sul
        self.model_checker = model_checker

    def find_cex(self, h_minus: IoltsMachine, h_plus: IoltsMachine, _observation_table=None) -> Optional[tuple]:
        # TODO counter example on SUL, who is responsible?
        # check if the property holds on the SUL, this should be done by running the counter example on the SUL.
        # However, to run the counter example on the SUL we need to have a step_to function again. If the counter example
        # doesn't hold on the SUL, we found a bug in the SUL or the property is wrong. This means that we need to stop learning,
        # It is not clear how to recover from that error, so we need to throw an assert.

        # TODO are safety properties also binding for h_minus?
        # Safety properties needs to hold for upper hypothesis, but are they also valid for the lower hypothesis.
        # However, we think that, it doesn't make sense to check liveness on the upper H, because the chaos state is always live.

        h_minus.remove_self_loops_from_non_quiescence_states()
        h_plus.remove_self_loops_from_non_quiescence_states()

        is_safe, cex, safety_property = self.model_checker.check_safety_properties(h_plus)
        if not is_safe:
            print("Found safety property counter example: " + str(cex))
            return cex

        is_live, cex, liveness_property = self.model_checker.check_liveness_properties(h_minus)
        if not is_live:
            print("Found liveness property counter example: " + str(cex))
            return cex

        return None


class HotSpotPrecisionOracle:
    """
    This precision oracle uses hot spot detection and the completeness query to find counter examples.
    Hot spots are sections that have the same origin and destination state but different transition letters between.
    """

    def __init__(self, sul: IoltsMachineSUL):
        self.sul = sul

    def find_cex(self, h_minus: IoltsMachine, h_plus: IoltsMachine, _observation_table=None) -> Optional[tuple]:

        h_minus.remove_self_loops_from_non_quiescence_states()

        for origin, dest in self.find_hot_spots(h_minus):
            prefix = origin.prefix

            postfixes = [letter for letter, _ in dest.get_inputs()] + [letter for letter, _ in dest.get_outputs()]

            for letter in h_minus.get_input_alphabet():
                if origin.get_inputs(letter, dest):
                    for postfix in postfixes:
                        cex = prefix + tuple([letter, postfix])
                        observed_set = set([h_minus.query(cex) for _ in range(50)])
                        if not self.sul.completeness_query(cex, observed_set):
                            print("Found hot spot counter example: " + str(cex))
                            return cex

            for letter in h_minus.get_output_alphabet():
                if origin.get_outputs(letter, dest):
                    for postfix in postfixes:
                        cex = prefix + tuple([letter, postfix])
                        observed_set = set([h_minus.query(cex) for _ in range(50)])
                        if not self.sul.completeness_query(cex, observed_set):
                            print("Found hot spot counter example: " + str(cex))
                            return cex

        return None

    def find_hot_spots(self, automata: IoltsMachine) -> list[tuple[IoltsState, IoltsState]]:
        result = []

        for state in automata.states:
            same_dest_count = Counter()
            for letter in automata.get_input_alphabet():
                same_dest_count.update(dest for letter, dest in state.get_inputs(letter, None))

            for letter in automata.get_output_alphabet():
                same_dest_count.update(dest for letter, dest in state.get_outputs(letter, None))

            for dest, count in same_dest_count.items():
                if count > 1 and dest != state:
                    result.append(tuple([state, dest]))

        return result
