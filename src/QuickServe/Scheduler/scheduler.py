"""
Schedules tasks for QuickServe

Author: Quintin Dunn
Date: 11/18/26
"""

import dataclasses
import heapq
import logging
import threading
import time

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

        self._sequence = count()

    def submit_job(
        self,
        start_time: datetime | timedelta,
        func: Callable[[Any], Any],
        args: tuple = (),
        kwargs: dict | None = None,
        _parent: "RecurringJob | None" = None,
    ) -> ScheduledJob:
        """
        Submits a new job to the scheduler.
        :param start_time: The time for the job to start executing.
        :param func: The function to call for the job.
        :param args: The args for the job's function.
        :param kwargs: The kwargs for the job's function.
        :param _parent: The recurring job that spawned this job. If it's not a recurring job, None.
        :return: The scheduled job.
        """

        if isinstance(start_time, timedelta):
            delay = start_time
            start_time = datetime.now() + delay

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

        heapq.heappush(self._jobs, (start_time, next(self._sequence), job))
        logger.info(
            "Submitted job %s for %s%s.",
            getattr(func, "__qualname__", repr(func)),
            start_time.isoformat(),
            " (recurring)" if _parent is not None else "",
        )
        return job

    def _submit_job_from_recurring_job(
        self, recurring_job: RecurringJob
    ) -> ScheduledJob:
        """
        Submits a new job from a recurring job.
        :param recurring_job: The recurring job.
        :return: The scheduled job.
        """

        next_start_time = recurring_job.interval
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
        initial_start_time: datetime,
        interval: timedelta,
        func: Callable[[Any], Any],
        args: tuple = (),
        kwargs: dict | None = None,
    ) -> RecurringJob:
        """
        Register a recurring job in the recurring jobs list.
        :param initial_start_time: The initial start time for the first job.
        :param interval: The interval between job starts.
        :param func: The function to call.
        :param args: The args for the function.
        :param kwargs: The kwargs for the function.
        """

        if interval <= timedelta(0):
            raise ValueError("interval must be greater than zero")

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
                self._submit_job_from_recurring_job(job.parent)
            logger.debug("Dequeued job scheduled for %s.", job.start_time.isoformat())
            return job
        return None

    @staticmethod
    def _handle_job(job: ScheduledJob):
        job.func(*job.args, **job.kwargs)

    def runner_loop(self):
        while self.running:
            if not self._jobs or self._jobs[0][2].start_time < datetime.now():
                time.sleep(0.05)

            job = self.pop_next_job()

            if job is None:
                logger.error("Job is None!")
                continue

            thread = threading.Thread(
                target=self._handle_job, args=(job,), daemon=job.daemon
            )
            thread.start()
