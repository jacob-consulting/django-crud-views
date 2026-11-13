# Deferred observations

- The Python 3.12.3 / Django 4.2.30 compatibility selection passed 1,589 tests but emitted 12
  `ExceptionCycleWarning` messages from Django's `views/debug.py:487`, triggered by the unchanged
  `tests/test1/test_workflow_review.py` dependent-refusal exception-chain cases. This phase does not modify
  those tests or workflow execution. No fix attempted; these warnings are outside this presentation change.
