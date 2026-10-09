"""
Tests the TfIDF class

Author: Quintin Dunn
Date: 10/09/2026
"""

import math
import unittest

from QuickServe.Common.tf_idf import _TfIDFTable, _TfIDFDocument, TfIDF  # noqa


class TestTfIDFTable(unittest.TestCase):
    """
    Tests the TfIDF table.
    """

    def test_add_item(self):
        """
        Tests adding an item to the TfIDF table.
        """

        table = _TfIDFTable()

        table.add_item("hello")
        table.add_item("hello")
        table.add_item("world", 2)

        self.assertEqual(
            table.frequencies,
            {
                "hello": 2,
                "world": 2,
            },
        )

    def test_tf(self):
        """
        Tests the term frequency part of TF IDF
        """

        table = _TfIDFTable()

        table.add_item("hello", 2)
        table.add_item("world")

        self.assertEqual(
            table.tf,
            {
                "hello": 2 / 3,
                "world": 1 / 3,
            },
        )


class TestTfIDFDocument(unittest.TestCase):
    """
    Tests TfIDF registered documents
    """

    def test_weights(self):
        """
        Tests that weighting of different parts affect TF IDF.
        """

        document = _TfIDFDocument(
            "test",
            "Hello",
            "World",
            "Hello",
            5,
            0.75,
        )

        self.assertEqual(
            document.frequencies,
            {
                "hello": 5.75,
                "world": 1,
            },
        )

    def test_tokenization(self):
        """
        Tests the TfIDF token correctly breaks strings into their individual words.
        """

        document = _TfIDFDocument(
            "test",
            "Hello-World",
            "Python programming",
            None,
            5,
            0.75,
        )

        self.assertEqual(
            document.frequencies,
            {
                "hello": 5,
                "world": 5,
                "python": 1,
                "programming": 1,
            },
        )


class TestTfIDF(unittest.TestCase):
    def test_add_result(self):
        """
        Tests adding documents to the TfIDF corpus.
        """

        tfidf = TfIDF()

        tfidf.add_result(
            "1",
            "Hello World",
            "Python programming",
        )

        self.assertEqual(len(tfidf.corpus), 1)
        self.assertEqual(tfidf.corpus[0].identifier, "1")
        self.assertEqual(
            tfidf._vocabulary,
            {
                "hello",
                "world",
                "python",
                "programming",
            },
        )

    def test_idf(self):
        """
        Tests that the inverse document frequency part of the TfIDF works.
        """

        tfidf = TfIDF()

        tfidf.add_result("1", "", "hello world")
        tfidf.add_result("2", "", "hello python")

        self.assertAlmostEqual(
            tfidf.idf["hello"],
            1.0,
        )
        self.assertAlmostEqual(
            tfidf.idf["world"],
            math.log(3 / 2) + 1,
        )

    def test_prefix_search(self):
        """
        Tests that full queries aren't required for a search to be fulfilled.
        """

        tfidf = TfIDF()

        tfidf.add_result(
            "1",
            "",
            "hello helicopter help world",
        )

        self.assertEqual(
            set(tfidf._expand_query("hel")),
            {
                "hello",
                "helicopter",
                "help",
            },
        )

    def test_query_returns_matching_documents(self):
        """
        Tests that the query only returns matching documents.
        """

        tfidf = TfIDF()

        tfidf.add_result(
            "1",
            "Python",
            "Python programming",
        )
        tfidf.add_result(
            "2",
            "Java",
            "Java programming",
        )

        results = tfidf.query("python")

        self.assertEqual(
            results[0][0].identifier,
            "1",
        )
        self.assertGreater(results[0][1], 0)

    def test_query_ranks_best_match_first(self):
        """
        Tests that results rank properly
        """

        tfidf = TfIDF(title_weight=1)

        tfidf.add_result(
            "1",
            "",
            "python programming language",
        )
        tfidf.add_result(
            "2",
            "",
            "python",
        )

        results = tfidf.query("python programming")

        self.assertEqual(
            results[0][0].identifier,
            "1",
        )
        self.assertGreater(
            results[0][1],
            results[1][1],
        )

    def test_minor_weight(self):
        """
        Tests that the minor weight affects the TfIDF.
        """

        tfidf = TfIDF(minor_weight=0.75)

        tfidf.add_result(
            "body",
            "",
            "python",
        )
        tfidf.add_result(
            "minor",
            "",
            "something else",
            "python",
        )

        results = tfidf.query("python")

        self.assertEqual(
            results[0][0].identifier,
            "body",
        )

    def test_unknown_query_returns_no_results(self):
        """
        Tests that a query that should return no results, returns no results.
        """

        tfidf = TfIDF()

        tfidf.add_result("1", "", "hello world")

        self.assertEqual(
            tfidf.query("python"),
            [],
        )

    def test_max_results(self):
        """
        Tests that results are limited to the max_results setting.
        """

        tfidf = TfIDF()

        for i in range(10):
            tfidf.add_result(str(i), "", "hello")

        results = tfidf.query("hello", max_results=3)

        self.assertEqual(len(results), 3)

    def test_empty_query(self):
        """
        Tests what happens with an empty query.
        """

        tfidf = TfIDF()

        tfidf.add_result("1", "", "hello world")

        self.assertEqual(
            tfidf.query(""),
            [],
        )
