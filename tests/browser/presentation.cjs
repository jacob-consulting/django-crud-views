// Dedicated real-browser acceptance. Port rejection precedes runtime discovery.
const portText = process.env.CV_PRESENTATION_PORT ?? '8145';
const port = Number(portText);
if (!/^[0-9]+$/.test(portText) || port < 1024 || port > 65535) {
    console.error('CV_PRESENTATION_PORT must be decimal 1024..65535; reserved ports: 8143, 8144');
    process.exit(1);
}
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
process.chdir(root);
const node = process.env.CV_FOCUS_NODE ?? process.execPath;
assert(fs.existsSync(node), `Missing CV_FOCUS_NODE: ${node}`);
if (fs.realpathSync(node) !== fs.realpathSync(process.execPath)) {
    const result = cp.spawnSync(node, [__filename, ...process.argv.slice(2)], {stdio: 'inherit'});
    process.exit(result.status ?? 1);
}
