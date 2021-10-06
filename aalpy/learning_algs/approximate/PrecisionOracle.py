from typing import Optional

from aalpy.SULs import IoltsMachineSUL
from aalpy.utils import IocoChecker


class IocoPrecisionOracle:
    """ Use the Ioco Checker to find counter examples """

    def __init__(self, sul: IoltsMachineSUL, ioco_checker: IocoChecker = None):
        self.sul = sul
        self.ioco_checker = ioco_checker if ioco_checker else IocoChecker(sul.iolts)

    def find_cex(self, h_minus, h_plus, _observation_table=None) -> Optional[tuple]:
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
