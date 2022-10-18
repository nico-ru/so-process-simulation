from collections import OrderedDict
import random
import string
import pandas as pd
from typing import Callable, Dict, List, Optional, Union
from datetime import datetime, timedelta


class ProcessPart:
    def __init__(self):
        self.next_part = None

    def _launch_next_part(self) -> None:
        if self.next_part:
            self.next_part._execute_part(self)

    def _execute_part(self, initiator: "ProcessPart") -> None:
        self.initiator = initiator
        self.case = initiator.case


class Start(ProcessPart):
    def _execute_part(self, case: "ProcessRunner") -> None:
        self.case = case
        self._launch_next_part()


class Activity(ProcessPart):
    def __init__(
        self,
        name: Optional[str] = None,
        t: int = 0,
        attributes: Dict = {},
        execution: Optional[Callable[[Dict], None]] = None,
    ):
        """
        inintiate activity
        Parameters:
            name (str): name of the activity. If None, activity will be treated as placeholder
            t (int): avg execution time of activity in seconds.
            attributes: mapping of additional activity attributes.
        """
        super().__init__()
        self.name = name
        self.avg_time_s = t
        self.attributes = OrderedDict(attributes)
        self.execution = execution

    def _get_execution_time(self) -> timedelta:
        seconds = random.gauss(self.avg_time_s, (self.avg_time_s * 0.1))
        return timedelta(seconds=seconds)

    def _execute_part(self, initiator: ProcessPart) -> None:
        super()._execute_part(initiator)

        if self.name:
            event = [
                self.case.case_id,
                self.name,
                self.case.start.isoformat(),
                *list(self.attributes.values()),
            ]
            self.case.trace.append(event)
            self._get_noise()

        if self.execution:
            self.execution(self.case.data)

        self.case.start = self.case.start + self._get_execution_time()
        self._launch_next_part()

    def _get_noise(self):
        add_noise = self.case.noise_rate >= random.randint(1, 1000)
        if add_noise:
            noise_name = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=8)
            )
            event = [
                self.case.case_id,
                noise_name,
                self.case.start.isoformat(),
                *list(self.attributes.values()),
            ]
            self.case.trace.append(event)


class Sequence(ProcessPart):
    def __init__(self, sequence: List[ProcessPart]):
        super().__init__()
        self.sequence = []
        self._init_sequence(sequence)

    def _init_sequence(self, sequence: List[ProcessPart]) -> None:
        for i, part in enumerate(sequence):
            if len(sequence) > i + 1:
                part.next_part = sequence[i + 1]  # type:ignore
            self.sequence.append(part)

    def _execute_part(self, initiator: ProcessPart) -> None:
        super()._execute_part(initiator)
        self.sequence[0]._execute_part(self)
        self._launch_next_part()


class Decision(ProcessPart):
    def __init__(
        self,
        options: List[ProcessPart],
        probabilities: Optional[List[float]] = None,
        condition: Optional[Callable[[Dict], int]] = None,
    ):
        super().__init__()
        self.options = options
        if probabilities and sum(probabilities) != 100:
            raise Exception("Probabilities for a decision have to add up to 100%")
        if probabilities and len(probabilities) != len(options):
            raise Exception("Given Probabilities have to match the number of options")
        if not probabilities:
            probabilities = [(100 / len(options)) for i in range(len(options))]
        self.true_rates = probabilities

    def _decide(self) -> int:
        pick = random.randint(0, 100)
        start = 0
        idx = 0
        for i, rate in enumerate(self.true_rates):
            end = start + rate
            if start <= pick <= end:
                idx = i
                break
            start += rate

        return idx

    def _execute_part(self, initiator: ProcessPart) -> None:
        super()._execute_part(initiator)
        option_idx = self._decide()
        self.options[option_idx]._execute_part(self)
        self._launch_next_part()


class Process:
    def __init__(self, parts: List[ProcessPart], header: Optional[List[str]] = None):
        self.header = header if header else ["case_id", "activity", "timestamp"]
        self.parts = []
        self.start_part = Start()
        self._link_parts(parts)

    def _link_parts(self, parts):
        for i, part in enumerate(parts):
            if len(parts) > i + 1:
                part.next_part = parts[i + 1]
            self.parts.append(part)
        self.start_part.next_part = self.parts[0]

    def _execute(self, case: "ProcessRunner"):
        self.start_part._execute_part(case)


class ProcessRunner:
    def __init__(self, process: Process, noise_rate: int = 0):
        """
        initializes given process
        Parameters:
            process (Process): instance of Process to run
            noise_rate (int): rate of change name noise (parts per thousand)
        """
        self.process = process
        self.case_id = 0
        self.noise_rate = noise_rate
        self.trace = []
        self.data = dict()

    def execute(
        self,
        start_time: Optional[datetime] = None,
        case_id: Optional[Union[int, str]] = None,
    ) -> None:
        self.start = datetime.now()
        if start_time:
            self.start = start_time

        if case_id:
            self.case_id = case_id
        else:
            assert isinstance(self.case_id, int)
            self.case_id += self.case_id

        self.process._execute(self)

    def get_data_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.trace, columns=self.process.header)
