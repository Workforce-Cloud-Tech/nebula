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

---

## Generate a new package

### Option A — convenience script

```bash
./generate.sh
```

The script prompts for everything (artifact id, package name, description, etc.)
and runs `mvn archetype:generate` in the current directory. The new project
will land at `./<artifactId>/`.

Non-interactive:

```bash
./generate.sh \
  --artifact-id geocoding-package \
  --package-name Geocoding \
  --group-id io.recruitcrm.geocoding \
  --description "RecruitCRM geocoding shared library" \
  --output-dir ~/code/recruitcrm
```

### Option B — raw Maven

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
├── generate.sh                                   # Helper wrapper around `mvn archetype:generate`
└── src/
    ├── main/resources/
    │   ├── META-INF/maven/archetype-metadata.xml # Property + fileSet descriptor
    │   └── archetype-resources/                  # Templated project skeleton
    └── test/resources/projects/basic/            # Smoke test config
```

---

## Sister archetype

- **[Starforge](../starforge)** — scaffolds **microservices** (Spring Boot apps
  with controllers, security, deployment scripts, CodeDeploy, etc.).
- **Nebula** (this repo) — scaffolds **packages** (jOOQ-friendly libraries
  published to CodeArtifact, no application code, no deployment).

Pick the archetype that matches what you're building.
