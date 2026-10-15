"""Finds the knowledge-base article that best matches a ticket (plain TF-IDF search)."""
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class KnowledgeBase:
    def __init__(self, kb_dir):
        self.articles = []
        for path in sorted(Path(kb_dir).glob("*.md")):
            text = path.read_text(encoding="utf-8")
            self.articles.append({"file": path.name, "title": self._title(text, path.name), "text": text})
        self._vectorizer = None
        self._matrix = None
        if self.articles:
            self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
            self._matrix = self._vectorizer.fit_transform([a["text"] for a in self.articles])

    @staticmethod
    def _title(text, fallback):
        for line in text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return fallback

    def __len__(self):
        return len(self.articles)

    def search(self, query, top_k=3, min_score=0.05):
        """Return up to top_k articles whose similarity to the query is at least min_score."""
        if not self.articles:
            return []
        scores = linear_kernel(self._vectorizer.transform([query]), self._matrix)[0]
        ranked = sorted(zip(scores, self.articles), key=lambda pair: pair[0], reverse=True)[:top_k]
        return [
            {"file": a["file"], "title": a["title"], "score": round(float(s), 3)}
            for s, a in ranked
            if s >= min_score
        ]
