from aalpy.utils.HelperFunctions import extend_set, print_observation_table
from .ApproximatedIoltsObservationTable import ApproximatedIoltsObservationTable
from ...SULs import IoltsMachineSUL
from ...automata import IocoValidator, IoltsMachine


def run_approimated_Iolts_Lstar(input_alphabet: list, output_alphabet: list, sul: IoltsMachineSUL, print_level=2):
    """

    """

    # Initialize (S,E,T)
    observation_table = ApproximatedIoltsObservationTable(input_alphabet, output_alphabet, sul)

    while True:

        is_reducible = False
        while not is_reducible:
            # Update (S,E,T)
            observation_table.update_obs_table()

            # Stabilize (S,E,T)
            is_closed = False
            is_consistent = False

            while not (is_closed and is_consistent):
                is_closed, s_set_causes = observation_table.is_globally_closed()
                # TODO only add the shortest row that should improve the performancen
                extend_set(observation_table.S, s_set_causes)
                observation_table.update_obs_table()

                is_consistent, e_set_causes = observation_table.is_globally_consistent()
                extend_set(observation_table.E, e_set_causes)
                observation_table.update_obs_table()

            # Check quiescence reducible
            is_reducible, e_set_reducible = observation_table.is_quiescence_reducible()
            print("Found E by quiescence reducible: " + str(e_set_reducible))
            # extend_set(observation_table.E, e_set_reducible)

        print_observation_table(observation_table, "approximated")

        # Consturuct H- and H+
        h_minus = observation_table.gen_hypothesis_minus()
        h_plus = observation_table.gen_hypothesis_plus()

        print(h_minus)
        print(h_plus)

        print(IocoValidator(sul.iolts).automata)

        print(IocoValidator(sul.iolts).check(h_minus))

        if not IocoValidator(sul.iolts).check(h_minus):
            pass



        # Check preciseness

        return h_minus, h_plus

