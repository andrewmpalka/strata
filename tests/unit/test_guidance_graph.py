"""Mechanical checks for the public repository guidance graph."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROOT_GUIDANCE = REPOSITORY_ROOT / "AGENTS.md"

# The runtime verification image copies the test suites but intentionally does
# not copy repository documentation or Git metadata. Guidance validation is a
# source-checkout responsibility exposed by `make test-docs`. A checkout
# with a deleted AGENTS.md still reaches the failing existence assertion below.
if not ROOT_GUIDANCE.exists() and not (REPOSITORY_ROOT / ".git").exists():
    pytest.skip(
        "repository guidance is not included in the runtime verification image",
        allow_module_level=True,
    )

GUIDANCE_DOCUMENTS = (
    Path("docs/architecture/repository-layout.md"),
    Path("docs/architecture/migrations.md"),
    Path("docs/architecture/data-pipeline.md"),
    Path("docs/architecture/coverage-and-publication.md"),
    Path("docs/engineering/testing.md"),
    Path("docs/engineering/ci-isolation.md"),
    Path("docs/engineering/secrets-and-live-data.md"),
    Path("docs/engineering/provider-integration.md"),
    Path("docs/methodology/attribution-invariants.md"),
    Path("docs/methodology/temporal-boundaries.md"),
    Path("docs/methodology/study-integrity.md"),
    Path("docs/methodology/publication-language.md"),
    Path("docs/operations/demo-and-live.md"),
    Path("docs/operations/migrations-and-recovery.md"),
)

MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
DIRECT_CI_COMMAND = re.compile(
    r"(?m)^[ \t]*(?:\./)?scripts/ci\.sh[ \t]+"
    r"(?:green|clean|up|down|test(?:-integration)?|logs|verify|psql)\b"
)


def _read(relative_path: Path) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")


def _repository_markdown_links(text: str) -> list[Path]:
    targets: list[Path] = []
    for raw_target in MARKDOWN_LINK.findall(text):
        target = raw_target.split("#", 1)[0]
        if not target or "://" in target or target.startswith(("/", "#")):
            continue
        if Path(target).suffix == ".md":
            targets.append(Path(target))
    return targets


def _guidance_texts() -> dict[Path, str]:
    paths = (Path("AGENTS.md"), *GUIDANCE_DOCUMENTS)
    return {path: _read(path) for path in paths}


def test_root_guidance_exists_and_is_concise():
    assert ROOT_GUIDANCE.is_file(), "root AGENTS.md must exist"
    line_count = len(ROOT_GUIDANCE.read_text(encoding="utf-8").splitlines())
    assert line_count <= 160, f"root AGENTS.md has {line_count} lines; maximum is 160"


def test_every_root_guidance_link_resolves():
    root_text = ROOT_GUIDANCE.read_text(encoding="utf-8")
    links = _repository_markdown_links(root_text)
    assert links, "root AGENTS.md must link to focused guidance"
    missing = [str(path) for path in links if not (REPOSITORY_ROOT / path).is_file()]
    assert not missing, f"root guidance has missing Markdown targets: {missing}"


def test_navigation_targets_are_complete_and_unique():
    root_text = ROOT_GUIDANCE.read_text(encoding="utf-8")
    navigation = root_text.split("## Navigation", 1)[1].split("\n## ", 1)[0]
    targets = _repository_markdown_links(navigation)
    duplicates = sorted({str(path) for path in targets if targets.count(path) > 1})
    assert not duplicates, f"navigation destinations must be unique: {duplicates}"
    assert set(targets) == set(GUIDANCE_DOCUMENTS), (
        "navigation must contain each canonical focused document exactly once"
    )


def test_guidance_does_not_claim_to_supersede_the_prd():
    forbidden_claim = re.compile(
        r"\b(?:supersedes?|overrides?|replaces?)\b.{0,80}\b(?:canonical\s+)?PRD\b",
        re.IGNORECASE | re.DOTALL,
    )
    violations = [
        str(path)
        for path, text in _guidance_texts().items()
        if forbidden_claim.search(text)
    ]
    assert not violations, f"guidance cannot supersede the canonical PRD: {violations}"


def test_public_guidance_does_not_expose_direct_ci_commands():
    paths = (Path("README.md"), Path("AGENTS.md"), *GUIDANCE_DOCUMENTS)
    violations = [
        str(path) for path in paths if DIRECT_CI_COMMAND.search(_read(path))
    ]
    assert not violations, (
        "public verification commands must use Make targets; direct "
        f"scripts/ci.sh commands found in: {violations}"
    )


@pytest.mark.parametrize(
    ("label", "pattern"),
    (
        ("absolute developer home", r"(?:/Users/|/home/|~/)"),
        ("private repository", r"\bprivate-strata\b"),
        ("task source vocabulary", r"\bprompts?\b"),
        ("scheduling vocabulary", r"\bschedulers?\b"),
        ("contribution automation", r"\bcontribution[- ]automation\b"),
        ("hidden control", r"\bhidden[- ](?:control|orchestration)\b"),
        ("build-day vocabulary", r"\bbuild[- ]day\b"),
        (
            "model-specific workflow",
            r"\b(?:Anthropic|Claude|Codex|ChatGPT|OpenAI)\b",
        ),
    ),
)
def test_public_guidance_excludes_private_or_workflow_material(label, pattern):
    matcher = re.compile(pattern, re.IGNORECASE)
    violations = [
        str(path) for path, text in _guidance_texts().items() if matcher.search(text)
    ]
    assert not violations, f"{label} appears in public guidance: {violations}"


def test_guidance_links_have_no_direct_cycles():
    texts = _guidance_texts()
    graph = {
        source: {
            target
            for target in _repository_markdown_links(text)
            if target in texts
        }
        for source, text in texts.items()
    }
    cycles = sorted(
        f"{source} <-> {target}"
        for source, targets in graph.items()
        for target in targets
        if source != target and source in graph.get(target, set())
    )
    assert not cycles, f"guidance documents contain direct circular links: {cycles}"


CRITICAL_RULES = (
    (
        "guarded destructive cleanup",
        Path("docs/engineering/ci-isolation.md"),
        r"`scripts/ci\.sh` is the only sanctioned path for destructive cleanup",
    ),
    (
        "disposable CI identity",
        Path("docs/engineering/ci-isolation.md"),
        r"project names beginning with `strata_ci`",
    ),
    (
        "live volume prohibition",
        Path("docs/engineering/ci-isolation.md"),
        r"project `strata_live`.*?may\s+name, mount, reset, or delete its volumes",
    ),
    (
        "human-owned live environment",
        Path("docs/engineering/secrets-and-live-data.md"),
        r"`\.env\.live` is human-owned.*?Never create,\s+edit, display, read",
    ),
    (
        "applied migration immutability",
        Path("docs/architecture/migrations.md"),
        r"Never edit an applied migration",
    ),
    (
        "raw-to-staging replay",
        Path("docs/architecture/data-pipeline.md"),
        r"replay staging from retained raw artifacts under a new\s+`parser_version`",
    ),
    (
        "completed-empty coverage",
        Path("docs/architecture/coverage-and-publication.md"),
        r"`completed-empty`.*?zero events; it is valid coverage",
    ),
    (
        "publication refusal",
        Path("docs/architecture/coverage-and-publication.md"),
        r"`status=refused`.*?leaves no\s+partial published state",
    ),
    (
        "bundler attribution",
        Path("docs/methodology/attribution-invariants.md"),
        r"bundler is never the actor.*?UserOperation to its\s+`sender`",
    ),
    (
        "fee-payer and sponsor attribution",
        Path("docs/methodology/attribution-invariants.md"),
        r"Fee payers and sponsors are never actors",
    ),
    (
        "receipt and passive behavior",
        Path("docs/methodology/attribution-invariants.md"),
        r"Receipt never activates.*?passive participant.*?zero actor facts",
    ),
    (
        "index-block exposure",
        Path("docs/methodology/attribution-invariants.md"),
        r"Exposure state is assigned using code at the index block, never `latest`",
    ),
    (
        "direct 7702 matched-arm prohibition",
        Path("docs/methodology/attribution-invariants.md"),
        r"`eoa_7702_direct` is descriptive-only and never a matched arm\.",
    ),
    (
        "fixture findings prohibition",
        Path("docs/methodology/study-integrity.md"),
        r"Fixture data never produces empirical findings",
    ),
    (
        "association language",
        Path("docs/methodology/publication-language.md"),
        r"associated with retention.*?never.*?improves",
    ),
    (
        "exact-day UTC retention",
        Path("docs/methodology/temporal-boundaries.md"),
        r"Retention is exact-day UTC",
    ),
    (
        "suppression and immaturity are absence",
        Path("docs/methodology/study-integrity.md"),
        r"balance failure, sub-floor cell, or immature cell is absent.*?never zeroed",
    ),
)


@pytest.mark.parametrize(
    ("label", "relative_path", "pattern"),
    CRITICAL_RULES,
    ids=[rule[0] for rule in CRITICAL_RULES],
)
def test_critical_rule_has_canonical_statement(label, relative_path, pattern):
    text = _read(relative_path)
    assert re.search(pattern, text, re.IGNORECASE | re.DOTALL), (
        f"canonical statement missing for {label} in {relative_path}"
    )
