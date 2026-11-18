# Companion validator source evidence

Read-only GitHub contents API retrieval; no checkout or product edits.

Repository: jacob-consulting/skills
Path: scripts/validate.py
Blob SHA: aa3207740dd95efc3ce36497503229486169eb53

```python
22: REPO_ROOT = Path(__file__).resolve().parent.parent
23: MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
```

The validator derives its root from `__file__`, so running it from the product cwd does not validate the wrong tree. This refutes Grok plan07 cwd concern. Signature correctness remains outside intel adapter coverage.
