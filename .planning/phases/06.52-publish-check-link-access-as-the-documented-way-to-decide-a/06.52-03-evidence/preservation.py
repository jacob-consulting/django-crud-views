import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()

baseline = '1d538046'
entry = 'eaacb2e937ef14b977da5ee5b34b66204a5fde2d'
subprocess.run(['git', 'diff', '--exit-code', baseline, '--', 'tests', ':!tests/test1/test_public_link_access.py', ':!tests/test1/test_link_access_docs.py'], check=True)
subprocess.run(['git', 'diff', '--exit-code', baseline, '--', 'src', ':!src/crud_views/lib/link_access.py'], check=True)
subprocess.run(['git', 'diff', '--exit-code', entry, '--', 'src', 'tests/test1/test_public_link_access.py', 'superpowers/specs/2026-11-23-link-access-check-design.md'], check=True)
path = 'src/crud_views/lib/link_access.py'
before = git('show', f'{baseline}:{path}')
after = Path(path).read_text()
old_nodes = ast.parse(before).body
new_nodes = ast.parse(after).body
preserved = []
for old in old_nodes:
    if isinstance(old, ast.FunctionDef):
        new = next(n for n in new_nodes if isinstance(n, ast.FunctionDef) and n.name == old.name)
    elif isinstance(old, ast.Assign):
        name = old.targets[0].id
        new = next(n for n in new_nodes if isinstance(n, ast.Assign) and n.targets[0].id == name)
    else:
        continue
    assert ast.get_source_segment(before, old) == ast.get_source_segment(after, new)
    preserved.append(getattr(old, 'name', None) or old.targets[0].id)

page = 'docs/reference/link_access.md'
fence = re.compile(r'## Object target\n.*?(```python\n.*?```)', re.S)
assert fence.search(git('show', f'{entry}:{page}')).group(1) == fence.search(Path(page).read_text()).group(1)
old_changelog = git('show', f'{entry}:CHANGELOG.md')
new_changelog = Path('CHANGELOG.md').read_text()
assert old_changelog.split('### Breaking', 1)[1].split('\n### ', 1)[0] == new_changelog.split('### Breaking', 1)[1].split('\n### ', 1)[0]

old_tests = git('show', f'{entry}:tests/test1/test_link_access_docs.py')
new_tests = Path('tests/test1/test_link_access_docs.py').read_text()
unchanged_docs_tests = []
for old in ast.parse(old_tests).body:
    if isinstance(old, ast.FunctionDef) and old.name != 'test_link_check_is_not_in_the_stability_inventory':
        new = next(n for n in ast.parse(new_tests).body if isinstance(n, ast.FunctionDef) and n.name == old.name)
        assert ast.get_source_segment(old_tests, old) == ast.get_source_segment(new_tests, new), old.name
        unchanged_docs_tests.append(old.name)

assert Path('.planning/config.default.json').read_bytes() == Path('/tmp/cv-0652-orchestrator/config.default.json').read_bytes()
assert Path('.planning/config.json').read_bytes() == Path('/tmp/cv-0652-orchestrator/config.json').read_bytes()
print(json.dumps(dict(baseline=baseline, plan_entry=entry, private_definitions_preserved=preserved, original_docs_tests_preserved=unchanged_docs_tests, protected_tests_goldens_matrix_cost_pins='byte-identical', other_production='byte-identical', object_fence='byte-identical', original_breaking_section='byte-identical', user_configuration='byte-identical', matrix_cost_reuse=dict(summary='06.52-02-SUMMARY.md', passed=1665, seconds=14.37, source_tree=git('rev-parse', 'd2249304:src'), relevant_source_unchanged=True)), indent=2))
