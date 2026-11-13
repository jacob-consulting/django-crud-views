// Startup protocol regressions: importing the helper must not start Django or Chromium.
const assert = require('node:assert/strict');
const {EventEmitter} = require('node:events');
const {PassThrough} = require('node:stream');
const {test} = require('node:test');
const {waitForReady} = require('./formset-row-cards.cjs');

test('compact styles distinguish borders from complete suppression', () => {
    const {validateCompactStyle} = require('./formset-row-cards.cjs');
    assert.equal(typeof validateCompactStyle, 'function');
    const style = {borders: Array(4).fill('1px'), padding: Array(4).fill('8px'),
        radius: '4px', background: 'rgb(255, 255, 255)', margins: Array(4).fill('0px'),
        compact: true, bordered: true, plain: false, cards: 0, legends: 0};
    validateCompactStyle(style, 'bordered');
    validateCompactStyle({...style, borders: Array(4).fill('0px'), bordered: false}, 'borderless');
    validateCompactStyle({...style, borders: Array(4).fill('0px'), padding: Array(4).fill('0px'),
        radius: '0px', background: 'rgba(0, 0, 0, 0)', bordered: false, plain: true}, 'plain');
    for (let side = 0; side < 4; side++) {
        const borders = [...style.borders]; borders[side] = '0px';
        assert.throws(() => validateCompactStyle({...style, borders}, 'bordered'));
        const padding = [...style.padding]; padding[side] = '0px';
        assert.throws(() => validateCompactStyle({...style, padding}, 'bordered'));
    }
    for (const change of [{plain: true}, {bordered: false}, {cards: 1}, {legends: 1},
        {background: 'rgba(0, 0, 0, 0)'}, {radius: '0px'}, {compact: false}]) {
        assert.throws(() => validateCompactStyle({...style, ...change}, 'bordered'));
    }
    assert.throws(() => validateCompactStyle(style, 'borderless'));
    assert.throws(() => validateCompactStyle(style, 'plain'));
});

function host() {
    const child = new EventEmitter();
    child.stdout = new PassThrough();
    return child;
}

test('buffers split readiness records until the terminating newline', async () => {
    const child = host();
    const ready = waitForReady(child, () => '', 1000);
    ready.catch(() => {});
    let settled = false;
    ready.then(() => {settled = true;}, () => {settled = true;});
    for (const part of ['migration log\n{"po', 'rt": 8123, "login": "/lo', 'gin/"}']) {
        assert.doesNotThrow(() => child.stdout.write(part));
        await Promise.resolve();
        assert.equal(settled, false, 'partial record must not settle readiness');
    }
    child.stdout.write('\ntrailing log\n');
    assert.deepEqual(await ready, {port: 8123, login: '/login/'});
    assert.equal(child.stdout.listenerCount('data'), 0);
});

test('malformed complete records reject readiness and reach caller finally cleanup', async () => {
    const child = host();
    let cleaned = false;
    const operation = (async () => {
        try {await waitForReady(child, () => '', 1000);}
        finally {cleaned = true;}
    })();
    operation.catch(() => {});
    assert.doesNotThrow(() => child.stdout.write('{"port": invalid}\n'));
    await assert.rejects(operation, SyntaxError);
    assert.equal(cleaned, true);
    assert.equal(child.stdout.listenerCount('data'), 0);
    assert.equal(child.listenerCount('exit'), 0);
});

test('an unterminated record followed by host exit is a startup failure', async () => {
    const child = host();
    const ready = waitForReady(child, () => 'host stopped', 1000);
    ready.catch(() => {});
    child.stdout.write('{"port": 8123}');
    child.emit('exit', 2);
    await assert.rejects(ready, /Host exited 2: host stopped/);
});
