import shutil
import sys
from pathlib import Path

import pytest
import yaml

TOOLS = Path(__file__).resolve().parent.parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import distill  # noqa: E402

BOOK = """# Agnostic Deism

### *Revised Edition: Twelfth Update*

## Preamble

Intro.

## Table of Contents

- stuff

## I. First Chapter

### 1. Sub

Text one.

## II. Second Chapter

Text two.
"""

ESSAY = "# Essay One\n\nCites the Eleventh Update.\n\n## Section\n\nBody.\n"


@pytest.fixture
def ws(tmp_path):
    src = tmp_path / "source"
    (src / "book").mkdir(parents=True)
    (src / "article").mkdir()
    (src / "book" / "agnostic-deism.md").write_text(BOOK, encoding="utf-8")
    (src / "article" / "one.md").write_text(ESSAY, encoding="utf-8")
    (src / "article" / "two.md").write_text(ESSAY.replace("One", "Two"), encoding="utf-8")

    root = tmp_path / "repo"
    for folder in ("vocab", "templates", "alignment"):
        shutil.copytree(REPO / folder, root / folder)
    # Start from an empty ledger: the real one holds entries for real chapters that don't exist here.
    ledger = root / "alignment" / "ledger.md"
    skeleton = ledger.read_text(encoding="utf-8").split("## Entries", 1)[0] + "## Entries\n"
    ledger.write_text(skeleton, encoding="utf-8")
    config = yaml.safe_load((REPO / "distill.config.yaml").read_text(encoding="utf-8"))
    config["source_root"] = "../source"
    config["book"]["chapters"] = [
        {"id": "P", "heading": "Preamble", "file": "00-preamble.md"},
        {"id": "I", "heading": "I. First Chapter", "file": "01-first.md"},
        {"id": "II", "heading": "II. Second Chapter", "file": "02-second.md"},
    ]
    config["essays"] = [
        {"slug": "one", "path": "article/one.md", "prefix": "ONE"},
        {"slug": "two", "path": "article/two.md", "prefix": "TWO"},
    ]
    (root / "distill.config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    return distill.Workspace(root)


def claim(cid, extra="", ctype="Interpretation"):
    return (f"#### {cid} — Title of {cid}\n- **Claim:** Something.\n- **Type:** {ctype}\n"
            f"- **Concepts:** infinite-pool\n- **Source:** § Sub\n{extra}\n")


def put_claims(path: Path, blocks: str, status="reviewed"):
    text = path.read_text(encoding="utf-8").replace("status: draft", f"status: {status}")
    text = text.replace("## 2. Claims\n", "## 2. Claims\n\n" + blocks, 1)
    path.write_text(text, encoding="utf-8")


def ledger_entry(lid, essay="ONE-001", foundation="AD-I-001", relation="contradicts", ruling="pending",
                 ruled_by="—", status="open", before="—", after="—"):
    return (f"\n### {lid} — Conflict\n\n- **Kind:** essay-vs-foundation\n- **Essay claim:** {essay}\n"
            f"- **Foundation claims:** {foundation}\n- **Relation:** {relation}\n- **Status:** {status}\n"
            f"- **Ruling:** {ruling}\n- **Ruled by:** {ruled_by}\n- **Proposed ruling:** —\n\n"
            f"**Foundation before:** {before}\n\n**Foundation after:** {after}\n")


def add_ledger(ws, *entries):
    path = ws.paths["ledger"]
    path.write_text(path.read_text(encoding="utf-8") + "".join(entries), encoding="utf-8")


def errors(ws):
    return distill.validate(ws).errors


@pytest.fixture
def scaffolded(ws):
    distill.cmd_scaffold(ws, True, None, "all")
    return ws


def test_chapter_range_stops_at_next_level2_heading(ws):
    lines = ws.book_lines()
    start, end = distill.chapter_range(lines, ws.chapter("I"))
    chapter = lines[start:end]
    assert chapter[0] == "## I. First Chapter"
    assert "### 1. Sub" in chapter
    assert not any(line.startswith("## II.") for line in chapter)
    p_start, p_end = distill.chapter_range(lines, ws.chapter("P"))
    assert "## Table of Contents" not in lines[p_start:p_end]


def test_renamed_chapter_heading_is_reported(ws):
    ws.chapters[1].heading = "I. Renamed Chapter"
    assert any("Chapter I heading not found" in e for e in errors(ws))


def test_fresh_scaffold_validates_and_is_not_overwritten(scaffolded, capsys):
    ws = scaffolded
    report = distill.validate(ws)
    assert report.errors == []
    assert any("no claims distilled yet" in w for w in report.warnings)
    front, body, _ = distill.split_front_matter(ws.essay_file(ws.essay("one")).read_text(encoding="utf-8"))
    assert "framework_version_cited" not in front
    assert 'L3: "Eleventh Update"' in body
    assert front["title"] == "Essay One"
    chapter_body = ws.foundation_file(ws.chapter("I")).read_text(encoding="utf-8")
    assert "{{" not in chapter_body and "Version references" not in chapter_body.split("-->")[-1]
    chapter_file = ws.foundation_file(ws.chapter("I"))
    chapter_file.write_text("sentinel", encoding="utf-8")
    distill.cmd_scaffold(ws, True, "I", None)
    assert chapter_file.read_text(encoding="utf-8") == "sentinel"
    assert "exists, not overwritten" in capsys.readouterr().out


def test_claim_ids_must_match_document_and_be_unique(scaffolded):
    ws = scaffolded
    put_claims(ws.foundation_file(ws.chapter("I")), claim("AD-I-001") + claim("AD-II-001"))
    put_claims(ws.foundation_file(ws.chapter("II")), claim("AD-II-001"))
    errs = errors(ws)
    assert any("must look like AD-I-NNN" in e for e in errs)
    assert any("duplicate claim ID AD-II-001" in e for e in errs)


def test_unknown_type_and_concept_are_rejected(scaffolded):
    ws = scaffolded
    put_claims(ws.foundation_file(ws.chapter("I")),
               claim("AD-I-001", ctype="Fact").replace("infinite-pool", "made-up-tag"))
    errs = errors(ws)
    assert any("unknown Type 'Fact'" in e for e in errs)
    assert any("unknown concept 'made-up-tag'" in e for e in errs)


def test_conflict_relation_requires_bidirectional_ledger_link(scaffolded):
    ws = scaffolded
    put_claims(ws.foundation_file(ws.chapter("I")), claim("AD-I-001"))
    essay = ws.essay_file(ws.essay("one"))
    put_claims(essay, claim("ONE-001", "- **Foundation:** AD-I-001 (contradicts)"))
    assert any("requires a Ledger entry" in e for e in errors(ws))

    text = essay.read_text(encoding="utf-8").replace("(contradicts)", "(contradicts)\n- **Ledger:** L-0001")
    essay.write_text(text, encoding="utf-8")
    assert any("Ledger L-0001 does not exist" in e for e in errors(ws))

    add_ledger(ws, ledger_entry("L-0001"))
    assert errors(ws) == []


def test_ruling_markers_need_applied_rulings(scaffolded):
    ws = scaffolded
    foundation = ws.foundation_file(ws.chapter("I"))
    put_claims(foundation, claim("AD-I-001", "- **Ledger:** L-0002\n- **Amended:** L-0002"))
    essay = ws.essay_file(ws.essay("one"))
    put_claims(essay, claim("ONE-001", "- **Foundation:** AD-I-001 (contradicts)\n- **Ledger:** L-0001, L-0002\n"
                                       "- **Canonical:** no (L-0001)"))
    pending_a = ledger_entry("L-0001")
    pending_b = ledger_entry("L-0002")
    add_ledger(ws, pending_a, pending_b)
    errs = errors(ws)
    assert any("Canonical marker needs L-0001 ruled A" in e for e in errs)
    assert any("Amended marker needs L-0002 ruled B" in e for e in errs)

    ledger = ws.paths["ledger"]
    text = ledger.read_text(encoding="utf-8")
    text = text.replace(pending_a, ledger_entry("L-0001", ruling="A — foundation holds", ruled_by="user",
                                                status="applied"))
    text = text.replace(pending_b, ledger_entry("L-0002", ruling="B — update foundation",
                                                ruled_by="agent (confirmed by user)", status="applied"))
    ledger.write_text(text, encoding="utf-8")
    errs = errors(ws)
    assert any("needs 'Foundation before' filled in" in e for e in errs)
    assert any("does not mention this claim" in e for e in errs)
    assert any("front matter amended is False" in e for e in errs)

    text = text.replace(ledger_entry("L-0002", ruling="B — update foundation", ruled_by="agent (confirmed by user)",
                                     status="applied"),
                        ledger_entry("L-0002", ruling="B — update foundation", ruled_by="agent (confirmed by user)",
                                     status="applied", before="AD-I-001: old.", after="AD-I-001: new."))
    ledger.write_text(text, encoding="utf-8")
    foundation.write_text(foundation.read_text(encoding="utf-8").replace("amended: false", "amended: true"),
                          encoding="utf-8")
    assert errors(ws) == []


def test_applied_ruling_a_requires_canonical_marker(scaffolded):
    ws = scaffolded
    put_claims(ws.foundation_file(ws.chapter("I")), claim("AD-I-001"))
    put_claims(ws.essay_file(ws.essay("one")),
               claim("ONE-001", "- **Foundation:** AD-I-001 (tension)\n- **Ledger:** L-0001"))
    add_ledger(ws, ledger_entry("L-0001", relation="tension", ruling="A", ruled_by="user", status="applied"))
    assert any("lacks 'Canonical: no (L-0001)'" in e for e in errors(ws))


def test_impact_lists_other_essays_linked_to_amended_claim(scaffolded, capsys):
    ws = scaffolded
    put_claims(ws.foundation_file(ws.chapter("I")), claim("AD-I-001"))
    put_claims(ws.essay_file(ws.essay("one")),
               claim("ONE-001", "- **Foundation:** AD-I-001 (contradicts)\n- **Ledger:** L-0001"))
    put_claims(ws.essay_file(ws.essay("two")), claim("TWO-001", "- **Foundation:** AD-I-001 (agrees)"))
    add_ledger(ws, ledger_entry("L-0001"))
    capsys.readouterr()
    distill.cmd_ledger(ws, pending=False, impact="L-0001")
    out = capsys.readouterr().out
    assert "TWO-001" in out
    assert "ONE-001" not in out


def test_index_regenerates_ledger_summary_idempotently(scaffolded):
    ws = scaffolded
    put_claims(ws.foundation_file(ws.chapter("I")), claim("AD-I-001"))
    put_claims(ws.essay_file(ws.essay("one")),
               claim("ONE-001", "- **Foundation:** AD-I-001 (contradicts)\n- **Ledger:** L-0001"))
    add_ledger(ws, ledger_entry("L-0001"))
    distill.cmd_index(ws)
    first = ws.paths["ledger"].read_text(encoding="utf-8")
    distill.cmd_index(ws)
    assert ws.paths["ledger"].read_text(encoding="utf-8") == first
    assert "| L-0001 | Conflict |" in first
    assert "[AD-I-001](foundation/01-first.md)" in ws.paths["index"].read_text(encoding="utf-8")
    assert errors(ws) == []


def test_next_id_skips_ids_mentioned_in_ledger(scaffolded, capsys):
    ws = scaffolded
    put_claims(ws.essay_file(ws.essay("one")), claim("ONE-001"))
    add_ledger(ws, ledger_entry("L-0004", essay="ONE-003"))
    capsys.readouterr()
    distill.cmd_next_id(ws, "one")
    distill.cmd_next_id(ws, "ledger")
    assert capsys.readouterr().out.split() == ["ONE-004", "L-0005"]


def test_paths_outside_repository_are_refused(ws):
    with pytest.raises(distill.DistillError, match="outside the repository"):
        ws.inside(ws.root.parent / "elsewhere.md")
