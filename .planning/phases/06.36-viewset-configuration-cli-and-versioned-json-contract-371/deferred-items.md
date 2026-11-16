## Deferred Items

- Pydantic 2.2.1 command corpus blocked by pre-existing Resource subclass import failure.
  status: open
  **What:** `src/crud_views/lib/resource.py:89` reads `cls.__pydantic_fields__`, absent at the declared floor. The installed floor session proves Python 3.12.3 / Django 5.2.19 / Pydantic 2.2.1 / typing-extensions 4.16.0 and passes 51 report-model tests, but five modules produce 20 xdist collection errors. The actual command corpus is not emitted, so floor/published schema conformance at the floor is unresolved. This owner predates phase 06.36 (last modification 04f95c30); plan07 does not change it or raise the dependency floor. See `evidence/07-floor.log`.
  **Final replay:** Frozen source `4846f729` passes 57 report-model tests with the same 20 collection errors; 3.06s pytest, 7.874s outer command. Schema-only output succeeds, but the independent command-corpus checker fails for missing exports. See `evidence/07-execution.json`; the original 51-test receipt is retained above as historical evidence.
