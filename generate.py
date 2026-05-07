#!/usr/bin/env python3
"""Nebula — cross-platform Python wrapper around ``mvn archetype:generate``.

The actual scaffolding is performed by Maven Archetype + Velocity (the same
template engine the archetype was always built around). This script only
handles the CLI / interactive UX and validation that the old ``generate.sh``
did, but in pure stdlib Python so it runs identically on macOS, Linux and
Windows.

Usage examples::

    python3 generate.py
    python3 generate.py --artifact-id mylib-package --package-name Mylib
    python3 generate.py --artifact-id mylib-package --output-dir ~/code

Power-user overrides (``--repo-url``, ``--slack-channel-id``, ``--codeowners``)
are forwarded to Maven only when explicitly set, so the archetype-side
defaults still apply otherwise. Generated projects ship a
``CHANGE_ME_SLACK_CHANNEL_ID`` placeholder for Slack so it's easy to grep +
replace later.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Archetype coordinates (must match the root pom.xml)
# ---------------------------------------------------------------------------

ARCHETYPE_GROUP_ID = "io.recruitcrm.nebula"
ARCHETYPE_ARTIFACT_ID = "nebula-archetype"
ARCHETYPE_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def to_pascal_case(s: str) -> str:
    """``"geocoding-package"`` / ``"geocoding_package"`` -> ``"GeocodingPackage"``."""

    parts = re.split(r"[-_ ]+", s or "")
    return "".join(p[:1].upper() + p[1:].lower() for p in parts if p)


def strip_package_suffix(s: str) -> str:
    """Strip a trailing ``-package`` / ``_package`` (case-insensitive)."""

    return re.sub(r"[-_]?package$", "", s or "", flags=re.IGNORECASE)


def to_lower_alpha(s: str) -> str:
    """Lowercase and strip everything that isn't ``[a-z0-9]``."""

    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def prompt(label: str, default: Optional[str] = None) -> str:
    if not is_interactive():
        if default is None or default == "":
            sys.stderr.write(
                f"Missing required value for {label!r} "
                f"(no default available, stdin is not a tty).\n"
            )
            sys.exit(1)
        return default
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            answer = input(f"{label}{suffix}: ").strip()
        except EOFError:
            answer = ""
        if answer:
            return answer
        if default is not None and default != "":
            return default


def expand_user_path(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def find_mvn() -> Optional[str]:
    """Locate the Maven launcher on PATH.

    ``shutil.which`` honours ``PATHEXT`` on Windows, so a single lookup picks
    up ``mvn.cmd`` automatically there.
    """

    return shutil.which("mvn")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="generate.py",
        description=(
            "Forge a new RecruitCRM Java package by invoking "
            "`mvn archetype:generate` against the Nebula archetype."
        ),
    )
    ap.add_argument("--group-id", default=None)
    ap.add_argument("--artifact-id", default=None)
    ap.add_argument("--version", default=None)
    ap.add_argument("--package", default=None)
    ap.add_argument("--package-name", default=None)
    ap.add_argument("--package-name-lower", default=None)
    ap.add_argument("--description", default=None)
    ap.add_argument("--spring-boot-version", default=None)
    ap.add_argument("--sonar-key", default=None)
    # Power-user overrides — left unset by default so archetype-side defaults
    # in archetype-metadata.xml apply.
    ap.add_argument("--repo-url", default=None)
    ap.add_argument("--slack-channel-id", default=None)
    ap.add_argument("--codeowners", default=None)
    ap.add_argument("--output-dir", default=None)
    return ap.parse_args(argv)


def collect_inputs(args: argparse.Namespace, default_output_dir: Path) -> dict:
    """Resolve every templating variable from CLI args and/or interactive prompts."""

    artifact_id = args.artifact_id or prompt(
        "Maven artifactId (e.g. geocoding-package, scoring-package)"
    )
    short_name = strip_package_suffix(artifact_id)
    package_name = args.package_name or prompt(
        "Package name in PascalCase (e.g. Geocoding, Scoring)",
        to_pascal_case(short_name),
    )
    package_name_lower = args.package_name_lower or prompt(
        "Package name lowercase",
        to_lower_alpha(short_name),
    )
    group_id = args.group_id or prompt(
        "groupId", f"io.recruitcrm.{package_name_lower}"
    )
    version = args.version or prompt("version", "1.0.0")
    package = args.package or prompt("Java package", group_id)
    description = args.description or prompt(
        "Description", f"RecruitCRM {package_name} shared library"
    )
    spring_boot_version = args.spring_boot_version or prompt(
        "spring-boot-starter-parent version", "3.5.8"
    )
    sonar_key = args.sonar_key or prompt(
        "Sonar project key", f"Workforce-Cloud-Tech_{artifact_id}"
    )
    output_dir = args.output_dir or prompt(
        f"Output directory (where to create {artifact_id}/)",
        str(default_output_dir),
    )

    return {
        "groupId": group_id,
        "artifactId": artifact_id,
        "version": version,
        "package": package,
        "packageName": package_name,
        "packageNameLower": package_name_lower,
        "packageDescription": description,
        "springBootVersion": spring_boot_version,
        "sonarProjectKey": sonar_key,
        # Optional overrides (None when not supplied).
        "repoUrl": args.repo_url,
        "slackChannelId": args.slack_channel_id,
        "codeowners": args.codeowners,
        # Internal — not a Maven property, popped before the build.
        "_output_dir": output_dir,
    }


def validate_target(
    output_dir: str,
    artifact_id: str,
    script_dir: Path,
    default_output_dir: Path,
) -> Optional[Path]:
    """Return the resolved output directory, or ``None`` on a fatal issue.

    Mirrors the safety checks from the old ``generate.sh``:
      * refuse to scaffold inside the archetype repo,
      * refuse if the output dir already contains a ``pom.xml`` (Maven would
        otherwise try to add the new project as a ``<module>`` and fail),
      * refuse if a directory named after the artifactId already exists.
    """

    output_path = expand_user_path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if output_path == script_dir or is_inside(output_path, script_dir):
        sys.stderr.write(
            f"Refusing to generate inside the archetype repo: {output_path}\n"
            f"Pick a different --output-dir (default is {default_output_dir}).\n"
        )
        return None

    if (output_path / "pom.xml").exists():
        sys.stderr.write(
            f"\nERROR: {output_path} contains a pom.xml.\n"
            "       Running mvn archetype:generate here would try to add the\n"
            "       new package as a <module> of that pom and fail.\n"
            "       cd somewhere outside any Maven project, or pass --output-dir.\n\n"
        )
        return None

    if (output_path / artifact_id).exists():
        sys.stderr.write(
            f"Target already exists: {output_path / artifact_id}\n"
            "Move or remove it before re-running.\n"
        )
        return None

    return output_path


def build_mvn_command(mvn: str, ctx: dict) -> list[str]:
    cmd = [
        mvn,
        "archetype:generate",
        "-B",
        f"-DarchetypeGroupId={ARCHETYPE_GROUP_ID}",
        f"-DarchetypeArtifactId={ARCHETYPE_ARTIFACT_ID}",
        f"-DarchetypeVersion={ARCHETYPE_VERSION}",
        f"-DgroupId={ctx['groupId']}",
        f"-DartifactId={ctx['artifactId']}",
        f"-Dversion={ctx['version']}",
        f"-Dpackage={ctx['package']}",
        f"-DpackageName={ctx['packageName']}",
        f"-DpackageNameLower={ctx['packageNameLower']}",
        f"-DpackageDescription={ctx['packageDescription']}",
        f"-DspringBootVersion={ctx['springBootVersion']}",
        f"-DsonarProjectKey={ctx['sonarProjectKey']}",
        "-DinteractiveMode=false",
    ]
    # Only forward the power-user overrides when explicitly set, so the
    # archetype-side defaults still apply for everyone else.
    if ctx.get("repoUrl"):
        cmd.append(f"-DrepoUrl={ctx['repoUrl']}")
    if ctx.get("slackChannelId"):
        cmd.append(f"-DslackChannelId={ctx['slackChannelId']}")
    if ctx.get("codeowners"):
        cmd.append(f"-Dcodeowners={ctx['codeowners']}")
    return cmd


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    script_dir = Path(__file__).resolve().parent
    default_output_dir = script_dir.parent

    mvn = find_mvn()
    if mvn is None:
        sys.stderr.write(
            "Maven (`mvn`) was not found on PATH.\n"
            "Install Maven 3.8+ and re-run, or use Maven directly with\n"
            "`mvn archetype:generate -DarchetypeGroupId="
            f"{ARCHETYPE_GROUP_ID} ...`.\n"
        )
        return 1

    print()
    print("Nebula — RecruitCRM Java Package Generator")
    print("===========================================")

    ctx = collect_inputs(args, default_output_dir)
    output_dir = ctx.pop("_output_dir")
    output_path = validate_target(
        output_dir, ctx["artifactId"], script_dir, default_output_dir
    )
    if output_path is None:
        return 1

    cmd = build_mvn_command(mvn, ctx)
    target = output_path / ctx["artifactId"]

    print(f"\nGenerating {ctx['artifactId']} in {target} ...\n")
    # Maven creates the new project in its current working directory, so run
    # it inside the chosen output dir. Stream stdout/stderr live so the user
    # sees Maven's normal output.
    completed = subprocess.run(cmd, cwd=str(output_path), check=False)
    if completed.returncode != 0:
        sys.stderr.write(
            f"\nmvn archetype:generate failed (exit code {completed.returncode}).\n"
        )
        return completed.returncode

    print("\nDone.")
    print()
    print("Next steps:")
    print(f"  cd \"{target}\"")
    print("  git init && git config core.hooksPath .githooks")
    print("  ./mvnw verify")
    print()
    print(
        "TIP: search the generated repo for 'CHANGE_ME_SLACK_CHANNEL_ID' to wire"
    )
    print("     up Jenkins notifications, and edit .github/CODEOWNERS to set reviewers.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
