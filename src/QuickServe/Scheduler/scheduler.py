"""
Schedules tasks for QuickServe

Author: Quintin Dunn
Date: 11/18/26
"""

import dataclasses
import heapq
import logging
import threading

from datetime import datetime, timedelta
from itertools import count
from typing import Callable, Any

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ScheduledJob:
    start_time: datetime

    func: Callable[[Any], Any]
    args: tuple
    kwargs: dict

    daemon: bool

    cancelled: bool

    parent: RecurringJob | None = None


@dataclasses.dataclass
class RecurringJob:
    # The start time for the first job, after that job base off interval
    initial_start_time: datetime
    interval: timedelta
    cancelled: bool
    daemon: bool

    func: Callable[[Any], Any]
    args: tuple
    kwargs: dict


class Scheduler:
    _jobs: list[tuple[datetime, int, ScheduledJob]]
    _recurring_jobs: list[RecurringJob]

    running: bool

    def __init__(self):
        self._jobs = list()
        self._recurring_jobs = list()
        self.running = True
        self._jobs_changed = threading.Condition()

        self._sequence = count()

    def submit_job(
        self,
        func: Callable[[Any], Any],
        args: tuple = (),
        kwargs: dict | None = None,
        start_time: datetime | timedelta | None = None,
        _parent: "RecurringJob | None" = None,
    ) -> ScheduledJob:
        """
        Submits a new job to the scheduler.
        :param start_time: The time for the job to start executing, if None datetime.now().
        :param func: The function to call for the job.
        :param args: The args for the job's function.
        :param kwargs: The kwargs for the job's function.
        :param _parent: The recurring job that spawned this job. If it's not a recurring job, None.
        :return: The scheduled job.
        """

        if isinstance(start_time, timedelta):
            delay = start_time
            start_time = datetime.now() + delay

        if start_time is None:
            start_time = datetime.now()

        job = ScheduledJob(
            start_time=start_time,
            func=func,
            args=args,
            kwargs={} if kwargs is None else kwargs,
            cancelled=False,
            daemon=False,
            parent=_parent,
        )

        logger.debug(
            "Scheduling job %s for %s.",
            job.func.__name__,
            job.start_time.isoformat(),
        )

        with self._jobs_changed:
            heapq.heappush(self._jobs, (start_time, next(self._sequence), job))
            self._jobs_changed.notify()
        logger.info(
            "Submitted job %s for %s%s.",
            getattr(func, "__qualname__", repr(func)),
            start_time.isoformat(),
            " (recurring)" if _parent is not None else "",
        )
        return job

    def _submit_job_from_recurring_job(
        self, recurring_job: RecurringJob, previous_start_time: datetime
    ) -> ScheduledJob:
        """
        Submits a new job from a recurring job.
        :param recurring_job: The recurring job.
        :return: The scheduled job.
        """

        next_start_time = previous_start_time + recurring_job.interval
        job = self.submit_job(
            start_time=next_start_time,
            func=recurring_job.func,
            args=recurring_job.args,
            kwargs=recurring_job.kwargs,
            _parent=recurring_job,
        )
        logger.debug(
            "Queued next job of %s for %s.",
            getattr(recurring_job.func, "__qualname__", repr(recurring_job.func)),
            job.start_time.isoformat(),
        )
        return job

    def submit_recurring_job(
        self,
        interval: timedelta,
        func: Callable[[Any], Any],
        args: tuple = (),
        kwargs: dict | None = None,
        initial_start_time: "datetime | None" = None,
    ) -> RecurringJob:
        """
        Register a recurring job in the recurring jobs list.
        :param interval: The interval between job starts.
        :param func: The function to call.
        :param args: The args for the function.
        :param kwargs: The kwargs for the function.
        :param initial_start_time: The initial start time for the first job, if None default: datetime.now().
        """

        if interval <= timedelta(0):
            raise ValueError("interval must be greater than zero")

        if initial_start_time is None:
            initial_start_time = datetime.now()

        recurring_job = RecurringJob(
            initial_start_time=initial_start_time,
            interval=interval,
            cancelled=False,
            func=func,
            args=args,
            kwargs={} if kwargs is None else kwargs,
            daemon=False,
        )
        self._recurring_jobs.append(recurring_job)
        logger.info(
            "Registered recurring job %s: first run at %s, interval %s.",
            getattr(func, "__qualname__", repr(func)),
            initial_start_time.isoformat(),
            interval,
        )
        self.submit_job(
            start_time=initial_start_time,
            func=func,
            args=args,
            kwargs={} if kwargs is None else kwargs,
            _parent=recurring_job,
        )
        return recurring_job

    def pop_next_job(self):
        with self._jobs_changed:
            while self._jobs:
                _, _, job = heapq.heappop(self._jobs)
                if job.cancelled:
                    logger.debug(
                        "Skipping cancelled job scheduled for %s.",
                        job.start_time.isoformat(),
                    )
                    continue
                if job.parent is not None:
                    if job.parent.cancelled:
                        logger.debug(
                            "Skipping occurrence of cancelled recurring job scheduled for %s.",
                            job.start_time.isoformat(),
                        )
                        continue
                    self._submit_job_from_recurring_job(job.parent, job.start_time)
                logger.debug(
                    "Dequeued job scheduled for %s.", job.start_time.isoformat()
                )
                return job
        return None

    @staticmethod
    def _handle_job(job: ScheduledJob):
        job.func(*job.args, **job.kwargs)

    def runner_loop(self):
        while self.running:
            job = None
            with self._jobs_changed:
                while self.running:
                    if not self._jobs:
                        self._jobs_changed.wait()
                        continue

                    wait_seconds = (
                        self._jobs[0][2].start_time - datetime.now()
                    ).total_seconds()
                    if wait_seconds > 0:
                        self._jobs_changed.wait(timeout=wait_seconds)
                        continue

                    job = self.pop_next_job()
                    break

            if not self.running:
                break

            if job is None:
                continue

            thread = threading.Thread(
                target=self._handle_job, args=(job,), daemon=job.daemon
            )
            thread.start()
