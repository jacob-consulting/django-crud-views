# Node configuration reporter

The first final `--check-final` composition stopped at `nonpassing fresh-shell configuration` because
Node 24's default reporter emitted `ℹ pass 21` / `ℹ fail 0`, while the checker requires TAP `# pass` / `# fail`.
The test process itself exited 0 with all 21 cases passing. Its unmodified command and output remain in the
final report's gate history. No test result was relabeled and no checker/source predicate was weakened.

The configuration command was rerun with the same argv and explicit `NODE_OPTIONS=--test-reporter=tap`.
That option is accepted by the existing Node runtime and selects its built-in reporter; no install or
tracked source/runtime package change was required. The rerun's complete TAP output is the authoritative
configuration gate. Other source-identical passing gates were not rerun for this reporting-only adjustment.
