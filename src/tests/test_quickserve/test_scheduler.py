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
        cancelled = self.scheduler.submit_job(start_time, lambda: None)
        active = self.scheduler.submit_job(start_time, lambda: None)
        cancelled.cancelled = True

        self.assertIs(self.scheduler.pop_next_job(), active)

    def test_submit_recurring_job_registers_and_queues_first_job(self):
        """
        Tests that the initial registration of a recurring job registers the starting job.
        """

        first_start = datetime(2026, 11, 18, 12, 0)
        func = lambda value: value
        args = ("arg",)
        kwargs = {"kwarg": True}

        recurring = self.scheduler.submit_recurring_job(
            first_start,
            timedelta(hours=1),
            func,
            args=args,
            kwargs=kwargs,
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
                datetime(2026, 11, 18, 12, 0),
                timedelta(0),
                lambda: None,
            )
