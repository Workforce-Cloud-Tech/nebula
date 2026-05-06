#set( $symbol_dollar = '$' )
// release.config.js (ESM)
import envCi from 'env-ci';

const { branch, isPr } = envCi();
const isMain = branch === 'main' && !isPr;

export default {
    branches: [
        'main',
        { name: 'main-next', prerelease: true },
        { name: 'cse-bug-release', prerelease: true },
        { name: 'dev', prerelease: true },
        { name: 'dev-next', prerelease: true },
        { name: 'feature-*', prerelease: true },
        { name: 'enhancement-*', prerelease: true },
        { name: 'bugfix-*', prerelease: true },
        { name: 'bug-hotfix-*', prerelease: true },
        { name: 'bugfix-cse-*', prerelease: true },
        { name: 'refactor-*', prerelease: true },
    ],

    plugins: [
        '@semantic-release/commit-analyzer',

        [
            '@semantic-release/exec',
            {
                prepareCmd: 'mvn --batch-mode -T 2C versions:set -DnewVersion=${symbol_dollar}{nextRelease.version}',
                publishCmd:
                    'mvn -s settings.xml ' +
                    '--batch-mode ' +
                    '-T 2C ' +
                    '-Dmaven.test.skip=true ' +
                    '-Dsentry.maven.plugin.skip=true ' +
                    '-Dcheckstyle.skip=true ' +
                    '-Dspotless.skip=true ' +
                    '-Djacoco.skip=true ' +
                    'package deploy',
            },
        ],

        '@semantic-release/release-notes-generator',

        // Only create a GitHub Release on main
        isMain && [
            '@semantic-release/github',
            { releasedLabels: false },
        ],

        // Always commit pom.xml on every branch
        [
            '@semantic-release/git',
            { assets: ['pom.xml'] },
        ],
    ].filter(Boolean),
};
