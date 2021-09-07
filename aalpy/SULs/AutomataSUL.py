from aalpy.base import SUL
from aalpy.automata import Dfa, MealyMachine, MooreMachine, Onfsm, Mdp, StochasticMealyMachine, IotsMachine, IotsState


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


class IotsMachineSUL(SUL):
    def __init__(self, iots: IotsMachine):
        super().__init__()
        self.iots = iots

    def pre(self):
        self.iots.reset_to_initial()

    def post(self):
        pass

    def step(self, letter):
        if letter == "QUIESCENCE":
            letter = "?quiescence"
        return self.iots.step(letter)

    def query(self, word: tuple) -> tuple[list, IotsState]:
        self.pre()

        middle_state = self.iots.initial_state
        out = []
        if not word:
            word = ["?empty_word"]

        for letter in word:
            if letter.startswith("?") or letter == "QUIESCENCE":
                output, middle_state = self.step(letter)
                out.append(output)
            if letter.startswith("!"):
                self.iots.current_state = middle_state
                output = self.iots.step_to(letter)
                out.append(output)

        self.post()
        self.num_queries += 1
        self.num_steps += len(word)
        return out, middle_state
