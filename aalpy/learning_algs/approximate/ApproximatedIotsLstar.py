from aalpy.base import SUL

from .ApproximatedIotsObservationTable import ApproximatedIotsObservationTable
from ...SULs import IotsMachineSUL
from ...utils.HelperFunctions import print_observation_table

from aalpy.utils.HelperFunctions import extend_set, print_learning_info, print_observation_table, all_prefixes


def run_approimated_Iots_Lstar(alphabet: list, sul: IotsMachineSUL, print_level=2):
    """

    """

    # 1. initialize table
    hypothesis = None
    observation_table = ApproximatedIotsObservationTable(alphabet, sul)

    while True:

        observation_table.update_obs_table()

        is_closed = False
        is_consistent = False

        while not is_closed or not is_consistent:
            is_closed, s_set_causes = observation_table.is_globally_closed()
            extend_set(observation_table.S, s_set_causes)
            observation_table.update_obs_table()

            is_consistent, e_set_causes = observation_table.is_globally_consistent()
            extend_set(observation_table.E, e_set_causes)
            observation_table.update_obs_table()

            print_observation_table(observation_table, "det")




        break

    return None


