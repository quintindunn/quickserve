import logging
import math
import re

logger = logging.getLogger(__name__)

_WORD_PATTERN = re.compile(r"[^\W\-_]+")


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
        if self._total_word == 0:
            return {}

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

        logger.debug(
            f"Created document {identifier!r} with "
            f"{len(self.frequencies)} unique terms"
        )

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
        self._vocabulary: set[str] = set()

        logger.debug(
            f"Initialized TF-IDF with title weight {title_weight} "
            f"and minor weight {minor_weight}"
        )

    def add_result(
        self,
        identifier: str,
        title: str,
        text: str,
        minor: str = None,
    ) -> None:
        logger.debug(f"Adding document {identifier!r}")

        document = _TfIDFDocument(
            identifier,
            title.lower(),
            text.lower(),
            minor.lower() if minor else None,
            self._title_weight,
            self._minor_weight,
        )

        self.corpus.append(document)
        self._vocabulary.update(document.frequencies)

        logger.info(
            f"Added document {identifier!r}; "
            f"corpus now contains {len(self.corpus)} documents"
        )

    @property
    def idf(self) -> dict[str, float]:
        document_count = len(self.corpus)
        frequencies: dict[str, int] = {}

        for document in self.corpus:
            for term in document.frequencies:
                frequencies[term] = frequencies.get(term, 0) + 1

        idf = {
            term: math.log((document_count + 1) / (count + 1)) + 1
            for term, count in frequencies.items()
        }

        logger.debug(f"Calculated IDF for {len(idf)} unique terms")

        return idf

    def _expand_query(self, query: str) -> list[str]:
        terms = [
            word.group().lower()
            for word in re.finditer(_WORD_PATTERN, query)
        ]

        expanded = []

        for term in terms:
            matches = [
                vocabulary_term
                for vocabulary_term in self._vocabulary
                if vocabulary_term.startswith(term)
            ]

            if matches:
                expanded.extend(matches)
                logger.debug(
                    f"Expanded query term {term!r} to {matches!r}"
                )
            else:
                expanded.append(term)

        return expanded

    def query(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[tuple[_TfIDFDocument, float]]:
        logger.info(f"Running query {query!r}")

        query_table = _TfIDFTable()

        for term in self._expand_query(query):
            query_table.add_item(term)

        query_tf = query_table.tf
        idf = self.idf

        logger.debug(f"Query contains {len(query_tf)} unique terms")

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
                sum(value**2 for value in query_vector.values())
            )

            document_magnitude = math.sqrt(
                sum(value**2 for value in document_vector.values())
            )

            if query_magnitude == 0 or document_magnitude == 0:
                similarity = 0
            else:
                similarity = dot_product / (
                    query_magnitude * document_magnitude
                )

            logger.debug(
                f"Document {document.identifier!r} "
                f"similarity: {similarity:.4f}"
            )

            if similarity > 0:
                results.append((document, similarity))

        results.sort(
            key=lambda result: result[1],
            reverse=True,
        )

        results = results[:max_results]

        logger.info(f"Query returned {len(results)} results")

        return results