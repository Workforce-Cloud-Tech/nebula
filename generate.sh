#!/usr/bin/env bash
# Nebula — convenience wrapper around `mvn archetype:generate` for the
# RecruitCRM Java package archetype.
#
# Usage:
#   ./generate.sh                                                      # interactive
#   ./generate.sh --artifact-id mylib-package --package-name Mylib
#   ./generate.sh --artifact-id mylib-package --output-dir ~/code      # non-prompt for location
#
# Prompts only for the basics (artifactId, package name, groupId, version,
# Java package, description, Spring Boot version, sonar key, output dir).
#
# By default the new project folder is created in the PARENT directory of
# this archetype repo, NOT inside it.
#
# repoUrl, slackChannelId and codeowners are filled in from sensible defaults
# defined in archetype-metadata.xml unless you override them with the matching
# flags. Generated projects ship a `CHANGE_ME_SLACK_CHANNEL_ID` placeholder for
# Slack so it's easy to grep + replace later.

set -euo pipefail

ARCHETYPE_GROUP_ID="io.recruitcrm.nebula"
ARCHETYPE_ARTIFACT_ID="nebula-archetype"
ARCHETYPE_VERSION="1.0.0"

# Resolve where this script (i.e. the archetype repo) lives so we can
#   (a) default the output dir to its parent (sibling folders), and
#   (b) refuse to scaffold a new project on top of the archetype itself.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_OUTPUT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---- Defaults --------------------------------------------------------------
GROUP_ID=""
ARTIFACT_ID=""
VERSION="1.0.0"
PACKAGE=""
PACKAGE_NAME=""
PACKAGE_NAME_LOWER=""
DESCRIPTION=""
SPRING_BOOT_VERSION="3.5.8"
SONAR_KEY=""

# Power-user overrides — silently use archetype defaults if not set.
REPO_URL=""
SLACK_CHANNEL_ID=""
CODEOWNERS=""

OUTPUT_DIR=""

# ---- Parse flags -----------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --group-id)             GROUP_ID="$2"; shift 2 ;;
        --artifact-id)          ARTIFACT_ID="$2"; shift 2 ;;
        --version)              VERSION="$2"; shift 2 ;;
        --package)              PACKAGE="$2"; shift 2 ;;
        --package-name)         PACKAGE_NAME="$2"; shift 2 ;;
        --package-name-lower)   PACKAGE_NAME_LOWER="$2"; shift 2 ;;
        --description)          DESCRIPTION="$2"; shift 2 ;;
        --spring-boot-version)  SPRING_BOOT_VERSION="$2"; shift 2 ;;
        --sonar-key)            SONAR_KEY="$2"; shift 2 ;;
        --repo-url)             REPO_URL="$2"; shift 2 ;;
        --slack-channel-id)     SLACK_CHANNEL_ID="$2"; shift 2 ;;
        --codeowners)           CODEOWNERS="$2"; shift 2 ;;
        --output-dir)           OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            grep '^#' "$0" | sed 's/^# *//;s/^#//'
            exit 0
            ;;
        *)
            echo "Unknown flag: $1" >&2
            exit 1
            ;;
    esac
done

# ---- Helpers ---------------------------------------------------------------
to_pascal_case() {
    # turns "geocoding-package" or "geocoding_package" into "GeocodingPackage"
    printf '%s' "$1" \
        | awk -F'[-_ ]' '{ for (i=1; i<=NF; i++) printf "%s%s", toupper(substr($i,1,1)), tolower(substr($i,2)) }'
}

# Strip a trailing "-package" before deriving things like the Java root package.
strip_package_suffix() {
    printf '%s' "$1" | sed -E 's/[-_]?package$//I'
}

to_lower_alpha() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -dc 'a-z0-9'
}

is_interactive() {
    [[ -t 0 ]] && [[ -t 1 ]]
}

prompt() {
    local var_name="$1"
    local prompt_msg="$2"
    local default_val="${3:-}"
    local current_val
    eval "current_val=\${$var_name}"

    if [[ -n "$current_val" ]]; then
        return
    fi

    if ! is_interactive; then
        if [[ -z "$default_val" ]]; then
            echo "Missing required value for $var_name (no default available, stdin is not a tty)." >&2
            exit 1
        fi
        eval "$var_name=\$default_val"
        return
    fi

    local input
    if [[ -n "$default_val" ]]; then
        read -r -p "$prompt_msg [$default_val]: " input
        input="${input:-$default_val}"
    else
        while [[ -z "${input:-}" ]]; do
            read -r -p "$prompt_msg: " input
        done
    fi
    eval "$var_name=\$input"
}

# ---- Interactive prompts (basics only) -------------------------------------
echo ""
echo "Nebula — RecruitCRM Java Package Generator"
echo "==========================================="

prompt ARTIFACT_ID         "Maven artifactId (e.g. geocoding-package, scoring-package)"
SHORT_NAME="$(strip_package_suffix "$ARTIFACT_ID")"
prompt PACKAGE_NAME        "Package name in PascalCase (e.g. Geocoding, Scoring)"  "$(to_pascal_case "$SHORT_NAME")"
prompt PACKAGE_NAME_LOWER  "Package name lowercase"                                "$(to_lower_alpha "$SHORT_NAME")"
prompt GROUP_ID            "groupId"                                               "io.recruitcrm.$PACKAGE_NAME_LOWER"
prompt VERSION             "version"                                               "$VERSION"
prompt PACKAGE             "Java package"                                          "$GROUP_ID"
prompt DESCRIPTION         "Description"                                           "RecruitCRM $PACKAGE_NAME shared library"
prompt SPRING_BOOT_VERSION "spring-boot-starter-parent version"                    "$SPRING_BOOT_VERSION"
prompt SONAR_KEY           "Sonar project key"                                     "Workforce-Cloud-Tech_$ARTIFACT_ID"
prompt OUTPUT_DIR          "Output directory (where to create ${ARTIFACT_ID}/)"    "$DEFAULT_OUTPUT_DIR"

# Expand a leading ~ to $HOME (read -r doesn't do this for us).
case "$OUTPUT_DIR" in
    "~")     OUTPUT_DIR="$HOME" ;;
    "~/"*)   OUTPUT_DIR="$HOME/${OUTPUT_DIR#~/}" ;;
esac

mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"

# Refuse to scaffold inside the archetype repo itself (would clobber sources).
if [[ "$OUTPUT_DIR" == "$SCRIPT_DIR" ]] || [[ "$OUTPUT_DIR" == "$SCRIPT_DIR"/* ]]; then
    echo "Refusing to generate inside the archetype repo: $OUTPUT_DIR" >&2
    echo "Pick a different --output-dir (default is $DEFAULT_OUTPUT_DIR)." >&2
    exit 1
fi

# Refuse to run inside any other Maven project — `mvn archetype:generate`
# tries to register the new project as a child <module> of the surrounding pom,
# which only works if its packaging is "pom". Otherwise Maven errors with
# "Unable to add module to the current project as it is not of packaging type 'pom'".
if [[ -f "$OUTPUT_DIR/pom.xml" ]]; then
    echo "" >&2
    echo "ERROR: $OUTPUT_DIR contains a pom.xml." >&2
    echo "       Running mvn archetype:generate here would try to add the new" >&2
    echo "       package as a <module> of that pom and fail." >&2
    echo "" >&2
    echo "       Pick a different output directory (default is $DEFAULT_OUTPUT_DIR)" >&2
    echo "       via --output-dir <path>, or cd somewhere outside any Maven project." >&2
    echo "" >&2
    exit 1
fi

if [[ -e "$OUTPUT_DIR/$ARTIFACT_ID" ]]; then
    echo "Target already exists: $OUTPUT_DIR/$ARTIFACT_ID" >&2
    echo "Move or remove it before re-running." >&2
    exit 1
fi

echo ""
echo "Generating ${ARTIFACT_ID} in ${OUTPUT_DIR}/${ARTIFACT_ID} ..."
echo ""

cd "$OUTPUT_DIR"

# Build the mvn arg list, only passing the optional overrides when explicitly set.
MVN_ARGS=(
    "archetype:generate" "-B"
    "-DarchetypeGroupId=$ARCHETYPE_GROUP_ID"
    "-DarchetypeArtifactId=$ARCHETYPE_ARTIFACT_ID"
    "-DarchetypeVersion=$ARCHETYPE_VERSION"
    "-DgroupId=$GROUP_ID"
    "-DartifactId=$ARTIFACT_ID"
    "-Dversion=$VERSION"
    "-Dpackage=$PACKAGE"
    "-DpackageName=$PACKAGE_NAME"
    "-DpackageNameLower=$PACKAGE_NAME_LOWER"
    "-DpackageDescription=$DESCRIPTION"
    "-DspringBootVersion=$SPRING_BOOT_VERSION"
    "-DsonarProjectKey=$SONAR_KEY"
    "-DinteractiveMode=false"
)
[[ -n "$REPO_URL" ]]         && MVN_ARGS+=("-DrepoUrl=$REPO_URL")
[[ -n "$SLACK_CHANNEL_ID" ]] && MVN_ARGS+=("-DslackChannelId=$SLACK_CHANNEL_ID")
[[ -n "$CODEOWNERS" ]]       && MVN_ARGS+=("-Dcodeowners=$CODEOWNERS")

mvn "${MVN_ARGS[@]}"

echo ""
echo "Done."
echo ""
echo "Next steps:"
echo "  cd \"$OUTPUT_DIR/$ARTIFACT_ID\""
echo "  git init && git config core.hooksPath .githooks"
echo "  ./mvnw verify"
echo ""
echo "TIP: search the generated repo for 'CHANGE_ME_SLACK_CHANNEL_ID' to wire"
echo "     up Jenkins notifications, and edit .github/CODEOWNERS to set reviewers."
echo ""
