opencode review failed or returned empty output. stderr:
[93m[1m! [0mpermission requested: external_directory (/home/alex/projects/alex/tabler-test/*); auto-rejecting

Raw response body:
OpenCode review returned no assistant text (#1936: agent ended its turn with no final message).
Diagnostic: stop reason=tool-calls, output tokens=304
Diagnosis: opencode ran at effort=high and exited cleanly inside the timeout — a clean exit that produced no output is most often a model ending its turn without writing a final message rather than a crash; if this lane carries a reasoning effort, raising it is the usual fix.
