# Nebula — RecruitCRM Java Package Archetype

A **Maven archetype** that scaffolds a fresh Java 21 / Spring Boot 3 **library**
(publishable to AWS CodeArtifact) for the RecruitCRM platform with a single
command. Modeled after [`recruitcrm-search-package-java`](https://github.com/Workforce-Cloud-Tech/recruitcrm-search-package-java),
so every new package starts with the same Maven, Spotless, Checkstyle, JaCoCo,
SonarCloud, semantic-release, Jenkins, and pre-commit conventions already wired
in.

> Sister archetype to **[Starforge](../starforge)** (which scaffolds new
> microservices). Nebula is for **shared libraries** — the things that get
> deployed to CodeArtifact and consumed by services like Aries.

---

## What it generates

```
my-new-package/
├── pom.xml                          # Inherits spring-boot-starter-parent (default 3.5.8), publishes to CodeArtifact
├── README.md
├── settings.xml                     # Maven CodeArtifact credentials wiring
├── checkstyle.xml + checkstyle-suppressions.xml
├── lombok.config + .springjavaformatconfig
├── code-formatting/                 # Eclipse JDT formatter profile used by Spotless
│   ├── eclipse-java-format.xml
│   └── eclipse.importorder
├── .githooks/                       # pre-commit Spotless + Checkstyle
│   ├── pre-commit
│   └── README.md
├── .github/
│   ├── CODEOWNERS
│   └── workflows/code_reviewer.yml
├── scripts/jenkins/Build.Jenkinsfile
├── package.json + release.config.js # semantic-release for auto-versioning
├── pull_request_template.md
├── mvnw + mvnw.cmd + .mvn/
└── src/
    ├── main/
    │   ├── java/<your.package>/
    │   │   └── <PackageName>AutoConfiguration.java     # Spring Boot autoconfig entry point
    │   └── resources/
    │       └── META-INF/spring/
    │           └── org.springframework.boot.autoconfigure.AutoConfiguration.imports
    └── test/
        ├── java/<your.package>/
        │   └── <PackageName>AutoConfigurationTests.java
        └── resources/
            └── mockito-extensions/  # Drop org.mockito.plugins.MockMaker here when needed
```

The Spring Boot AutoConfiguration import file ensures any Spring Boot 3
application that adds the published jar as a dependency automatically picks up
the library's `@ComponentScan` / `@EntityScan` / `@EnableJpaRepositories` for
its package — no extra wiring needed by consumers.

---

## One-time install

```bash
cd nebula
mvn clean install -Darchetype.test.skip=true
```

This publishes `io.recruitcrm.nebula:nebula-archetype:1.0.0` into your local
`~/.m2`. Bump the archetype, re-run, done.

### Prerequisites

- **Java 21** + **Maven 3.8+** on `PATH` (Maven Archetype + Velocity do the
  actual templating).
- **Python 3.9+** on `PATH` (only used to drive the prompts and call Maven —
  no third-party Python deps; standard library only).

---

## Generate a new package

### Option A — Python CLI (recommended)

```bash
python3 generate.py
```

`generate.py` is a small, cross-platform replacement for the old
`generate.sh`. It uses only the Python standard library: it prompts for the
required values (artifact id, package name, description, etc.), validates
them, and then shells out to `mvn archetype:generate` to do the real
templating via **Maven Archetype + Velocity**. Works identically on macOS,
Linux and Windows — no Bash required.

The new project is written to `<output-dir>/<artifactId>/` (default
`output-dir` is the **parent** of this archetype repo, so the new package
lands as a sibling rather than nested inside Nebula).

Pass everything non-interactively:

```bash
python3 generate.py \
  --artifact-id geocoding-package \
  --package-name Geocoding \
  --group-id io.recruitcrm.geocoding \
  --description "RecruitCRM geocoding shared library" \
  --output-dir ~/code/recruitcrm
```

Power-user overrides (forwarded to Maven only when explicitly set, so the
archetype-side defaults from `archetype-metadata.xml` still apply otherwise):

```bash
python3 generate.py \
  --artifact-id geocoding-package \
  --repo-url https://github.com/Workforce-Cloud-Tech/geocoding-package \
  --slack-channel-id C0123456789 \
  --codeowners "@Workforce-Cloud-Tech/search"
```

Run `python3 generate.py --help` for the full flag list.

### Option B — raw Maven

If you'd rather skip the Python wrapper entirely, call Maven directly:

```bash
mvn archetype:generate \
  -DarchetypeGroupId=io.recruitcrm.nebula \
  -DarchetypeArtifactId=nebula-archetype \
  -DarchetypeVersion=1.0.0 \
  -DgroupId=io.recruitcrm.geocoding \
  -DartifactId=geocoding-package \
  -Dversion=1.0.0-SNAPSHOT \
  -Dpackage=io.recruitcrm.geocoding \
  -DpackageName=Geocoding \
  -DpackageNameLower=geocoding \
  -DpackageDescription="RecruitCRM geocoding shared library" \
  -DspringBootVersion=3.5.8 \
  -DinteractiveMode=false
```

Both options end up running the same Maven Archetype + Velocity pipeline; the
Python wrapper just adds prompts, defaults and the safety checks the old
shell script had.

---

## Required properties

| Property             | Example                                                 | Notes                                                         |
|---------------------|---------------------------------------------------------|---------------------------------------------------------------|
| `groupId`            | `io.recruitcrm.geocoding`                              | Maven groupId                                                 |
| `artifactId`         | `geocoding-package`                                    | Maven artifactId; usually the repo name                       |
| `version`            | `1.0.0`                                        | Initial version (semantic-release will manage from there)     |
| `package`            | `io.recruitcrm.geocoding`                              | Java root package                                             |
| `packageName`        | `Geocoding`                                            | PascalCase; drives the `<PackageName>AutoConfiguration` class |
| `packageNameLower`   | `geocoding`                                            | Defaults to `artifactId`; used in a few config strings        |
| `packageDescription` | `RecruitCRM geocoding shared library`                  | Free-form; lands in README + pom `<description>`              |
| `springBootVersion`  | `3.5.8`                                                | spring-boot-starter-parent version                            |
| `sonarProjectKey`    | `Workforce-Cloud-Tech_geocoding-package`               | Defaults to `Workforce-Cloud-Tech_${artifactId}`              |

---

## Layout of this repository

```
nebula/
├── pom.xml                                       # The archetype itself (packaging=maven-archetype)
├── README.md                                     # This file
├── generate.py                                   # Cross-platform Python wrapper around `mvn archetype:generate`
└── src/
    ├── main/resources/
    │   ├── META-INF/maven/archetype-metadata.xml # Property + fileSet descriptor (consumed by mvn archetype)
    │   └── archetype-resources/                  # Templated project skeleton (Velocity placeholders)
    └── test/resources/projects/basic/            # Maven smoke-test config
```

`generate.py` is a thin orchestration layer: it gathers inputs, validates the
target directory, and invokes `mvn archetype:generate`. The actual file
rendering — substituting `${packageName}`, relocating files under
`src/main/java/<package as path>/...`, etc. — is done by Maven Archetype +
Velocity, exactly as before. The only thing we removed was the Bash script;
the templating engine and template files are unchanged.

---

## Sister archetype

- **[Starforge](../starforge)** — scaffolds **microservices** (Spring Boot apps
  with controllers, security, deployment scripts, CodeDeploy, etc.).
- **Nebula** (this repo) — scaffolds **packages** (jOOQ-friendly libraries
  published to CodeArtifact, no application code, no deployment).

Pick the archetype that matches what you're building.
