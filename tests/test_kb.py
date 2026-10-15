from app.kb import KnowledgeBase


def test_title_is_taken_from_first_heading(tmp_path):
    (tmp_path / "x.md").write_text("intro line\n# The real title\nbody text\n", encoding="utf-8")
    kb = KnowledgeBase(tmp_path)
    assert kb.articles[0]["title"] == "The real title"


def test_title_falls_back_to_file_name(tmp_path):
    (tmp_path / "plain.md").write_text("no heading here\n", encoding="utf-8")
    kb = KnowledgeBase(tmp_path)
    assert kb.articles[0]["title"] == "plain.md"
