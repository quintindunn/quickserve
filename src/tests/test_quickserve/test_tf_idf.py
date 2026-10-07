import math
import unittest

from QuickServe.Common.tf_idf import _TfIDFTable, _TfIDFDocument, TfIDF


class TestTfIDFTable(unittest.TestCase):
    def test_add_item(self):
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
    def test_weights(self):
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
        tfidf = TfIDF()

        tfidf.add_result("1", "", "hello world")

        self.assertEqual(
            tfidf.query("python"),
            [],
        )

    def test_max_results(self):
        tfidf = TfIDF()

        for i in range(10):
            tfidf.add_result(str(i), "", "hello")

        results = tfidf.query("hello", max_results=3)

        self.assertEqual(len(results), 3)

    def test_empty_query(self):
        tfidf = TfIDF()

        tfidf.add_result("1", "", "hello world")

        self.assertEqual(
            tfidf.query(""),
            [],
        )
