"""
Tests for the QuickServe job scheduler.

Author: Quintin Dunn
Date: 11/18/2026
"""

import logging
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from QuickServe.Scheduler import scheduler as scheduler_module
from QuickServe.Scheduler.scheduler import Scheduler


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()

    def test_cancelled_job_is_skipped(self):
        """
        Tests that canceled jobs are truly skipped.
        """

        start_time = datetime(2026, 11, 18, 12, 0)
        cancelled = self.scheduler.submit_job(lambda: None, start_time=start_time)
        active = self.scheduler.submit_job(lambda: None, start_time=start_time)
        cancelled.cancelled = True

        self.assertIs(self.scheduler.pop_next_job(), active)

    def test_relative_jobs_are_ordered_by_their_delays(self):
        """
        Jobs starting at n and n+i seconds retain the expected order.
        """
        now = datetime(2026, 11, 18, 12, 0)
        delay = timedelta(seconds=5)
        additional_delay = timedelta(seconds=3)

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return now

        with patch.object(scheduler_module, "datetime", FixedDateTime):
            earlier = self.scheduler.submit_job(lambda: None, start_time=delay)
            later = self.scheduler.submit_job(
                lambda: None, start_time=delay + additional_delay
            )

        self.assertEqual(earlier.start_time, now + delay)
        self.assertEqual(later.start_time, now + delay + additional_delay)
        self.assertIs(self.scheduler.pop_next_job(), earlier)
        self.assertIs(self.scheduler.pop_next_job(), later)

    def test_runner_waits_until_a_normal_job_start_time(self):
        """
        The runner must not dispatch a job before its scheduled time.
        """

        start_time = datetime(2026, 11, 18, 12, 0, 1)
        clock = {"now": start_time - timedelta(seconds=1)}
        events = []
        scheduler = self.scheduler

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return clock["now"]

        class FakeThread:
            def __init__(self, target, args, daemon):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                events.append(("dispatch", clock["now"]))
                scheduler.running = False

        def advance_to_start_time(timeout=None):
            events.append(("wait", clock["now"]))
            self.assertGreater(timeout, 0)
            clock["now"] = start_time

        self.scheduler.submit_job(lambda: None, start_time=start_time)

        with (
            patch.object(scheduler_module, "datetime", FixedDateTime),
            patch.object(
                self.scheduler._jobs_changed,
                "wait",
                side_effect=advance_to_start_time,
            ),
            patch.object(scheduler_module.threading, "Thread", FakeThread),
        ):
            self.scheduler.runner_loop()

        self.assertEqual([event[0] for event in events], ["wait", "dispatch"])
        self.assertEqual(events[-1][1], start_time)

    def test_submit_recurring_job_registers_and_queues_first_job(self):
        """
        Tests that the initial registration of a recurring job registers the starting job.
        """

        first_start = datetime(2026, 11, 18, 12, 0)
        func = lambda value: value
        args = ("arg",)
        kwargs = {"kwarg": True}

        recurring = self.scheduler.submit_recurring_job(
            timedelta(hours=1),
            func,
            args=args,
            kwargs=kwargs,
            initial_start_time=first_start,
        )
        first_occurrence = self.scheduler.pop_next_job()

        self.assertIn(recurring, self.scheduler._recurring_jobs)
        self.assertEqual(first_occurrence.start_time, first_start)
        self.assertIs(first_occurrence.parent, recurring)
        self.assertIs(first_occurrence.func, func)
        self.assertEqual(first_occurrence.args, args)
        self.assertEqual(first_occurrence.kwargs, kwargs)

    def test_recurring_job_requires_positive_interval(self):
        """
        Tests that you cannot submit a job with a negative interval.
        """

        with self.assertRaises(ValueError):
            self.scheduler.submit_recurring_job(
                timedelta(0),
                lambda: None,
                initial_start_time=datetime(2026, 11, 18, 12, 0),
            )

    def test_recurring_interval_is_based_on_previous_scheduled_time(self):
        """A late pop must not shift the recurring job's schedule."""
        first_start = datetime(2026, 11, 18, 12, 0)
        interval = timedelta(hours=1)
        recurring = self.scheduler.submit_recurring_job(
            interval,
            lambda: None,
            initial_start_time=first_start,
        )

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                # Simulate popping the first occurrence 30 minutes late.
                return first_start + timedelta(minutes=30)

        with patch.object(scheduler_module, "datetime", FixedDateTime):
            first_occurrence = self.scheduler.pop_next_job()

        next_occurrence = self.scheduler._jobs[0][2]
        self.assertIs(first_occurrence.parent, recurring)
        self.assertEqual(next_occurrence.start_time, first_start + interval)
