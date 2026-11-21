#!/usr/bin/env python3
"""Distillation helper for philosophy-v2.

Commands
  outline   [--chapter X | --essay SLUG]   Heading outline of the book, one chapter, or an essay (with line numbers).
  chapter   X                              Print one book chapter with line numbers (X = P, I ... XIII).
  scaffold  --foundation [--chapter X]     Create foundation chapter distillation(s) from the template.
  scaffold  --essay SLUG|all               Create essay distillation(s) from the template.
  validate  [--strict]                     Check every distillation and the ledger. Exit 1 on errors.
  index                                    Regenerate distillations/INDEX.md, foundation/README.md and the ledger summary.
  ledger    [--pending] [--impact L-NNNN]  List ledger entries, or the claims affected by an entry.
  next-id   AD-<X> | <slug> | <PREFIX> | ledger   Print the next free claim or ledger ID.

Source documents are read-only. Nothing is ever written outside this repository.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

CHAPTER_ID = r"(?:P|[IVX]+)"
CHAPTER_ID_RE = re.compile(rf"^{CHAPTER_ID}$")
FOUNDATION_CLAIM_RE = re.compile(rf"^AD-({CHAPTER_ID})-(\d{{3}})$")
ESSAY_CLAIM_RE = re.compile(r"^([A-Z]{2,6})-(\d{3})$")
CLAIM_TOKEN_RE = re.compile(rf"\b(?:AD-{CHAPTER_ID}|[A-Z]{{2,6}})-\d{{3}}\b")
LEDGER_ID_RE = re.compile(r"^L-\d{4}$")
LEDGER_TOKEN_RE = re.compile(r"\bL-\d{4}\b")
PREFIX_RE = re.compile(r"^[A-Z]{2,6}$")

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
CLAIM_HEADING_RE = re.compile(r"^####\s+(\S+)\s+[—–-]\s+(.+?)\s*$")
LEDGER_HEADING_RE = re.compile(r"^###\s+(\S+)\s+[—–-]\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^-\s+\*\*([A-Za-z ]+):\*\*\s*(.*?)\s*$")
PARAGRAPH_RE = re.compile(r"^\*\*([A-Za-z ]+):\*\*\s*(.*?)\s*$")
SECTION_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FENCE_RE = re.compile(r"^\s*(```|~~~)")
ORDINAL_UPDATE_RE = re.compile(
    r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth|Thirteenth|"
    r"Fourteenth|Fifteenth|Sixteenth|Seventeenth|Eighteenth|Nineteenth|Twentieth)\s+Update\b",
    re.I,
)

EMPTY_VALUES = {"", "—", "–", "-", "n/a", "none"}
CLAIM_FIELDS = ["Claim", "Type", "Concepts", "Source", "Quote", "Restates", "Foundation", "Ledger", "Canonical", "Amended"]
REQUIRED_CLAIM_FIELDS = ["Claim", "Type", "Concepts", "Source"]
FOUNDATION_ONLY_FIELDS = {"Restates", "Amended"}
ESSAY_ONLY_FIELDS = {"Foundation", "Canonical"}
LEDGER_REQUIRED_RELATIONS = {"tension", "contradicts", "terminology-drift"}
LEDGER_RELATIONS = LEDGER_REQUIRED_RELATIONS | {"novel"}
LEDGER_FIELDS = ["Kind", "Essay claim", "Foundation claims", "Relation", "Status", "Ruling", "Ruled by", "Proposed ruling"]
LEDGER_KINDS = {"essay-vs-foundation", "foundation-internal"}
RULED_BY_VALUES = {"user", "agent (confirmed by user)"}
STATUSES = {"draft", "reviewed", "aligned"}
SECTIONS = {
    1: "Thesis",
    2: "Claims",
    3: "Explicit denials",
    4: "Key terms",
    5: "Metaphors and imagery",
    6: "Load-bearing arguments",
    7: "Objections addressed",
    8: "Alignment summary",
    9: "Drift and open questions",
}
REQUIRED_SECTIONS = {"foundation-chapter": {1, 2, 3, 5, 6, 9}, "essay": set(SECTIONS)}
QUOTE_MAX_WORDS = 40


class DistillError(Exception):
    """A fatal problem (bad config, missing source) that stops a command."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def is_empty(value: str | None) -> bool:
    return value is None or value.strip().lower() in EMPTY_VALUES


def split_list(value: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;,]", value) if p.strip()]


def blank_comments(text: str) -> str:
    """Remove HTML comments but keep line numbering intact."""
    return COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def split_front_matter(text: str) -> tuple[dict | None, str, int]:
    """Return (front matter, body, body start line index)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text, 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            data = yaml.safe_load("\n".join(lines[1:i])) or {}
            return data, "\n".join(lines[i + 1 :]), i + 1
    return None, text, 0


# --------------------------------------------------------------------------------------------------------------------
# Workspace (config + paths)
# --------------------------------------------------------------------------------------------------------------------


@dataclass
class Chapter:
    id: str
    heading: str
    file: str


@dataclass
class Essay:
    slug: str
    path: str
    prefix: str


class Workspace:
    def __init__(self, root: Path = REPO_ROOT, source_root: str | None = None):
        self.root = root.resolve()
        cfg_path = self.root / "distill.config.yaml"
        if not cfg_path.is_file():
            raise DistillError(f"Config not found: {cfg_path}")
        self.config = yaml.safe_load(read_text(cfg_path)) or {}
        cfg = self.config
        src = source_root or os.environ.get("PHILOSOPHY_SOURCE_ROOT") or cfg.get("source_root", "../philosophy")
        src_path = Path(src)
        self.source_root = (src_path if src_path.is_absolute() else self.root / src_path).resolve()
        self.source_repo = cfg.get("source_repo", "")
        self.book_path = cfg["book"]["path"]
        self.chapters = [Chapter(str(c["id"]), str(c["heading"]), str(c["file"])) for c in cfg["book"]["chapters"]]
        self.essays = [Essay(str(e["slug"]), str(e["path"]), str(e["prefix"])) for e in cfg.get("essays", [])]
        self.paths = {k: self.inside(self.root / v) for k, v in cfg["paths"].items()}
        self._check_config()

    def inside(self, path: Path) -> Path:
        resolved = path.resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise DistillError(f"Refusing to use a path outside the repository: {path}")
        return resolved

    def _check_config(self) -> None:
        problems = []
        ids = [c.id for c in self.chapters]
        for c in self.chapters:
            if not CHAPTER_ID_RE.match(c.id):
                problems.append(f"chapter id {c.id!r} must be P or a Roman numeral")
        if len(set(ids)) != len(ids):
            problems.append("chapter ids must be unique")
        if len({c.file for c in self.chapters}) != len(self.chapters):
            problems.append("chapter files must be unique")
        prefixes = [e.prefix for e in self.essays]
        for e in self.essays:
            if not PREFIX_RE.match(e.prefix) or e.prefix == "AD" or CHAPTER_ID_RE.match(e.prefix):
                problems.append(f"essay prefix {e.prefix!r} must be 2-6 capital letters, not 'AD' or a Roman numeral")
        if len(set(prefixes)) != len(prefixes):
            problems.append("essay prefixes must be unique")
        if len({e.slug for e in self.essays}) != len(self.essays):
            problems.append("essay slugs must be unique")
        if problems:
            raise DistillError("Invalid distill.config.yaml: " + "; ".join(problems))

    # -- lookups -------------------------------------------------------------------------------------------------
    def chapter(self, chapter_id: str) -> Chapter:
        key = chapter_id.upper().removeprefix("AD-")
        for c in self.chapters:
            if c.id == key:
                return c
        raise DistillError(f"Unknown chapter {chapter_id!r}. Known: {', '.join(c.id for c in self.chapters)}")

    def essay(self, key: str) -> Essay:
        for e in self.essays:
            if key in (e.slug, e.prefix):
                return e
        raise DistillError(f"Unknown essay {key!r}. Known slugs: {', '.join(e.slug for e in self.essays)}")

    def foundation_file(self, c: Chapter) -> Path:
        return self.inside(self.paths["foundation_dir"] / c.file)

    def essay_file(self, e: Essay) -> Path:
        return self.inside(self.paths["essays_dir"] / f"{e.slug}.md")

    # -- source access (read-only) ---------------------------------------------------------------------------------
    def source_available(self) -> bool:
        return (self.source_root / self.book_path).is_file()

    def require_source(self) -> None:
        if not self.source_available():
            raise DistillError(
                f"Source documents not found at {self.source_root}.\n"
                f"Clone them with:  git clone {self.source_repo} \"{self.source_root}\"\n"
                f"or point to an existing checkout with PHILOSOPHY_SOURCE_ROOT or --source-root."
            )

    def source_lines(self, rel_path: str) -> list[str]:
        self.require_source()
        path = self.source_root / rel_path
        if not path.is_file():
            raise DistillError(f"Source file not found: {path}")
        return read_text(path).split("\n")

    def book_lines(self) -> list[str]:
        return self.source_lines(self.book_path)

    def source_commit(self) -> str:
        try:
            out = subprocess.run(
                ["git", "-C", str(self.source_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            return out.stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "unknown"


def level2_headings(lines: list[str]) -> list[tuple[int, str]]:
    out, fence = [], False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            fence = not fence
            continue
        if fence:
            continue
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) == 2:
            out.append((i, m.group(2)))
    return out


def chapter_range(lines: list[str], chapter: Chapter) -> tuple[int, int]:
    """0-based [start, end) line range of a chapter, from its level-2 heading to the next level-2 heading."""
    heads = level2_headings(lines)
    matches = [k for k, (_, text) in enumerate(heads) if text == chapter.heading]
    if not matches:
        raise DistillError(f"Chapter {chapter.id} heading not found in book: '## {chapter.heading}'")
    if len(matches) > 1:
        raise DistillError(f"Chapter {chapter.id} heading appears more than once in book: '## {chapter.heading}'")
    k = matches[0]
    end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
    return heads[k][0], end


# --------------------------------------------------------------------------------------------------------------------
# Parsing distillations and the ledger
# --------------------------------------------------------------------------------------------------------------------


@dataclass
class Claim:
    id: str
    title: str
    line: int
    section: int | None
    doc: "Doc"
    fields: dict[str, str] = field(default_factory=dict)

    def get(self, name: str) -> str | None:
        value = self.fields.get(name)
        return None if is_empty(value) else value

    def foundation_links(self) -> list[tuple[str, str]]:
        value = self.get("Foundation")
        if not value or value.strip().lower() == "none (novel)":
            return []
        links = []
        for part in split_list(value):
            m = re.match(r"^(\S+)\s*\(([a-z-]+)\)$", part)
            links.append((m.group(1), m.group(2)) if m else (part, ""))
        return links

    def ledger_ids(self) -> list[str]:
        return split_list(self.get("Ledger") or "")


@dataclass
class Doc:
    path: Path
    kind: str
    key: str
    prefix: str
    front: dict
    claims: list[Claim] = field(default_factory=list)
    sections: dict[int, str] = field(default_factory=dict)
    section_lines: dict[int, list[tuple[int, str]]] = field(default_factory=dict)

    @property
    def label(self) -> str:
        return f"AD-{self.key}" if self.kind == "foundation-chapter" else self.key


@dataclass
class LedgerEntry:
    id: str
    title: str
    line: int
    fields: dict[str, str] = field(default_factory=dict)
    paragraphs: dict[str, str] = field(default_factory=dict)
    text: str = ""

    def get(self, name: str) -> str | None:
        value = self.fields.get(name)
        return None if is_empty(value) else value

    @property
    def ruling(self) -> str:
        value = (self.fields.get("Ruling") or "pending").strip()
        return "pending" if value.lower().startswith("pending") else value[:1].upper()

    @property
    def status(self) -> str:
        return (self.fields.get("Status") or "").strip().lower()

    @property
    def proposed(self) -> str | None:
        value = self.get("Proposed ruling")
        return value[:1].upper() if value else None

    def foundation_claims(self) -> list[str]:
        return split_list(self.get("Foundation claims") or "")


class Report:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def _where(self, path: Path | None, line: int | None) -> str:
        if path is None:
            return ""
        rel = path.relative_to(self.root).as_posix() if self.root in path.parents else str(path)
        return f"{rel}:{line}: " if line else f"{rel}: "

    def error(self, msg: str, path: Path | None = None, line: int | None = None) -> None:
        self.errors.append(self._where(path, line) + msg)

    def warn(self, msg: str, path: Path | None = None, line: int | None = None) -> None:
        self.warnings.append(self._where(path, line) + msg)


def parse_doc(path: Path, kind: str, key: str, prefix: str, report: Report) -> Doc:
    text = read_text(path)
    front, body, offset = split_front_matter(text)
    doc = Doc(path, kind, key, prefix, front or {})
    if front is None:
        report.error("missing YAML front matter", path)
    lines = blank_comments(body).split("\n")
    section: int | None = None
    claim: Claim | None = None
    fence = False
    for i, line in enumerate(lines):
        lineno = offset + i + 1
        if FENCE_RE.match(line):
            fence = not fence
        if fence:
            continue
        sm = SECTION_RE.match(line)
        if sm:
            section = int(sm.group(1))
            if section in doc.sections:
                report.error(f"duplicate section '## {section}.'", path, lineno)
            doc.sections[section] = sm.group(2)
            doc.section_lines.setdefault(section, [])
            claim = None
            continue
        if line.startswith("#"):
            cm = CLAIM_HEADING_RE.match(line)
            if cm:
                claim = Claim(cm.group(1), cm.group(2), lineno, section, doc)
                doc.claims.append(claim)
            else:
                if line.startswith("#### "):
                    report.error("level-4 headings are reserved for claims ('#### ID — title')", path, lineno)
                claim = None
            continue
        if section is not None:
            doc.section_lines[section].append((lineno, line))
        fm = FIELD_RE.match(line)
        if claim is not None and fm:
            name, value = fm.group(1).strip(), fm.group(2)
            if name not in CLAIM_FIELDS:
                report.error(f"{claim.id}: unknown claim field '{name}'", path, lineno)
            elif name in claim.fields:
                report.error(f"{claim.id}: duplicate field '{name}'", path, lineno)
            else:
                claim.fields[name] = value
    return doc


def parse_ledger(path: Path, report: Report) -> list[LedgerEntry]:
    if not path.is_file():
        report.error("ledger file not found", path)
        return []
    lines = blank_comments(read_text(path)).split("\n")
    entries: list[LedgerEntry] = []
    entry: LedgerEntry | None = None
    para: str | None = None
    for i, line in enumerate(lines):
        lm = LEDGER_HEADING_RE.match(line)
        if lm:
            if not LEDGER_ID_RE.match(lm.group(1)):
                report.error(f"ledger heading ID '{lm.group(1)}' must look like L-0001", path, i + 1)
            entry = LedgerEntry(lm.group(1), lm.group(2), i + 1)
            entries.append(entry)
            para = None
            continue
        if entry is None:
            continue
        if line.startswith("## ") or line.startswith("### "):
            entry, para = None, None
            continue
        entry.text += line + "\n"
        fm = FIELD_RE.match(line)
        pm = PARAGRAPH_RE.match(line)
        if fm and para is None:
            name = fm.group(1).strip()
            if name in entry.fields:
                report.error(f"{entry.id}: duplicate field '{name}'", path, i + 1)
            entry.fields[name] = fm.group(2)
        elif pm:
            para = pm.group(1).strip()
            entry.paragraphs[para] = pm.group(2)
        elif para is not None:
            if line.strip() == "" or line.strip() == "---":
                para = None
            else:
                entry.paragraphs[para] = (entry.paragraphs[para] + " " + line.strip()).strip()
    return entries


def load_vocab_table(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return set(re.findall(r"^\|\s*`([^`]+)`\s*\|", read_text(path), re.M))


def load_concepts(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(read_text(path)) or {}
    return data.get("concepts") or {}


@dataclass
class Corpus:
    ws: Workspace
    docs: list[Doc]
    ledger: list[LedgerEntry]
    claims: dict[str, Claim]
    entries: dict[str, LedgerEntry]


def load_corpus(ws: Workspace, report: Report) -> Corpus:
    docs: list[Doc] = []
    known_files: set[Path] = set()
    for c in ws.chapters:
        path = ws.foundation_file(c)
        known_files.add(path)
        if path.is_file():
            docs.append(parse_doc(path, "foundation-chapter", c.id, f"AD-{c.id}", report))
    for e in ws.essays:
        path = ws.essay_file(e)
        known_files.add(path)
        if path.is_file():
            docs.append(parse_doc(path, "essay", e.slug, e.prefix, report))
    for folder in (ws.paths["foundation_dir"], ws.paths["essays_dir"]):
        if folder.is_dir():
            for p in sorted(folder.glob("*.md")):
                if p.resolve() not in known_files and p.name != "README.md":
                    report.warn("distillation file is not registered in distill.config.yaml; ignored", p)
    claims: dict[str, Claim] = {}
    for d in docs:
        for c in d.claims:
            if c.id in claims:
                other = claims[c.id]
                report.error(f"duplicate claim ID {c.id} (also at {other.doc.path.name}:{other.line})", d.path, c.line)
            else:
                claims[c.id] = c
    ledger = parse_ledger(ws.paths["ledger"], report)
    entries: dict[str, LedgerEntry] = {}
    for e in ledger:
        if e.id in entries:
            report.error(f"duplicate ledger ID {e.id}", ws.paths["ledger"], e.line)
        else:
            entries[e.id] = e
    return Corpus(ws, docs, ledger, claims, entries)


# --------------------------------------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------------------------------------


def validate(ws: Workspace) -> Report:
    report = Report(ws.root)
    types = load_vocab_table(ws.paths["claim_types"])
    relations = load_vocab_table(ws.paths["relations"])
    concepts = load_concepts(ws.paths["concepts"])
    if not types:
        report.error("no claim types found (expected a table of `Type` values)", ws.paths["claim_types"])
    if not relations:
        report.error("no relations found (expected a table of `relation` values)", ws.paths["relations"])
    if not concepts:
        report.error("no concepts found under 'concepts:'", ws.paths["concepts"])

    _validate_sources(ws, report)
    corpus = load_corpus(ws, report)
    for doc in corpus.docs:
        _validate_doc(ws, doc, types, concepts, report)
    _validate_links(corpus, relations, report)
    _validate_ledger(corpus, report)
    return report


def _validate_sources(ws: Workspace, report: Report) -> None:
    if not ws.source_available():
        report.warn(f"source documents not found at {ws.source_root}; source checks skipped")
        return
    lines = ws.book_lines()
    for c in ws.chapters:
        try:
            chapter_range(lines, c)
        except DistillError as exc:
            report.error(str(exc), ws.root / "distill.config.yaml")
    for e in ws.essays:
        if not (ws.source_root / e.path).is_file():
            report.error(f"essay source not found: {e.path}", ws.root / "distill.config.yaml")


def _validate_doc(ws: Workspace, doc: Doc, types: set[str], concepts: dict, report: Report) -> None:
    p, fm = doc.path, doc.front
    expected_id = doc.label
    common = ["doc_id", "title", "kind", "source_path", "source_repo", "source_commit", "distilled_on", "status"]
    required = common + (["chapter", "chapter_heading", "amended"] if doc.kind == "foundation-chapter" else [])
    for key in required:
        if key not in fm or fm[key] in (None, ""):
            report.error(f"front matter missing '{key}'", p)
    if fm.get("kind") not in (None, doc.kind):
        report.error(f"front matter kind is '{fm.get('kind')}', expected '{doc.kind}'", p)
    if fm.get("doc_id") not in (None, expected_id):
        report.error(f"front matter doc_id is '{fm.get('doc_id')}', expected '{expected_id}'", p)
    status = fm.get("status")
    if status is not None and status not in STATUSES:
        report.error(f"front matter status '{status}' must be one of {sorted(STATUSES)}", p)
    if doc.kind == "foundation-chapter":
        chapter = ws.chapter(doc.key)
        if fm.get("chapter") not in (None, chapter.id):
            report.error(f"front matter chapter is '{fm.get('chapter')}', expected '{chapter.id}'", p)
        if fm.get("chapter_heading") not in (None, chapter.heading):
            report.error("front matter chapter_heading does not match distill.config.yaml", p)
        if status == "aligned":
            report.error("status 'aligned' applies to essays only", p)
        has_amended = any(c.get("Amended") for c in doc.claims)
        if "amended" in fm and bool(fm.get("amended")) != has_amended:
            report.error(f"front matter amended is {fm.get('amended')} but claims with Amended markers: {has_amended}", p)

    for n in sorted(REQUIRED_SECTIONS[doc.kind] - set(doc.sections)):
        report.error(f"missing section '## {n}. {SECTIONS[n]}'", p)
    for n, title in doc.sections.items():
        if n in SECTIONS and title != SECTIONS[n]:
            report.warn(f"section {n} is titled '{title}', expected '{SECTIONS[n]}'", p)

    if not doc.claims:
        (report.warn if status == "draft" else report.error)("no claims distilled yet", p)

    for c in doc.claims:
        if doc.kind == "foundation-chapter":
            m = FOUNDATION_CLAIM_RE.match(c.id)
            if not m or m.group(1) != doc.key:
                report.error(f"claim ID {c.id} must look like AD-{doc.key}-NNN in this chapter", p, c.line)
            bad_fields = ESSAY_ONLY_FIELDS
        else:
            m = ESSAY_CLAIM_RE.match(c.id)
            if not m or m.group(1) != doc.prefix:
                report.error(f"claim ID {c.id} must look like {doc.prefix}-NNN in this essay", p, c.line)
            bad_fields = FOUNDATION_ONLY_FIELDS
        if c.section not in (2, 3):
            report.error(f"{c.id}: claims belong in section 2 (Claims) or 3 (Explicit denials)", p, c.line)
        for name in REQUIRED_CLAIM_FIELDS:
            if c.get(name) is None:
                report.error(f"{c.id}: missing '{name}'", p, c.line)
        for name in bad_fields & set(c.fields):
            report.error(f"{c.id}: field '{name}' is not allowed in a {doc.kind}", p, c.line)
        ctype = c.get("Type")
        if ctype and types and ctype not in types:
            report.error(f"{c.id}: unknown Type '{ctype}' (see vocab/claim-types.md)", p, c.line)
        for tag in split_list(c.get("Concepts") or ""):
            if concepts and tag not in concepts:
                report.error(f"{c.id}: unknown concept '{tag}' (see vocab/concepts.yaml)", p, c.line)
        quote = c.get("Quote")
        if quote and len(quote.split()) > QUOTE_MAX_WORDS:
            report.warn(f"{c.id}: quote longer than {QUOTE_MAX_WORDS} words", p, c.line)
        if doc.kind == "essay" and status == "aligned" and c.get("Foundation") is None:
            report.error(f"{c.id}: essay is 'aligned' but claim has no Foundation field", p, c.line)


def _validate_links(corpus: Corpus, relations: set[str], report: Report) -> None:
    claims, entries = corpus.claims, corpus.entries
    for doc in corpus.docs:
        p = doc.path
        for c in doc.claims:
            # Foundation relations (essays)
            fval = c.get("Foundation")
            if fval and fval.strip().lower() != "none (novel)":
                for target, rel in c.foundation_links():
                    if not rel:
                        report.error(f"{c.id}: Foundation item '{target}' must look like 'AD-X-NNN (relation)'", p, c.line)
                        continue
                    if relations and rel not in relations:
                        report.error(f"{c.id}: unknown relation '{rel}' (see vocab/relations.md)", p, c.line)
                    if rel == "novel":
                        report.error(f"{c.id}: use 'none (novel)' rather than linking a foundation claim as novel", p, c.line)
                    if not FOUNDATION_CLAIM_RE.match(target):
                        report.error(f"{c.id}: Foundation target '{target}' is not a foundation claim ID", p, c.line)
                    elif target not in claims:
                        report.error(f"{c.id}: Foundation target {target} does not exist", p, c.line)
            needs_ledger = any(rel in LEDGER_REQUIRED_RELATIONS for _, rel in c.foundation_links())
            ledger_ids = c.ledger_ids()
            if needs_ledger and not ledger_ids:
                report.error(f"{c.id}: tension/contradicts/terminology-drift requires a Ledger entry", p, c.line)
            for lid in ledger_ids:
                entry = entries.get(lid)
                if not LEDGER_ID_RE.match(lid) or entry is None:
                    report.error(f"{c.id}: Ledger {lid} does not exist in the ledger", p, c.line)
                elif doc.kind == "essay" and entry.get("Essay claim") != c.id:
                    report.error(f"{c.id}: ledger {lid} names essay claim '{entry.get('Essay claim')}'", p, c.line)
                elif doc.kind == "foundation-chapter" and c.id not in entry.foundation_claims():
                    report.error(f"{c.id}: ledger {lid} does not list this claim under Foundation claims", p, c.line)
            # Restates (foundation)
            for target in split_list(c.get("Restates") or ""):
                other = claims.get(target)
                if other is None or other.doc.kind != "foundation-chapter":
                    report.error(f"{c.id}: Restates {target} is not an existing foundation claim", p, c.line)
                elif other.get("Type") != c.get("Type") and not ledger_ids:
                    report.warn(
                        f"{c.id}: typed '{c.get('Type')}' but restates {target} typed '{other.get('Type')}' "
                        "(internal tension: consider a foundation-internal ledger entry)", p, c.line)
            # Ruling markers
            canonical = c.get("Canonical")
            if canonical:
                m = re.match(r"^no\s*\((L-\d{4})\)$", canonical.strip())
                if not m:
                    report.error(f"{c.id}: Canonical must be 'no (L-NNNN)'", p, c.line)
                else:
                    e = entries.get(m.group(1))
                    if not e or e.ruling != "A" or e.status != "applied" or e.get("Essay claim") != c.id:
                        report.error(f"{c.id}: Canonical marker needs {m.group(1)} ruled A, applied, for this claim",
                                     p, c.line)
            for lid in split_list(c.get("Amended") or ""):
                e = entries.get(lid)
                after = (e.paragraphs.get("Foundation after", "") if e else "")
                if not e or e.ruling != "B" or e.status != "applied":
                    report.error(f"{c.id}: Amended marker needs {lid} ruled B and applied", p, c.line)
                elif c.id not in after:
                    report.error(f"{c.id}: ledger {lid} 'Foundation after' does not mention this claim", p, c.line)
        # IDs referenced in arguments / objections must exist
        for n in (6, 7):
            for lineno, line in doc.section_lines.get(n, []):
                for token in CLAIM_TOKEN_RE.findall(line):
                    if token not in claims:
                        report.error(f"section {n} references unknown claim {token}", p, lineno)


def _validate_ledger(corpus: Corpus, report: Report) -> None:
    p = corpus.ws.paths["ledger"]
    claims = corpus.claims
    for e in corpus.ledger:
        for name in LEDGER_FIELDS:
            if name not in e.fields:
                report.error(f"{e.id}: missing field '{name}'", p, e.line)
        kind = (e.get("Kind") or "").strip()
        relation = (e.get("Relation") or "").strip()
        if kind not in LEDGER_KINDS:
            report.error(f"{e.id}: Kind must be one of {sorted(LEDGER_KINDS)}", p, e.line)
        if relation not in LEDGER_RELATIONS:
            report.error(f"{e.id}: Relation must be one of {sorted(LEDGER_RELATIONS)}", p, e.line)
        essay_id = e.get("Essay claim")
        essay_claim = claims.get(essay_id) if essay_id else None
        if kind == "essay-vs-foundation":
            if essay_claim is None or essay_claim.doc.kind != "essay":
                report.error(f"{e.id}: Essay claim '{essay_id}' is not an existing essay claim", p, e.line)
            elif e.id not in essay_claim.ledger_ids():
                report.error(f"{e.id}: essay claim {essay_id} does not reference this entry in its Ledger field",
                             p, e.line)
        elif kind == "foundation-internal" and essay_id:
            report.error(f"{e.id}: foundation-internal entries must have Essay claim '—'", p, e.line)
        fclaims = e.foundation_claims()
        if not fclaims and relation != "novel":
            report.error(f"{e.id}: Foundation claims is empty", p, e.line)
        for fid in fclaims:
            fc = claims.get(fid)
            if fc is None or fc.doc.kind != "foundation-chapter":
                report.error(f"{e.id}: Foundation claim '{fid}' is not an existing foundation claim", p, e.line)

        ruling, status = e.ruling, e.status
        if ruling not in {"pending", "A", "B", "C"}:
            report.error(f"{e.id}: Ruling must be 'pending' or start with A, B or C", p, e.line)
        if status not in {"open", "applied"}:
            report.error(f"{e.id}: Status must be 'open' or 'applied'", p, e.line)
        ruled_by = e.get("Ruled by")
        if ruling == "pending":
            if ruled_by:
                report.error(f"{e.id}: 'Ruled by' must be '—' while the ruling is pending", p, e.line)
            if status == "applied":
                report.error(f"{e.id}: cannot be applied while the ruling is pending", p, e.line)
        else:
            if ruled_by not in RULED_BY_VALUES:
                report.error(f"{e.id}: 'Ruled by' must be one of {sorted(RULED_BY_VALUES)}", p, e.line)
            if status == "open":
                report.warn(f"{e.id}: ruled {ruling} but not yet applied", p, e.line)
        if e.proposed and e.proposed not in {"A", "B", "C"}:
            report.error(f"{e.id}: Proposed ruling must be '—', A, B or C", p, e.line)
        if status != "applied":
            continue
        if ruling == "A" and kind == "essay-vs-foundation" and essay_claim is not None:
            if (essay_claim.get("Canonical") or "").replace(" ", "") != f"no({e.id})":
                report.error(f"{e.id}: applied ruling A but {essay_id} lacks 'Canonical: no ({e.id})'", p, e.line)
        if ruling == "B":
            for para in ("Foundation before", "Foundation after"):
                if is_empty(e.paragraphs.get(para)) or e.paragraphs.get(para, "").startswith("—"):
                    report.error(f"{e.id}: applied ruling B needs '{para}' filled in", p, e.line)
            if not any(e.id in split_list(c.get("Amended") or "") for c in claims.values()):
                report.error(f"{e.id}: applied ruling B but no foundation claim carries 'Amended: {e.id}'", p, e.line)
        if ruling == "C" and essay_claim is not None:
            still = [t for t, rel in essay_claim.foundation_links() if t in fclaims and rel in LEDGER_REQUIRED_RELATIONS]
            if still:
                report.error(f"{e.id}: applied ruling C but {essay_id} still relates to {', '.join(still)} with "
                             "a conflict relation", p, e.line)


# --------------------------------------------------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------------------------------------------------


def cmd_outline(ws: Workspace, chapter: str | None, essay: str | None) -> int:
    if essay:
        lines = ws.source_lines(ws.essay(essay).path)
        start, end = 0, len(lines)
    else:
        lines = ws.book_lines()
        start, end = chapter_range(lines, ws.chapter(chapter)) if chapter else (0, len(lines))
    fence = False
    for i in range(start, end):
        if FENCE_RE.match(lines[i]):
            fence = not fence
            continue
        m = None if fence else HEADING_RE.match(lines[i])
        if m and len(m.group(1)) <= 4:
            print(f"{i + 1:>6}  {'  ' * (len(m.group(1)) - 1)}{m.group(2)}")
    print(f"({end - start} lines: {start + 1}-{end})")
    return 0


def cmd_chapter(ws: Workspace, chapter: str) -> int:
    lines = ws.book_lines()
    start, end = chapter_range(lines, ws.chapter(chapter))
    for i in range(start, end):
        print(f"{i + 1:>6}: {lines[i]}")
    return 0


def _template_body(ws: Workspace) -> str:
    _, body, _ = split_front_matter(read_text(ws.paths["template"]))
    return body.lstrip("\n")


def _fill(body: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        body = body.replace("{{" + k + "}}", v)
    return body


def _render(front: dict, body: str) -> str:
    return "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=1000) + "---\n\n" + body


def _version_refs(lines: list[str]) -> str:
    """List references to a specific edition of the foundation book, which essays should not make."""
    refs = [f"- L{i + 1}: \"{m.group(0)}\"" for i, line in enumerate(lines) for m in ORDINAL_UPDATE_RE.finditer(line)]
    if not refs:
        return ""
    return "Version references to remove when reconstituting (essays must not cite a foundation edition):\n\n" + \
        "\n".join(refs) + "\n"


def cmd_scaffold(ws: Workspace, foundation: bool, chapter: str | None, essay: str | None) -> int:
    ws.require_source()
    body = _template_body(ws)
    commit = ws.source_commit()
    today = dt.date.today().isoformat()
    created = 0
    if foundation:
        book = ws.book_lines()
        for c in [ws.chapter(chapter)] if chapter else ws.chapters:
            chapter_range(book, c)  # fail early if heading missing
            path = ws.foundation_file(c)
            if path.exists():
                print(f"exists, not overwritten: {path.relative_to(ws.root).as_posix()}")
                continue
            front = {
                "doc_id": f"AD-{c.id}", "title": c.heading, "kind": "foundation-chapter",
                "source_path": ws.book_path, "source_repo": ws.source_repo, "source_commit": commit,
                "distilled_on": today, "status": "draft",
                "chapter": c.id, "chapter_heading": c.heading, "amended": False,
            }
            values = {"title": c.heading, "doc_id": f"AD-{c.id}", "id_pattern": f"AD-{c.id}-NNN",
                      "example_id": f"AD-{c.id}-001", "version_refs": ""}
            write_text(path, _render(front, _fill(body, values)))
            print(f"created: {path.relative_to(ws.root).as_posix()}")
            created += 1
    if essay:
        targets = ws.essays if essay == "all" else [ws.essay(essay)]
        for e in targets:
            path = ws.essay_file(e)
            if path.exists():
                print(f"exists, not overwritten: {path.relative_to(ws.root).as_posix()}")
                continue
            lines = ws.source_lines(e.path)
            title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), e.slug)
            front = {
                "doc_id": e.slug, "title": title, "kind": "essay", "source_path": e.path,
                "source_repo": ws.source_repo, "source_commit": commit, "distilled_on": today, "status": "draft",
            }
            values = {"title": title, "doc_id": e.slug, "id_pattern": f"{e.prefix}-NNN", "example_id": f"{e.prefix}-001",
                      "version_refs": _version_refs(lines)}
            write_text(path, _render(front, _fill(body, values)))
            print(f"created: {path.relative_to(ws.root).as_posix()}")
            created += 1
    print(f"{created} file(s) created.")
    return 0


def cmd_validate(ws: Workspace, strict: bool) -> int:
    report = validate(ws)
    for w in report.warnings:
        print(f"WARNING {w}")
    for e in report.errors:
        print(f"ERROR   {e}")
    failed = bool(report.errors) or (strict and bool(report.warnings))
    print(f"\n{len(report.errors)} error(s), {len(report.warnings)} warning(s). {'FAILED' if failed else 'OK'}")
    return 1 if failed else 0


def _claim_counts(doc: Doc) -> tuple[int, int, int]:
    amended = sum(1 for c in doc.claims if c.get("Amended"))
    noncanon = sum(1 for c in doc.claims if c.get("Canonical"))
    return len(doc.claims), amended, noncanon


def cmd_index(ws: Workspace) -> int:
    report = Report(ws.root)
    corpus = load_corpus(ws, report)
    concepts = load_concepts(ws.paths["concepts"])
    docs_by_key = {(d.kind, d.key): d for d in corpus.docs}
    fdir, edir = ws.paths["foundation_dir"], ws.paths["essays_dir"]
    index_dir = ws.paths["index"].parent

    # foundation/README.md
    rows = ["# Distilled foundation", "",
            "One distillation per chapter of *Agnostic Deism*. Generated by `python tools/distill.py index`; "
            "do not edit by hand.", "",
            "| Chapter | File | Status | Claims | Amended |", "|---------|------|--------|--------|---------|"]
    for c in ws.chapters:
        d = docs_by_key.get(("foundation-chapter", c.id))
        if d:
            n, amended, _ = _claim_counts(d)
            rows.append(f"| {c.heading} | [{c.file}]({c.file}) | {d.front.get('status', '?')} | {n} | {amended} |")
        else:
            rows.append(f"| {c.heading} | {c.file} | not started | 0 | 0 |")
    write_text(fdir / "README.md", "\n".join(rows) + "\n")

    # INDEX.md
    def link(claim: Claim) -> str:
        rel = os.path.relpath(claim.doc.path, index_dir).replace(os.sep, "/")
        marks = []
        if claim.get("Amended"):
            marks.append(f"amended {claim.get('Amended')}")
        if claim.get("Canonical"):
            marks.append(f"non-canonical {claim.get('Canonical').removeprefix('no').strip(' ()')}")
        suffix = f" — *{'; '.join(marks)}*" if marks else ""
        return f"- [{claim.id}]({rel}) {claim.title} · {claim.get('Type') or '?'}{suffix}"

    out = ["# Distillation index", "",
           "Generated by `python tools/distill.py index`; do not edit by hand.", "",
           "## Essays", "",
           "| Essay | Status | Claims | Ledgered | Non-canonical |", "|-------|--------|--------|----------|---------------|"]
    for e in ws.essays:
        d = docs_by_key.get(("essay", e.slug))
        if d:
            n, _, noncanon = _claim_counts(d)
            ledgered = sum(1 for c in d.claims if c.ledger_ids())
            rel = os.path.relpath(d.path, index_dir).replace(os.sep, "/")
            out.append(f"| [{e.slug}]({rel}) | {d.front.get('status', '?')} | {n} | {ledgered} | {noncanon} |")
        else:
            out.append(f"| {e.slug} | not started | 0 | 0 | 0 |")
    out += ["", "Foundation progress: [foundation/README.md](" +
            os.path.relpath(fdir / "README.md", index_dir).replace(os.sep, "/") + ")", "", "## Claims by concept", ""]
    by_concept: dict[str, list[Claim]] = {}
    for claim in corpus.claims.values():
        for tag in split_list(claim.get("Concepts") or ""):
            by_concept.setdefault(tag, []).append(claim)
    if not by_concept:
        out.append("_No claims distilled yet._")
    order = {"foundation-chapter": 0, "essay": 1}
    for tag in sorted(by_concept):
        label = (concepts.get(tag) or {}).get("label", "unknown concept")
        out += [f"### {tag}", "", f"*{label}*", ""]
        for claim in sorted(by_concept[tag], key=lambda c: (order[c.doc.kind], c.doc.path.name, c.id)):
            out.append(link(claim))
        out.append("")
    write_text(ws.paths["index"], "\n".join(out).rstrip() + "\n")

    # ledger summary
    ledger_path = ws.paths["ledger"]
    if ledger_path.is_file():
        text = read_text(ledger_path)
        start, end = "<!-- ledger-summary:start", "<!-- ledger-summary:end -->"
        if start in text and end in text:
            head, rest = text.split(start, 1)
            marker_line, _, _ = rest.partition("\n")
            _, tail = rest.split(end, 1)
            if corpus.ledger:
                table = ["| ID | Title | Kind | Essay claim | Foundation claims | Relation | Ruling | Status |",
                         "|----|-------|------|-------------|-------------------|----------|--------|--------|"]
                for e in corpus.ledger:
                    ruling = e.ruling + (f" (proposed {e.proposed})" if e.ruling == "pending" and e.proposed else "")
                    table.append(f"| {e.id} | {e.title} | {e.get('Kind') or '—'} | {e.get('Essay claim') or '—'} | "
                                 f"{e.get('Foundation claims') or '—'} | {e.get('Relation') or '—'} | {ruling} | "
                                 f"{e.status or '—'} |")
                summary = "\n".join(table)
            else:
                summary = "_No entries yet._"
            write_text(ledger_path, f"{head}{start}{marker_line}\n{summary}\n{end}{tail}")
        else:
            report.warn("ledger summary markers not found; summary not regenerated", ledger_path)

    for w in report.warnings + report.errors:
        print(w)
    print("Regenerated: " + ", ".join(p.relative_to(ws.root).as_posix()
                                      for p in (fdir / "README.md", ws.paths["index"], ledger_path)))
    return 0


def cmd_ledger(ws: Workspace, pending: bool, impact: str | None) -> int:
    report = Report(ws.root)
    corpus = load_corpus(ws, report)
    if impact:
        entry = corpus.entries.get(impact)
        if entry is None:
            raise DistillError(f"Ledger entry {impact} not found")
        targets = set(entry.foundation_claims())
        targets |= {c.id for c in corpus.claims.values() if impact in split_list(c.get("Amended") or "")}
        own = entry.get("Essay claim")
        print(f"Impact of {impact} — foundation claims: {', '.join(sorted(targets)) or 'none'}\n")
        print("Essay claims linked to these foundation claims:")
        hits = 0
        for c in sorted(corpus.claims.values(), key=lambda c: c.id):
            if c.doc.kind != "essay" or c.id == own:
                continue
            links = [f"{t} ({r})" for t, r in c.foundation_links() if t in targets]
            if links:
                hits += 1
                print(f"  {c.id:<10} {', '.join(links):<30} {c.doc.path.name} — {c.title}")
        print("  (none)" if not hits else "")
        print("Foundation claims restating them:")
        restating = [c for c in corpus.claims.values() if set(split_list(c.get("Restates") or "")) & targets]
        for c in sorted(restating, key=lambda c: c.id):
            print(f"  {c.id:<10} {c.doc.path.name} — {c.title}")
        print("  (none)" if not restating else "")
        print("Load-bearing arguments using them:")
        args = 0
        for d in corpus.docs:
            for lineno, line in d.section_lines.get(6, []):
                if set(CLAIM_TOKEN_RE.findall(line)) & targets:
                    args += 1
                    print(f"  {d.path.name}:{lineno}  {line.strip()}")
        print("  (none)" if not args else "")
        return 0
    shown = 0
    for e in corpus.ledger:
        if pending and e.ruling != "pending" and e.status == "applied":
            continue
        shown += 1
        proposed = f" (proposed {e.proposed})" if e.proposed and e.ruling == "pending" else ""
        print(f"{e.id} [{e.status or '?'}] ruling={e.ruling}{proposed} {e.get('Relation') or '?'}: "
              f"{e.get('Essay claim') or '—'} ↔ {e.get('Foundation claims') or '—'} — {e.title}")
    print(f"{shown} entr{'y' if shown == 1 else 'ies'}{' needing a ruling or application' if pending else ''}.")
    return 0


def cmd_next_id(ws: Workspace, target: str) -> int:
    ledger_text = read_text(ws.paths["ledger"]) if ws.paths["ledger"].is_file() else ""
    if target.lower() == "ledger":
        nums = [int(t[2:]) for t in LEDGER_TOKEN_RE.findall(blank_comments(ledger_text))]
        print(f"L-{max(nums, default=0) + 1:04d}")
        return 0
    if target.upper().startswith("AD-") or CHAPTER_ID_RE.match(target.upper()):
        c = ws.chapter(target)
        prefix, path = f"AD-{c.id}", ws.foundation_file(c)
    else:
        e = ws.essay(target)
        prefix, path = e.prefix, ws.essay_file(e)
    text = blank_comments(read_text(path)) if path.is_file() else ""
    pattern = re.compile(rf"\b{re.escape(prefix)}-(\d{{3}})\b")
    nums = [int(n) for n in pattern.findall(text + "\n" + ledger_text)]
    print(f"{prefix}-{max(nums, default=0) + 1:03d}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="distill.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-root", help="path to a checkout of the source philosophy repository")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("outline", help="heading outline with line numbers")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--chapter")
    g.add_argument("--essay")
    p = sub.add_parser("chapter", help="print one book chapter with line numbers")
    p.add_argument("chapter")
    p = sub.add_parser("scaffold", help="create distillation files from the template")
    p.add_argument("--foundation", action="store_true")
    p.add_argument("--chapter")
    p.add_argument("--essay", help="essay slug or prefix, or 'all'")
    p = sub.add_parser("validate", help="validate distillations and ledger")
    p.add_argument("--strict", action="store_true", help="treat warnings as errors")
    sub.add_parser("index", help="regenerate INDEX.md, foundation/README.md and ledger summary")
    p = sub.add_parser("ledger", help="list ledger entries")
    p.add_argument("--pending", action="store_true")
    p.add_argument("--impact", metavar="L-NNNN")
    p = sub.add_parser("next-id", help="print next free claim or ledger ID")
    p.add_argument("target", help="AD-<chapter>, <chapter>, essay slug or prefix, or 'ledger'")
    return parser


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        ws = Workspace(root, args.source_root)
        if args.command == "outline":
            return cmd_outline(ws, args.chapter, args.essay)
        if args.command == "chapter":
            return cmd_chapter(ws, args.chapter)
        if args.command == "scaffold":
            if not args.foundation and not args.essay:
                raise DistillError("scaffold needs --foundation and/or --essay")
            if args.chapter and not args.foundation:
                raise DistillError("--chapter is only valid with --foundation")
            return cmd_scaffold(ws, args.foundation, args.chapter, args.essay)
        if args.command == "validate":
            return cmd_validate(ws, args.strict)
        if args.command == "index":
            return cmd_index(ws)
        if args.command == "ledger":
            return cmd_ledger(ws, args.pending, args.impact)
        if args.command == "next-id":
            return cmd_next_id(ws, args.target)
    except DistillError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
