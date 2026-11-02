const {test} = require('node:test');
const assert = require('node:assert/strict');
const cp = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const root = path.resolve(__dirname, '../..');
const python = process.env.CV_FOCUS_PYTHON;
assert(python && fs.existsSync(python), 'Select an existing CV_FOCUS_PYTHON interpreter');
for (const [entry, command, args] of [
    ['node', process.execPath, ['tests/browser/presentation.cjs']],
    ['python', python, ['tests/browser/presentation_server.py']],
]) {
    for (const port of ['8143', '8144', '1023', '65536', '', 'no-port', '8145.5']) {
        test(`${entry} rejects port ${JSON.stringify(port)} before runtime discovery`, () => {
            const result = cp.spawnSync(command, args, {
                cwd: root, encoding: 'utf8', timeout: 4000, shell: false,
                env: {...process.env, CV_PRESENTATION_PORT: port, PYTHONPATH: `${root}/src:${root}`,
                    CV_FOCUS_NODE: '/nonexistent/node', CV_FOCUS_PLAYWRIGHT: '/nonexistent/playwright',
                    CV_FOCUS_CHROMIUM: '/nonexistent/chromium'},
            });
            assert.ifError(result.error);
            assert.notEqual(result.status, 0);
            assert.match(result.stderr + result.stdout, /CV_PRESENTATION_PORT.*1024\.\.65535.*8143.*8144/);
            assert.doesNotMatch(result.stdout, /"ready"/);
        });
    }
}
