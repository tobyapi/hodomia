#!/usr/bin/env python3
"""Detect a project's stack, layout, and verification commands.

Answers the questions an agent must know before editing code it has never seen:
which languages and frameworks are in play, where source and tests live, what
command proves a change, and which directories look like architectural layers.

Writes the result to .clean/context.json so a later session, or an agent with
no memory of this one, can read the answers instead of re-deriving them.

Standard library only. Reads files; writes nothing unless --write is given.

Usage:
    python detect_stack.py                # human-readable summary
    python detect_stack.py --json         # machine-readable, for tools
    python detect_stack.py --write        # also save .clean/context.json
    python detect_stack.py --root ../app  # inspect a different directory
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCHEMA_VERSION = 1

# Directories that hold dependencies, build output, or tool caches. Walking them
# is slow and tells us nothing about the project's own design.
SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", ".idea", ".vscode", ".vs",
    "node_modules", "bower_components", "jspm_packages", "vendor",
    "__pycache__", ".venv", "venv", "env", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".gradle", ".dart_tool", ".terraform",
    "bin", "obj", "build", "dist", "out", "target", "_build", "deps",
    "coverage", "htmlcov", ".next", ".nuxt", ".svelte-kit", ".parcel-cache",
    "Pods", "Carthage", ".cargo", ".stack-work", "cmake-build-debug",
})

# Extension -> language. Deliberately broad: the skill must work in any language,
# so an unknown extension is reported as unknown rather than forced into a guess.
LANGUAGE_BY_EXTENSION = {
    ".py": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".cs": "C#", ".fs": "F#", ".fsx": "F#", ".vb": "Visual Basic",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala", ".groovy": "Groovy",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".swift": "Swift", ".m": "Objective-C", ".mm": "Objective-C++",
    ".c": "C", ".h": "C/C++ header", ".cc": "C++", ".cpp": "C++", ".cxx": "C++",
    ".hpp": "C++ header", ".hh": "C++ header",
    ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang",
    ".clj": "Clojure", ".cljs": "ClojureScript", ".hs": "Haskell", ".ml": "OCaml",
    ".lua": "Lua", ".pl": "Perl", ".pm": "Perl", ".r": "R", ".jl": "Julia",
    ".zig": "Zig", ".nim": "Nim", ".cr": "Crystal", ".sol": "Solidity",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".ps1": "PowerShell", ".psm1": "PowerShell",
    ".sql": "SQL", ".graphql": "GraphQL", ".gql": "GraphQL",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
    ".tf": "Terraform", ".bicep": "Bicep",
    ".css": "CSS", ".scss": "SCSS", ".sass": "Sass", ".less": "Less",
    ".html": "HTML", ".htm": "HTML",
}

# Manifest filename -> (ecosystem, canonical verify command).
# The command is a starting point the agent must confirm, not a guarantee.
MANIFESTS = {
    "package.json": ("Node.js", "npm test"),
    "deno.json": ("Deno", "deno test"),
    "pyproject.toml": ("Python", "pytest"),
    "setup.py": ("Python", "pytest"),
    "setup.cfg": ("Python", "pytest"),
    "requirements.txt": ("Python", "pytest"),
    "Pipfile": ("Python", "pipenv run pytest"),
    "go.mod": ("Go", "go test ./..."),
    "Cargo.toml": ("Rust", "cargo test"),
    "pom.xml": ("Java/Maven", "mvn test"),
    "build.gradle": ("Java/Gradle", "gradle test"),
    "build.gradle.kts": ("Kotlin/Gradle", "gradle test"),
    "Gemfile": ("Ruby", "bundle exec rspec"),
    "composer.json": ("PHP", "vendor/bin/phpunit"),
    "mix.exs": ("Elixir", "mix test"),
    "rebar.config": ("Erlang", "rebar3 eunit"),
    "Package.swift": ("Swift", "swift test"),
    "pubspec.yaml": ("Dart/Flutter", "dart test"),
    "CMakeLists.txt": ("C/C++ (CMake)", "ctest"),
    "Makefile": ("Make", "make test"),
    "build.zig": ("Zig", "zig build test"),
    "shard.yml": ("Crystal", "crystal spec"),
    "dune-project": ("OCaml", "dune test"),
    "stack.yaml": ("Haskell", "stack test"),
    "cabal.project": ("Haskell", "cabal test"),
    "Project.toml": ("Julia", "julia --project -e 'using Pkg; Pkg.test()'"),
    "DESCRIPTION": ("R", "R CMD check ."),
}

# Manifests identified by extension rather than exact name.
MANIFEST_SUFFIXES = {
    ".csproj": ("C#/.NET", "dotnet test"),
    ".fsproj": ("F#/.NET", "dotnet test"),
    ".vbproj": ("Visual Basic/.NET", "dotnet test"),
    ".sln": (".NET solution", "dotnet test"),
    ".slnx": (".NET solution", "dotnet test"),
}

# Dependency name fragment -> framework label. Matched against manifest text, so
# one table serves every ecosystem's manifest format.
FRAMEWORK_SIGNATURES = [
    ("react", "React"), ("next", "Next.js"), ("vue", "Vue"), ("nuxt", "Nuxt"),
    ("@angular/core", "Angular"), ("svelte", "Svelte"), ("solid-js", "SolidJS"),
    ("express", "Express"), ("fastify", "Fastify"), ("nestjs", "NestJS"),
    ("@nestjs/core", "NestJS"), ("hono", "Hono"),
    ("django", "Django"), ("flask", "Flask"), ("fastapi", "FastAPI"),
    ("sqlalchemy", "SQLAlchemy"), ("pydantic", "Pydantic"), ("celery", "Celery"),
    ("spring-boot", "Spring Boot"), ("quarkus", "Quarkus"), ("micronaut", "Micronaut"),
    ("microsoft.aspnetcore", "ASP.NET Core"), ("microsoft.entityframeworkcore", "EF Core"),
    ("akka", "Akka"), ("mediatr", "MediatR"), ("dapper", "Dapper"),
    ("rails", "Ruby on Rails"), ("sinatra", "Sinatra"),
    ("laravel", "Laravel"), ("symfony", "Symfony"),
    ("gin-gonic", "Gin"), ("gofiber/fiber", "Fiber"), ("labstack/echo", "Echo"),
    ("actix", "Actix"), ("axum", "Axum"), ("rocket", "Rocket"), ("tokio", "Tokio"),
    ("phoenix", "Phoenix"), ("flutter", "Flutter"),
    ("tensorflow", "TensorFlow"), ("torch", "PyTorch"), ("pandas", "pandas"),
]

# Dependency name fragment -> test runner label.
TEST_RUNNER_SIGNATURES = [
    ("vitest", "Vitest"), ("jest", "Jest"), ("mocha", "Mocha"), ("jasmine", "Jasmine"),
    ("playwright", "Playwright"), ("cypress", "Cypress"),
    ("pytest", "pytest"), ("unittest2", "unittest"), ("nose", "nose"),
    ("xunit", "xUnit"), ("nunit", "NUnit"), ("mstest", "MSTest"),
    ("junit", "JUnit"), ("testng", "TestNG"), ("spock", "Spock"),
    ("rspec", "RSpec"), ("minitest", "Minitest"),
    ("phpunit", "PHPUnit"), ("pest", "Pest"),
    ("testify", "Testify"), ("ginkgo", "Ginkgo"),
]

TEST_DIR_NAMES = frozenset({
    "test", "tests", "spec", "specs", "__tests__", "testing",
    "unittest", "unittests", "test_suite", "integration-tests",
})

TEST_FILE_PATTERN = re.compile(
    r"(^test_|_test\.|\.test\.|\.spec\.|Tests?\.|Spec\.|_spec\.)", re.IGNORECASE
)

# Directory name -> the architectural role it conventionally signals. Used to
# offer a starting layer map; the project's real layout always overrides it.
LAYER_HINTS = {
    "domain": "domain", "entities": "domain", "entity": "domain", "model": "domain",
    "models": "domain", "core": "domain", "business": "domain",
    "usecases": "application", "use_cases": "application", "application": "application",
    "app": "application", "services": "application", "handlers": "application",
    "commands": "application", "queries": "application", "features": "application",
    "adapters": "adapter", "controllers": "adapter", "api": "adapter",
    "presentation": "adapter", "ui": "adapter", "views": "adapter", "web": "adapter",
    "graphql": "adapter", "rest": "adapter", "cli": "adapter",
    "infrastructure": "infrastructure", "infra": "infrastructure", "persistence": "infrastructure",
    "repositories": "infrastructure", "repository": "infrastructure", "data": "infrastructure",
    "db": "infrastructure", "database": "infrastructure", "gateways": "infrastructure",
    "clients": "infrastructure", "external": "infrastructure",
}

SOURCE_DIR_NAMES = frozenset({"src", "lib", "source", "sources", "app", "pkg", "internal"})

QUALITY_TOOL_FILES = {
    ".editorconfig": "EditorConfig",
    ".eslintrc": "ESLint", ".eslintrc.json": "ESLint", ".eslintrc.js": "ESLint",
    "eslint.config.js": "ESLint", "eslint.config.mjs": "ESLint",
    ".prettierrc": "Prettier", "prettier.config.js": "Prettier",
    "biome.json": "Biome", ".ruff.toml": "Ruff", "ruff.toml": "Ruff",
    ".flake8": "Flake8", "mypy.ini": "mypy", ".pylintrc": "Pylint",
    ".rubocop.yml": "RuboCop", ".golangci.yml": "golangci-lint",
    ".golangci.yaml": "golangci-lint", "rustfmt.toml": "rustfmt",
    "clippy.toml": "Clippy", ".clang-format": "clang-format",
    "checkstyle.xml": "Checkstyle", "spotbugs.xml": "SpotBugs",
    ".stylecop.json": "StyleCop", "Directory.Build.props": "MSBuild shared props",
    ".pre-commit-config.yaml": "pre-commit", "lefthook.yml": "Lefthook",
    "dependency-cruiser.js": "dependency-cruiser",
    ".dependency-cruiser.js": "dependency-cruiser",
    ".importlinter": "import-linter",
}

# Many projects configure their formatter, linter and test runner inside a manifest
# rather than as a standalone dotfile -- pyproject.toml [tool.ruff], package.json
# "eslintConfig", setup.cfg [flake8]. Looking only for files reports "no quality
# tools" on a project that has four of them, which invites an agent to hand-format.
QUALITY_TOOL_MARKERS = {
    "pyproject.toml": {
        "[tool.black]": "Black", "[tool.ruff": "Ruff", "[tool.isort]": "isort",
        "[tool.mypy]": "mypy", "[tool.pytest": "pytest", "[tool.flake8]": "Flake8",
        "[tool.pylint": "Pylint", "[tool.coverage": "coverage",
    },
    "setup.cfg": {"[flake8]": "Flake8", "[mypy]": "mypy", "[tool:pytest]": "pytest"},
    "package.json": {
        '"eslintConfig"': "ESLint", '"prettier"': "Prettier",
        '"jest"': "Jest", '"biome"': "Biome",
    },
    "Cargo.toml": {"[lints": "Cargo lints"},
    "composer.json": {'"phpstan"': "PHPStan", '"php-cs-fixer"': "PHP-CS-Fixer"},
}

AGENT_CONTEXT_FILES = (
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "CONTRIBUTING.md",
    ".github/copilot-instructions.md", ".cursor/rules", ".windsurf/rules",
    "ARCHITECTURE.md", "docs/architecture.md", "adr", "docs/adr",
)

MAX_FILES_SCANNED = 40000
MANIFEST_READ_LIMIT = 200_000


def is_skippable(directory_name: str) -> bool:
    return directory_name in SKIP_DIRS or (
        directory_name.startswith(".") and directory_name not in {".github"}
    )


def walk_project(root: Path):
    """Yield (relative_path, filename) for project files, pruning noise directories."""
    scanned = 0
    for current_dir, subdirs, filenames in os.walk(root):
        subdirs[:] = sorted(name for name in subdirs if not is_skippable(name))
        for filename in filenames:
            scanned += 1
            if scanned > MAX_FILES_SCANNED:
                return
            absolute = Path(current_dir) / filename
            try:
                yield absolute.relative_to(root), filename
            except ValueError:
                continue


def read_text_safely(path: Path, limit: int = MANIFEST_READ_LIMIT) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def count_languages(files) -> dict:
    counts: dict = {}
    for relative_path, _ in files:
        language = LANGUAGE_BY_EXTENSION.get(relative_path.suffix.lower())
        if language:
            counts[language] = counts.get(language, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def find_manifests(root: Path, files) -> list:
    found = []
    for relative_path, filename in files:
        entry = MANIFESTS.get(filename)
        if entry is None:
            entry = MANIFEST_SUFFIXES.get(relative_path.suffix.lower())
        if entry is None:
            continue
        ecosystem, verify_command = entry
        found.append({
            "path": relative_path.as_posix(),
            "ecosystem": ecosystem,
            "suggested_verify_command": verify_command,
            "depth": len(relative_path.parts) - 1,
        })
    found.sort(key=lambda item: (item["depth"], item["path"]))
    return found


COMMENT_PATTERNS = (
    re.compile(r"<!--.*?-->", re.DOTALL),      # XML: csproj, pom.xml
    re.compile(r"/\*.*?\*/", re.DOTALL),       # C-style block comments
    re.compile(r"(?m)^[ \t]*//.*$"),           # line comments, but not URLs mid-line
    re.compile(r"(?m)^[ \t]*#.*$"),            # TOML, YAML, requirements.txt
)


def strip_comments(text: str) -> str:
    """Remove comment bodies so prose cannot be mistaken for a dependency.

    A .csproj comment containing the English word "next" was enough to report a
    .NET service as using Next.js. Dependency detection must read declarations,
    not commentary.
    """
    for pattern in COMMENT_PATTERNS:
        text = pattern.sub(" ", text)
    return text


def compile_signatures(signatures) -> list:
    """Require a non-alphanumeric boundary around each name.

    Bare substring matching is wrong here: "ava" would match "javascript" and
    "next" would match "nextgen", so a .NET project could be reported as using
    Next.js. Dots, hyphens, quotes and angle brackets all count as boundaries,
    which is what separates a dependency name in JSON, XML, TOML and YAML alike.
    """
    return [
        (re.compile(r"(?<![a-z0-9])" + re.escape(fragment) + r"(?![a-z0-9])"), label)
        for fragment, label in signatures
    ]


FRAMEWORK_MATCHERS = compile_signatures(FRAMEWORK_SIGNATURES)
TEST_RUNNER_MATCHERS = compile_signatures(TEST_RUNNER_SIGNATURES)


def match_signatures(text: str, matchers) -> list:
    lowered = text.lower()
    return sorted({label for pattern, label in matchers if pattern.search(lowered)})


def scan_manifest_contents(root: Path, manifests: list) -> tuple:
    frameworks: set = set()
    test_runners: set = set()
    for manifest in manifests[:40]:
        text = read_text_safely(root / manifest["path"])
        if not text:
            continue
        text = strip_comments(text)
        frameworks.update(match_signatures(text, FRAMEWORK_MATCHERS))
        test_runners.update(match_signatures(text, TEST_RUNNER_MATCHERS))
    return sorted(frameworks), sorted(test_runners)


def find_test_locations(files) -> dict:
    directories: set = set()
    test_file_count = 0
    for relative_path, filename in files:
        parts = relative_path.parts
        in_test_dir = any(part.lower() in TEST_DIR_NAMES for part in parts[:-1])
        looks_like_test = bool(TEST_FILE_PATTERN.search(filename))
        if in_test_dir or looks_like_test:
            if relative_path.suffix.lower() in LANGUAGE_BY_EXTENSION:
                test_file_count += 1
                if len(parts) > 1:
                    directories.add(Path(*parts[:-1]).as_posix())
    return {
        "test_file_count": test_file_count,
        "test_directories": sorted(directories)[:25],
    }


def find_source_roots(root: Path) -> list:
    roots = []
    try:
        entries = sorted(entry for entry in root.iterdir() if entry.is_dir())
    except OSError:
        return roots
    for entry in entries:
        if is_skippable(entry.name):
            continue
        if entry.name.lower() in SOURCE_DIR_NAMES:
            roots.append(entry.name)
    return roots


def infer_layers(files) -> dict:
    """Map conventional directory names to architectural roles, with evidence."""
    layers: dict = {}
    for relative_path, _ in files:
        if relative_path.suffix.lower() not in LANGUAGE_BY_EXTENSION:
            continue
        for part in relative_path.parts[:-1]:
            role = LAYER_HINTS.get(part.lower())
            if role is None:
                continue
            bucket = layers.setdefault(role, {})
            bucket[part] = bucket.get(part, 0) + 1
    return {
        role: dict(sorted(names.items(), key=lambda item: (-item[1], item[0]))[:6])
        for role, names in sorted(layers.items())
    }


def find_quality_tools(root: Path, files) -> list:
    tools = set()
    manifests_seen = set()
    for relative_path, filename in files:
        label = QUALITY_TOOL_FILES.get(filename)
        if label:
            tools.add(label)
        if filename in QUALITY_TOOL_MARKERS and len(relative_path.parts) <= 2:
            manifests_seen.add((filename, relative_path))

    for filename, relative_path in manifests_seen:
        text = read_text_safely(root / relative_path)
        if not text:
            continue
        lowered = text.lower()
        for marker, label in QUALITY_TOOL_MARKERS[filename].items():
            if marker.lower() in lowered:
                tools.add(label)
    return sorted(tools)


def find_existing_context_files(root: Path) -> list:
    return [name for name in AGENT_CONTEXT_FILES if (root / name).exists()]


def infer_purpose(root: Path, manifests: list, languages: dict, tests: dict) -> dict:
    """Guess what kind of thing this project is. Reported as a guess, never a fact."""
    signals = []
    manifest_names = {Path(item["path"]).name for item in manifests}

    if len([m for m in manifests if m["depth"] <= 2]) > 3:
        signals.append("monorepo or multi-project solution")
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        signals.append("containerized deployment")
    if any((root / name).exists() for name in ("openapi.yaml", "openapi.json", "swagger.json")):
        signals.append("HTTP API with a published contract")
    if (root / ".github" / "workflows").is_dir():
        signals.append("CI configured")
    if "package.json" in manifest_names:
        package_text = read_text_safely(root / "package.json").lower()
        if '"bin"' in package_text:
            signals.append("ships a CLI")
        if '"private": true' not in package_text and '"version"' in package_text:
            signals.append("publishable package")
    if tests["test_file_count"] == 0:
        signals.append("no tests detected: treat every change as higher risk")

    return {
        "signals": signals,
        "note": "Purpose is inferred from layout only. Confirm it with the user "
                "before letting it influence a design decision.",
    }


def build_context(root: Path) -> dict:
    files = list(walk_project(root))
    languages = count_languages(files)
    manifests = find_manifests(root, files)
    frameworks, test_runners = scan_manifest_contents(root, manifests)
    tests = find_test_locations(files)

    primary_language = next(iter(languages), None)
    verify_commands = []
    for manifest in manifests:
        command = manifest["suggested_verify_command"]
        if command not in verify_commands:
            verify_commands.append(command)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "clean-code skill / detect_stack.py",
        "root": str(root),
        "confidence": "inferred from file layout; verify before relying on it",
        "primary_language": primary_language,
        "languages": languages,
        "ecosystems": sorted({item["ecosystem"] for item in manifests}),
        "manifests": manifests[:25],
        "frameworks": frameworks,
        "test_runners": test_runners,
        "tests": tests,
        "suggested_verify_commands": verify_commands[:8],
        "source_roots": find_source_roots(root),
        "layer_candidates": infer_layers(files),
        "quality_tools": find_quality_tools(root, files),
        "existing_context_files": find_existing_context_files(root),
        "purpose": infer_purpose(root, manifests, languages, tests),
        "files_scanned": len(files),
    }


def format_mapping(mapping: dict, limit: int) -> str:
    items = list(mapping.items())[:limit]
    return ", ".join(f"{key} ({value})" for key, value in items) or "none detected"


def render_summary(context: dict) -> str:
    lines = [
        "Project context (inferred; confirm before relying on it)",
        "",
        f"  Primary language : {context['primary_language'] or 'unknown'}",
        f"  Languages        : {format_mapping(context['languages'], 6)}",
        f"  Ecosystems       : {', '.join(context['ecosystems']) or 'none detected'}",
        f"  Frameworks       : {', '.join(context['frameworks']) or 'none detected'}",
        f"  Test runners     : {', '.join(context['test_runners']) or 'none detected'}",
        f"  Test files       : {context['tests']['test_file_count']}",
        f"  Source roots     : {', '.join(context['source_roots']) or 'repository root'}",
        f"  Quality tools    : {', '.join(context['quality_tools']) or 'none detected'}",
    ]

    verify = context["suggested_verify_commands"]
    lines.append(f"  Verify with      : {verify[0] if verify else 'unknown; ask the user'}")
    if len(verify) > 1:
        lines.append(f"  Other candidates : {', '.join(verify[1:])}")

    layers = context["layer_candidates"]
    if layers:
        lines.append("")
        lines.append("  Layer candidates (conventional names found in paths):")
        for role, names in layers.items():
            lines.append(f"    {role:<15}{format_mapping(names, 4)}")
        lines.append("    Direction of dependencies is NOT verified here. Declare the")
        lines.append("    intended layering in .clean/architecture.md, then run")
        lines.append("    check_boundaries.py to test whether the code obeys it.")

    context_files = context["existing_context_files"]
    if context_files:
        lines.append("")
        lines.append(f"  Read these first : {', '.join(context_files)}")

    signals = context["purpose"]["signals"]
    if signals:
        lines.append("")
        lines.append("  Signals:")
        lines.extend(f"    - {signal}" for signal in signals)

    return "\n".join(lines)


def parse_arguments(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect a project's stack, layout, and verification commands.",
    )
    parser.add_argument("--root", default=".", help="project directory (default: .)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a summary")
    parser.add_argument("--write", action="store_true",
                        help="save the result to <root>/.clean/context.json")
    parser.add_argument("--output", default=None,
                        help="write the JSON to this path instead of the default")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    arguments = parse_arguments(argv if argv is not None else sys.argv[1:])

    root = Path(arguments.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    context = build_context(root)
    payload = json.dumps(context, indent=2, ensure_ascii=False)

    if arguments.json:
        print(payload)
    else:
        print(render_summary(context))

    if arguments.write or arguments.output:
        destination = Path(arguments.output) if arguments.output else root / ".clean" / "context.json"
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(payload + "\n", encoding="utf-8")
        except OSError as error:
            print(f"error: could not write {destination}: {error}", file=sys.stderr)
            return 1
        if not arguments.json:
            print(f"\nSaved: {destination}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
