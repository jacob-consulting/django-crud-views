// Read-only replay of the recovered classifier inputs; no product behavior is inferred.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const tool = '/home/alex/.codex/gsd-core/bin/lib/edge-probe.cjs';
const probe = require(tool);
const read = name => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8'));
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(hash(fs.readFileSync(tool)), hash(fs.readFileSync(path.join(__dirname, 'detector-source.txt'))));
const ids = ['DEL-01', 'DEL-03', 'DEL-04', 'AUTH-06'];
const rows = [];
for (const phase of ['phase62', 'phase63']) {
  const requirements = read(`${phase}-input.json`);
  const original = read(`${phase}-output.json`);
  assert.deepEqual(probe.analyzeCoverage(requirements), original, `${phase}: entire recovered output must reproduce`);
  for (const requirement of requirements.filter(x => ids.includes(x.id))) {
    assert.deepEqual(probe.classifyShape(requirement.text), []);
    const candidate = probe.proposeEdges(requirement);
    assert.equal(candidate.length, 1);
    assert.equal(candidate[0].category, 'unclassified');
    assert.equal(candidate[0].probe, 'unclassified — review manually');
    assert.equal(candidate[0].resolution, null);
    rows.push({ phase, requirement, matched_shapes: [], original_candidate: candidate[0] });
  }
}
assert.deepEqual(rows.filter(x => x.phase === 'phase63').map(x => x.requirement.id).sort(), [...ids].sort());
// A recognized cue produces a named probe; this distinguishes the fallback branch.
assert.ok(probe.proposeEdges({id:'control',text:'delete'}).every(x => x.category !== 'unclassified'));
const dismissals = read('resolutions.json');
assert.deepEqual(dismissals.map(x => x.requirement_id).sort(), [...ids].sort());
const final = probe.analyzeCoverage(read('phase63-input.json'), dismissals);
assert.equal(final.items.filter(x => ids.includes(x.requirement_id) && x.category === 'unclassified' && x.status === 'dismissed').length, 4);
console.log(JSON.stringify({ checked_at: new Date().toISOString(), detector_sha256: hash(fs.readFileSync(tool)), result: 'FOUR_FALLBACKS_REPRODUCED_AND_DISPOSITIONS_VALID', rows, dispositions: final.items.filter(x => ids.includes(x.requirement_id) && x.category === 'unclassified'), note: 'Other classifier categories and general Guardian precision are unchanged; this is not phase verification.' }, null, 2));
