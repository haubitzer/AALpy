from aalpy.base import SUL
from aalpy.automata import Dfa, MealyMachine, MooreMachine, Onfsm, Mdp, StochasticMealyMachine, IoltsMachine, IoltsState, MarkovChain


class DfaSUL(SUL):
    """
    System under learning for DFAs.
    """

    def __init__(self, dfa: Dfa):
        super().__init__()
        self.dfa = dfa

    def pre(self):
        """
        Resets the dfa to the initial state.
        """
        self.dfa.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        """
        If the letter is empty/None check is preform to see if the empty string is accepted by the DFA.

        Args:

            letter: single input or None representing the empty string

        Returns:

            output of the dfa.step method (whether the next state is accepted or not)

        """
        if letter is None:
            return self.dfa.initial_state.is_accepting
        return self.dfa.step(letter)


class MdpSUL(SUL):
    def __init__(self, mdp: Mdp):
        super().__init__()
        self.mdp = mdp

    def query(self, word: tuple) -> list:
        initial_output = self.pre()
        out = [initial_output]
        for letter in word:
            out.append(self.step(letter))
        self.post()
        return out

    def pre(self):
        self.mdp.reset_to_initial()
        return self.mdp.current_state.output

    def post(self):
        pass

    def step(self, letter):
        return self.mdp.step(letter)


class McSUL(SUL):
    def __init__(self, mdp: MarkovChain):
        super().__init__()
        self.mc = mdp

    def query(self, word: tuple) -> list:
        initial_output = self.pre()
        out = [initial_output]
        for letter in word:
            out.append(self.step(letter))
        self.post()
        return out

    def pre(self):
        self.mc.reset_to_initial()
        return self.mc.current_state.output

    def post(self):
        pass

    def step(self, letter=None):
        return self.mc.step()


class MealySUL(SUL):
    """
    System under learning for Mealy machines.
    """

    def __init__(self, mm: MealyMachine):
        super().__init__()
        self.mm = mm

    def pre(self):
        """ """
        self.mm.reset_to_initial()

    def post(self):
        """ """
        pass

    def step(self, letter):
        """
        Args:

            letter: single non-Null input

        Returns:

            output of the mealy.step method (output based on the input and the current state)

        """
        return self.mm.step(letter)


class MooreSUL(SUL):
    """
    System under learning for Mealy machines.
    """

    def __init__(self, moore_machine: MooreMachine):
        super().__init__()
        self.mm = moore_machine

    def pre(self):
        """ """
        self.mm.reset_to_initial()

    def post(self):
        """ """
        pass

    def step(self, letter):
        if letter is None:
            return self.mm.initial_state.output
        return self.mm.step(letter)


class OnfsmSUL(SUL):
    def __init__(self, mdp: Onfsm):
        super().__init__()
        self.onfsm = mdp

    def pre(self):
        self.onfsm.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        return self.onfsm.step(letter)


class StochasticMealySUL(SUL):
    def __init__(self, smm: StochasticMealyMachine):
        super().__init__()
        self.smm = smm

    def pre(self):
        self.smm.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        return self.smm.step(letter)


class IoltsMachineSUL(SUL):
    def __init__(self, iolts: IoltsMachine):
        super().__init__()
        self.iolts = iolts

    def pre(self):
        self.iolts.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        if letter == "QUIESCENCE":
            letter = "?quiescence"
        return self.iolts.step(letter)

    def query(self, word: tuple) -> tuple[list, list]:
        self.pre()

        middle_state = self.iolts.current_state
        outputs = []
        possible_outputs = []
        enable_diff_state = []

        if not word:
            possible_outputs.append([])
            outputs.append(None)
            enable_diff_state.append(self.iolts.current_state.is_input_enabled_for_diff_state())

        for letter in word:
            if letter.startswith("?"):
                output, middle_state = self.step(letter)
                possible_outputs.append([key for key, _ in middle_state.get_outputs()])
                enable_diff_state.append(middle_state.is_input_enabled_for_diff_state())
                outputs.append(output)
            if letter.startswith("!"):
                self.iolts.current_state = middle_state
                self.iolts.step_to(letter)
                possible_outputs.append([key for key, _ in self.iolts.current_state.get_outputs()])
                enable_diff_state.append(self.iolts.current_state.is_input_enabled_for_diff_state())
                outputs.append(None)
            if letter == 'QUIESCENCE':
                possible_outputs.append([key for key, _ in self.iolts.current_state.get_outputs()])
                enable_diff_state.append(self.iolts.current_state.is_input_enabled_for_diff_state())
                outputs.append(None)


        self.post()
        self.num_queries += 1
        self.num_steps += len(word)
        return outputs, possible_outputs, enable_diff_state
