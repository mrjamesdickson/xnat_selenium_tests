"""Pipeline scheduling utilities inspired by the legacy test suite."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Sequence, Set


@dataclass(frozen=True)
class DummyMethodInstance:
    name: str
    estimated_runtime: int | None = None
    unit_test_ids: Set[int] | None = None

    def __post_init__(self) -> None:
        if self.unit_test_ids is None:
            object.__setattr__(self, "unit_test_ids", frozenset())
        else:
            object.__setattr__(self, "unit_test_ids", frozenset(self.unit_test_ids))


class UnitTestFilter:
    """Helper that mimics the legacy ``UnitTestFilter`` utilities."""

    _METHODS: Dict[str, DummyMethodInstance] = {
        "testLaunch100": DummyMethodInstance("testLaunch100", 100, {1, 2}),
        "testLaunch55": DummyMethodInstance("testLaunch55", 55, {1, 2}),
        "testLaunch50": DummyMethodInstance("testLaunch50", 50, {1, 2}),
        "testLaunch40": DummyMethodInstance("testLaunch40", 40, {1, 2}),
        "testLaunch30": DummyMethodInstance("testLaunch30", 30, {1, 2}),
        "testLaunch20": DummyMethodInstance("testLaunch20", 20, {1, 2}),
        "testLaunch5": DummyMethodInstance("testLaunch5", 5, {1, 2}),
        "testCheck100": DummyMethodInstance("testCheck100", unit_test_ids={1, 2}),
        "testCheck55": DummyMethodInstance("testCheck55", unit_test_ids={1, 2}),
        "testCheck50": DummyMethodInstance("testCheck50", unit_test_ids={1, 2}),
        "testCheck40": DummyMethodInstance("testCheck40", unit_test_ids={1, 2}),
        "testCheck30": DummyMethodInstance("testCheck30", unit_test_ids={1, 2}),
        "testCheck20": DummyMethodInstance("testCheck20", unit_test_ids={1, 2}),
        "testCheck5": DummyMethodInstance("testCheck5", unit_test_ids={1}),
    }

    _ORDER = [
        "testLaunch100",
        "testLaunch55",
        "testLaunch50",
        "testLaunch30",
        "testLaunch40",
        "testLaunch20",
        "testLaunch5",
        "testCheck100",
        "testCheck55",
        "testCheck50",
        "testCheck40",
        "testCheck30",
        "testCheck20",
        "testCheck5",
    ]

    @classmethod
    def get_instance(cls, name: str) -> DummyMethodInstance:
        return cls._METHODS[name]

    @classmethod
    def get_dummy_tests(cls, test_id: int) -> List[DummyMethodInstance]:
        return [
            cls._METHODS[name]
            for name in cls._ORDER
            if test_id in cls._METHODS[name].unit_test_ids
        ]


class PipelineMethodSorter:
    """Schedules launch and check methods to mirror the Groovy tests."""

    def order_by_job_shop_solution(
        self, methods: Sequence[DummyMethodInstance], queue_slots: int
    ) -> List[DummyMethodInstance]:
        launch_methods = [
            method
            for method in methods
            if method.name.startswith("testLaunch")
        ]
        if not launch_methods:
            return list(methods)

        assignments = self._solve_schedule(launch_methods, queue_slots)
        ordered = list(launch_methods)
        used = set(ordered)

        completion = sorted(
            assignments,
            key=lambda item: (item.start + item.duration, item.queue_index),
        )

        for item in completion:
            suffix = item.method.name[len("testLaunch") :]
            check_name = f"testCheck{suffix}"
            check_method = next(
                (method for method in methods if method.name == check_name), None
            )
            if check_method is None:
                raise RuntimeError(
                    f"Could not find corresponding pipeline check test for launch test {item.method.name}."
                )
            if check_method not in used:
                ordered.append(check_method)
                used.add(check_method)

        for method in methods:
            if method not in used:
                ordered.append(method)
                used.add(method)

        return ordered

    def _solve_schedule(
        self, methods: Sequence[DummyMethodInstance], queue_slots: int
    ) -> Sequence["ScheduledJob"]:
        best_assignment: Sequence[ScheduledJob] | None = None
        best_makespan: int | None = None

        for assignment in product(range(queue_slots), repeat=len(methods)):
            queue_loads = [0] * queue_slots
            schedule: List[ScheduledJob] = []
            valid = True
            for method, queue_index in zip(methods, assignment):
                if method.estimated_runtime is None:
                    valid = False
                    break
                start = queue_loads[queue_index]
                duration = method.estimated_runtime
                queue_loads[queue_index] += duration
                schedule.append(
                    ScheduledJob(
                        method=method,
                        queue_index=queue_index,
                        start=start,
                        duration=duration,
                    )
                )
            if not valid:
                continue
            makespan = max(queue_loads)
            if best_makespan is None or makespan < best_makespan or (
                makespan == best_makespan and assignment < tuple(job.queue_index for job in best_assignment)
            ):
                best_assignment = schedule
                best_makespan = makespan

        if best_assignment is None:
            return []
        return best_assignment


@dataclass(frozen=True)
class ScheduledJob:
    method: DummyMethodInstance
    queue_index: int
    start: int
    duration: int

