#set( $symbol_dollar = '$' )
pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: "v1"
kind: "Pod"
metadata:
  annotations:
    karpenter.sh/do-not-disrupt: "true"
  namespace: "jenkins"
spec:
  serviceAccountName: "java21-sa"
  automountServiceAccountToken: false
  containers:
  - image: "004468257635.dkr.ecr.ap-south-1.amazonaws.com/jenkins-inbound-agent-java-21:latest"
    imagePullPolicy: "IfNotPresent"
    name: "jnlp"
    resources:
      limits:
        cpu: "3000m"
        memory: "6Gi"
        ephemeral-storage: "10Gi"
      requests:
        cpu: "2000m"
        memory: "3Gi"
        ephemeral-storage: "10Gi"
    tty: true
    volumeMounts:
    - mountPath: "/home/jenkins/agent"
      name: "workspace-volume"
      readOnly: false
    - mountPath: "/cache/.m2/repository"
      name: "maven-cache"
      readOnly: false
    workingDir: "/home/jenkins/agent"
  nodeSelector:
    nodepool: "jenkins-node-pool"
    topology.kubernetes.io/zone: "ap-south-1a"
  restartPolicy: "Never"
  securityContext:
    fsGroup: 1000
    runAsGroup: 1000
    runAsUser: 1000
  tolerations:
  - effect: "NoSchedule"
    key: "jenkins"
    operator: "Equal"
    value: "true"
  volumes:
  - emptyDir:
      medium: ""
    name: "workspace-volume"
  - name: "maven-cache"
    persistentVolumeClaim:
      claimName: "maven-cache-pvc"
            """
        }
    }

    environment {
        // Use the EFS-mounted Maven cache; skip Javadoc in CI (run mvn javadoc:javadoc locally if needed).
        MAVEN_OPTS = "-Dmaven.repo.local=/cache/.m2/repository -Dmaven.javadoc.skip=true"

        SONAR_TOKEN = credentials('sonar-token')
        CHANNEL_ID = "${slackChannelId}"

        GIT_COMMITTER_NAME = 'RecruitCRM Engineering'
        GIT_AUTHOR_NAME = 'RecruitCRM Engineering'
        GIT_COMMITTER_EMAIL = 'automations-engineering@recruitcrm.io'
        GIT_AUTHOR_EMAIL = 'automations-engineering@recruitcrm.io'

        JAVA_PACKAGES_CODEARTIFACT_REPOSITORY_URL = 'https://recruitcrm-813287113117.d.codeartifact.ap-south-1.amazonaws.com/maven/java-packages/'
        AWS_CODEARTIFACT_REPOSITORY_USERNAME = 'aws'
        JAVA_PACKAGES_CODEARTIFACT_REPOSITORY_ID = 'java-packages'
        JAVA_PACKAGES_CODEARTIFACT_REPOSITORY_DOMAIN = 'recruitcrm'
        ARTIFACT_BUILD_ENVIRONMENT = 'production'
        AWS_ACCOUNT_ID = "813287113117"
        AWS_CODEARTIFACT_REGION = 'ap-south-1'
    }

    stages {
        stage('Prepare') {
            steps {
                script {
                    if (env.CHANGE_ID != null) {
                        env.CHECKOUT_BRANCH = env.CHANGE_BRANCH
                    } else {
                        env.CHECKOUT_BRANCH = env.BRANCH_NAME
                    }
                    withCredentials([usernamePassword(credentialsId: 'github-credentials-recruitcrm-engineering', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_TOKEN')]) {
                        sh("""
                        git config --global credential.helper 'store --file=.git/credentials'
                        echo "https://${symbol_dollar}GIT_USERNAME:${symbol_dollar}GIT_TOKEN@github.com" > .git/credentials
                        git fetch origin +refs/heads/*:refs/remotes/origin/*
                    """)
                    }
                }
            }
        }
        stage('Get CodeArtifact Auth Token') {
            steps {
                script {
                    env.CODEARTIFACT_AUTH_TOKEN = sh(
                            script: """
                        aws codeartifact get-authorization-token \
                            --domain ${symbol_dollar}{env.JAVA_PACKAGES_CODEARTIFACT_REPOSITORY_DOMAIN} \
                            --domain-owner ${symbol_dollar}{env.AWS_ACCOUNT_ID} \
                            --region ${symbol_dollar}{env.AWS_CODEARTIFACT_REGION} \
                            --query authorizationToken \
                            --output text
                        """,
                            returnStdout: true
                    ).trim()
                }
            }
        }
        stage('Code Quality Checks') {
            steps {
                sh "./mvnw -version"
                sh "./mvnw -s settings.xml \
                        --batch-mode \
                        -T 2C \
                        clean \
                        spotless:check \
                        checkstyle:check \
                        -Dsentry.maven.plugin.skip=true"
            }
        }
        stage('Execute Tests') {
            steps {
                sh "./mvnw -version"
                sh "./mvnw -s settings.xml \
                        --batch-mode \
                        -T 2C \
                        test \
                        surefire-report:report-only \
                        jacoco:report \
                        -Dsentry.maven.plugin.skip=true \
                        -Dmaven.test.failure.ignore=true \
                        -Dcheckstyle.skip=true \
                        -Dspotless.skip=true"
            }
        }
        stage('Publish Test Results') {
            steps {
                script {
                    junit '**/target/surefire-reports/TEST-*.xml'

                    def testResult = currentBuild.result ?: 'SUCCESS'
                    echo "Test result is: ${symbol_dollar}{testResult}"
                    env.TEST_RESULT_STATUS = testResult
                }
            }
            post {
                success {
                    script {
                        def buildUrl = env.BUILD_URL.replaceAll("http://jenkins-ci:8080", "https://jenkins.recruitcrm.net")
                        slackSend(
                                channel: "${symbol_dollar}{CHANNEL_ID}",
                                color: "good",
                                message: "JUnit tests passed! See the test report at ${symbol_dollar}{buildUrl}"
                        )
                    }
                }
                failure {
                    script {
                        def buildUrl = env.BUILD_URL.replaceAll("http://jenkins-ci:8080", "https://jenkins.recruitcrm.net")
                        slackSend(
                                channel: "${symbol_dollar}{CHANNEL_ID}",
                                color: "danger",
                                message: "JUnit tests failed. See the test report at ${symbol_dollar}{buildUrl}"
                        )
                    }
                }
                unstable {
                    script {
                        def buildUrl = env.BUILD_URL.replaceAll("http://jenkins-ci:8080", "https://jenkins.recruitcrm.net")
                        slackSend(
                                channel: "${symbol_dollar}{CHANNEL_ID}",
                                color: "warning",
                                message: "Some JUnit tests failed. See the test report at ${symbol_dollar}{buildUrl}"
                        )
                    }
                }
            }
        }
        stage('PR Analysis') {
            when {
                expression {
                    if (env.CHANGE_ID != null) {
                        def validChangeTarget = ["main", "main-next", "dev", "dev-next", "cse-bug-release"].contains(env.CHANGE_TARGET)
                        def validBaseBranchPrefixes = ['feature-', 'bugfix-', 'bugfix-cse', 'bug-hotfix-', 'enhancement-', 'refactor-', 'dev-next', 'main-next']
                        def validChangeBranch = validBaseBranchPrefixes.any { env.CHANGE_BRANCH.startsWith(it) }
                        return validChangeTarget && validChangeBranch
                    }
                    return false
                }
            }
            steps {
                script {
                    def pullRequestId = env.CHANGE_ID
                    def pullRequestBranch = env.CHANGE_BRANCH
                    def baseBranch = env.CHANGE_TARGET
                    withSonarQubeEnv('default_env') {
                        sh "./mvnw -s settings.xml \
                                --batch-mode \
                                -T 2C \
                                sonar:sonar \
                                -Dsonar.pullrequest.key=${symbol_dollar}{pullRequestId} \
                                -Dsonar.pullrequest.branch=${symbol_dollar}{pullRequestBranch} \
                                -Dsonar.pullrequest.base=${symbol_dollar}{baseBranch} \
                                -Dmaven.test.skip=true \
                                -Dsentry.maven.plugin.skip=true \
                                -Dcheckstyle.skip=true \
                                -Dspotless.skip=true \
                                -Djacoco.skip=true"
                    }
                }
            }
        }
        stage('Branch Analysis') {
            when {
                expression {
                    def validPrefixes = ['feature-', 'bugfix-', 'bugfix-cse', 'bug-hotfix-', 'enhancement-', 'refactor-', 'dev-next', 'main-next']
                    def validBranches = ['main', 'dev', 'cse-bug-release']
                    def validBranch = validPrefixes.any { env.BRANCH_NAME.startsWith(it) } || validBranches.contains(env.BRANCH_NAME)
                    return validBranch && env.CHANGE_ID == null
                }
            }
            steps {
                script {
                    def currentBranch = env.BRANCH_NAME
                    def targetBranch = 'dev'
                    if (currentBranch.startsWith('bugfix-cse')) {
                        targetBranch = 'cse-bug-release'
                    } else if (currentBranch.startsWith('bug-hotfix') || currentBranch.startsWith('main-next')) {
                        targetBranch = 'main'
                    }
                    if (currentBranch == 'main') {
                        withSonarQubeEnv('default_env') {
                            sh "./mvnw -s settings.xml \
                                --batch-mode \
                                -T 2C \
                                sonar:sonar \
                                -Dsonar.branch.name=${symbol_dollar}{currentBranch} \
                                -Dmaven.test.skip=true \
                                -Dsentry.maven.plugin.skip=true \
                                -Dcheckstyle.skip=true \
                                -Dspotless.skip=true \
                                -Djacoco.skip=true"
                        }
                    } else {
                        withSonarQubeEnv('default_env') {
                            sh "./mvnw -s settings.xml \
                                --batch-mode \
                                -T 2C \
                                sonar:sonar \
                                -Dsonar.branch.name=${symbol_dollar}{currentBranch} \
                                -Dsonar.branch.target=${symbol_dollar}{targetBranch} \
                                -Dmaven.test.skip=true \
                                -Dsentry.maven.plugin.skip=true \
                                -Dcheckstyle.skip=true \
                                -Dspotless.skip=true \
                                -Djacoco.skip=true"
                        }
                    }
                }
            }
        }
        stage('Send Test Report') {
            steps {
                script {
                    env.COMMIT_MESSAGE = sh(script: "git log -1 --pretty=%B", returnStdout: true).trim()
                    env.COMMIT_DIGEST = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    echo "Commit message: ${symbol_dollar}{env.COMMIT_MESSAGE}"
                    echo "Commit digest: ${symbol_dollar}{env.COMMIT_DIGEST}"
                }

                sh "zip -r scan.zip target/site/"
                slackUploadFile(
                        filePath: "scan.zip",
                        credentialId: "slack-bot-token",
                        channel: "${symbol_dollar}{CHANNEL_ID}",
                        initialComment: """
*REPOSITORY_NAME:* ${artifactId},
*BRANCH_NAME:* ${symbol_dollar}{env.CHECKOUT_BRANCH},
*COMMIT_URL:* ${repoUrl}/commit/${symbol_dollar}{env.COMMIT_DIGEST},
*COMMIT_MESSAGE:* ${symbol_dollar}{env.COMMIT_MESSAGE}
"""
                )
            }
        }
        stage('Semantic Versioning') {
            steps {
                lock("${artifactId}-${symbol_dollar}{env.CHECKOUT_BRANCH}") {
                    script {
                        withCredentials([usernamePassword(credentialsId: 'github-credentials-recruitcrm-engineering', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_TOKEN')]) {
                            sh "npm i"
                            sh "GITHUB_TOKEN=${symbol_dollar}GIT_TOKEN npx semantic-release --debug"
                        }
                    }
                }
            }
            post {
                failure {
                    echo "Build failed."
                }
                success {
                    echo "Build succeeded."
                }
            }
        }
    }
}
