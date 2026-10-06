import math
import re

_WORD_PATTERN = re.compile(r"[^\W\-_]+")


import re


class _TfIDFTable:
    def __init__(self):
        self._table: dict[str, float] = {}
        self._total_word: float = 0

    def add_item(self, term: str, weight: float = 1):
        self._table[term] = self._table.get(term, 0) + weight
        self._total_word += weight

    @property
    def frequencies(self) -> dict[str, float]:
        return self._table

    @property
    def tf(self) -> dict[str, float]:
        return {
            term: frequency / self._total_word
            for term, frequency in self._table.items()
        }


class _TfIDFDocument:
    def __init__(
        self,
        identifier: str,
        title: str,
        document: str,
        minor: str,
        title_weight: float,
        minor_weight: float,
    ):
        self.identifier = identifier
        self.title = title
        self.document = document
        self.minor = minor
        self.table = _TfIDFTable()

        for word in re.finditer(_WORD_PATTERN, title):
            self.table.add_item(word.group().lower(), title_weight)

        for word in re.finditer(_WORD_PATTERN, document):
            self.table.add_item(word.group().lower())

        for word in re.finditer(_WORD_PATTERN, minor or ""):
            self.table.add_item(word.group().lower(), minor_weight)

    @property
    def frequencies(self) -> dict[str, float]:
        return self.table.frequencies

    @property
    def tf(self) -> dict[str, float]:
        return self.table.tf

    def __repr__(self):
        return f"<TFIDF Result id={self.identifier!r}>"


class TfIDF:
    def __init__(self, title_weight: float = 5, minor_weight: float = 0.75):
        self._title_weight = title_weight
        self._minor_weight = minor_weight

        self.corpus: list[_TfIDFDocument] = []

    def add_result(self, identifier: str, title: str, text: str, minor: str = None) -> None:
        self.corpus.append(
            _TfIDFDocument(
                identifier,
                title.lower(),
                text.lower(),
                minor.lower() if minor else None,
                self._title_weight,
                self._minor_weight
            )
        )

    @property
    def idf(self) -> dict[str, float]:
        document_count = len(self.corpus)
        frequencies: dict[str, int] = {}

        for document in self.corpus:
            for term in document.frequencies:
                frequencies[term] = frequencies.get(term, 0) + 1

        return {
            term: math.log((document_count + 1) / (count + 1)) + 1
            for term, count in frequencies.items()
        }

    def query(self, query: str, max_results: int = 5) -> list[tuple[_TfIDFDocument, float]]:
        query_table = _TfIDFTable()

        for word in re.finditer(_WORD_PATTERN, query):
            query_table.add_item(word.group().lower())

        query_tf = query_table.tf
        idf = self.idf

        query_vector = {
            term: tf * idf[term]
            for term, tf in query_tf.items()
            if term in idf
        }

        results = []

        for document in self.corpus:
            document_vector = {
                term: tf * idf[term]
                for term, tf in document.tf.items()
                if term in idf
            }

            terms = set(query_vector) | set(document_vector)

            dot_product = sum(
                query_vector.get(term, 0) * document_vector.get(term, 0)
                for term in terms
            )

            query_magnitude = math.sqrt(
                sum(value ** 2 for value in query_vector.values())
            )

            document_magnitude = math.sqrt(
                sum(value ** 2 for value in document_vector.values())
            )

            if query_magnitude == 0 or document_magnitude == 0:
                similarity = 0
            else:
                similarity = dot_product / (
                        query_magnitude * document_magnitude
                )

            if similarity > 0:
                results.append((document, similarity))

        results.sort(key=lambda result: result[1], reverse=True)

        return results[:max_results]

if __name__ == '__main__':
    # DOCUMENTS generated w/ AI
    DOCUMENTS = [
        (
            "Java Programming",
            "Java is a popular programming language used for building applications and backend services."
        ),
        (
            "Python Programming",
            "Python is a popular programming language used for data science, machine learning, and web development."
        ),
        (
            "JavaScript Web Development",
            "JavaScript is a programming language commonly used for building interactive web applications."
        ),
        (
            "Backend Development",
            "Backend development often uses Java, Python, and other programming languages to build web services."
        ),
        (
            "Machine Learning",
            "Machine learning uses Python extensively for data analysis, training models, and artificial intelligence."
        ),
        (
            "Web Development",
            "Web development uses HTML, CSS, and JavaScript to create interactive websites and web applications."
        ),
    ]

    tfidf = TfIDF()
    for doc_title, doc in DOCUMENTS:
        tfidf.add_result(title=doc_title, text=doc, identifier=doc_title)

    results = tfidf.query("programming")
    print(results[0])