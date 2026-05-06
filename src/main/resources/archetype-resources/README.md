#set( $symbol_pound = '#' )
#set( $symbol_dollar = '$' )
${symbol_pound} ${packageName} (${artifactId})

${packageDescription}

Java library scaffolded from the **Nebula** archetype. Publishes to the RecruitCRM
**java-packages** AWS CodeArtifact repository via Jenkins + semantic-release.

${symbol_pound}${symbol_pound} Requirements

- **Java 21**
- **Maven 3.6.3+**
- AWS CodeArtifact credentials (env vars below) for resolving and publishing internal RecruitCRM packages.

${symbol_pound}${symbol_pound} Build & Test

```bash
${symbol_pound} Compile and run tests
./mvnw verify

${symbol_pound} Install to local repository (e.g. for dependent microservices)
./mvnw install

${symbol_pound} Skip tests
./mvnw install -DskipTests
```

Code style is enforced: **Spotless** (Eclipse JDT formatter, profile in `code-formatting/`)
runs on `verify`, and **Checkstyle** (Spring Java Format) runs in the `validate` phase.
Test coverage is reported via JaCoCo. Run the SonarCloud profile with `./mvnw -Pcoverage verify`.

${symbol_pound}${symbol_pound} Pre-commit hook

A `pre-commit` hook in `.githooks/` runs Spotless + Checkstyle before every commit.
Install once per clone:

```bash
git config core.hooksPath .githooks
```

See `.githooks/README.md` for details.

${symbol_pound}${symbol_pound} Project Structure

```
${artifactId}/
├── pom.xml                          ${symbol_pound} Inherits spring-boot-starter-parent ${springBootVersion}
├── README.md
├── settings.xml                     ${symbol_pound} Maven CodeArtifact credentials
├── checkstyle.xml + checkstyle-suppressions.xml
├── lombok.config + .springjavaformatconfig
├── code-formatting/                 ${symbol_pound} Eclipse JDT formatter profile (Spotless)
├── .githooks/                       ${symbol_pound} Pre-commit Spotless+Checkstyle
├── .github/                         ${symbol_pound} CODEOWNERS + workflows/code_reviewer.yml
├── scripts/jenkins/Build.Jenkinsfile
├── package.json + release.config.js ${symbol_pound} semantic-release for auto-versioning
├── pull_request_template.md
├── mvnw + mvnw.cmd + .mvn/
└── src/
    ├── main/
    │   ├── java/${packageInPathFormat}/
    │   │   └── ${packageName}AutoConfiguration.java   ${symbol_pound} Spring Boot autoconfig entry point
    │   └── resources/
    │       └── META-INF/spring/
    │           └── org.springframework.boot.autoconfigure.AutoConfiguration.imports
    └── test/
        ├── java/${packageInPathFormat}/
        │   └── ${packageName}AutoConfigurationTests.java
        └── resources/
            └── mockito-extensions/   ${symbol_pound} Drop org.mockito.plugins.MockMaker here for inline mocking
```

${symbol_pound}${symbol_pound} How consumers use this library

Once published, any Spring Boot 3 application that adds this artifact as a dependency
automatically picks up `${packageName}AutoConfiguration` (registered via
`META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`).
That triggers `@ComponentScan`, `@EntityScan`, and `@EnableJpaRepositories` for
`${package}` so all your library's beans, JPA entities and repositories light up
without the consumer having to add their own `@Configuration`.

${symbol_pound}${symbol_pound} CodeArtifact env vars

Required to resolve internal deps and publish:

```bash
export AWS_CODEARTIFACT_REPOSITORY_USERNAME=aws
export CODEARTIFACT_AUTH_TOKEN=${symbol_dollar}(aws codeartifact get-authorization-token \
  --domain recruitcrm \
  --domain-owner 813287113117 \
  --region ap-south-1 \
  --query authorizationToken --output text)
export JAVA_PACKAGES_CODEARTIFACT_REPOSITORY_DOMAIN=recruitcrm
export JAVA_PACKAGES_CODEARTIFACT_REPOSITORY_ID=java-packages
export JAVA_PACKAGES_CODEARTIFACT_REPOSITORY_URL=https://recruitcrm-813287113117.d.codeartifact.ap-south-1.amazonaws.com/maven/java-packages/
```

${symbol_pound}${symbol_pound} Releasing

Releases are managed by **semantic-release** in the Jenkins pipeline
(`scripts/jenkins/Build.Jenkinsfile`):

- Push to `main` → publishes a stable version (e.g. `1.4.0`) to CodeArtifact and
  cuts a GitHub Release.
- Push to `dev`, `feature-*`, `enhancement-*`, `bugfix-*`, etc. → publishes a
  prerelease (e.g. `1.4.0-feature-foo.1`).

Bump direction is derived from Conventional Commits (`feat:` → minor, `fix:` →
patch, `BREAKING CHANGE:` → major).

${symbol_pound}${symbol_pound} SonarCloud

Project key: `${sonarProjectKey}` — bound to the **workforce-cloud-tech** organisation.

${symbol_pound}${symbol_pound} License

Internal use only — RecruitCRM.
