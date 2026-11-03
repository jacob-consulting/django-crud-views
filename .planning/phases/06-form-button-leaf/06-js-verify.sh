#!/usr/bin/env bash
# Phase 06 JS verification entry point (M-NODE-COMMANDS / H-NODE).
#
#   bash .planning/phases/06-form-button-leaf/06-js-verify.sh [test paths...]
#
# Every invocation loads 06-JS-RUNTIME.json, requires its absolute Node / npm-cli.js paths, prepends the selected
# Node directory to PATH (so npm child scripts such as `vitest run` use the same Node in any fresh shell), and,
# using that Node, asserts process.execPath / version, the npm identity, the unchanged package-lock.json hash, every
# installed package's name / version against its lock entry, and every locked Node engine range (with npm's own
# bundled semver; no extra package is installed). Only then does it run `npm --prefix . test`, forwarding the given
# test paths after `--`; no paths runs the full suite. A missing record or runtime, engine mismatch, lock drift,
# package mismatch or test failure exits nonzero. This is a validation artifact, not a product change.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd -P)
RECORD="$SCRIPT_DIR/06-JS-RUNTIME.json"

fail() {
  echo "06-js-verify: FAIL: $*" >&2
  exit 1
}

[ -f "$RECORD" ] && [ -r "$RECORD" ] || fail "runtime record missing or unreadable: $RECORD"
command -v python3 >/dev/null 2>&1 || fail "python3 is required to read the runtime record"

# Read the two paths with a JSON parser (never eval); reject empty, relative or multi-line values.
FIELDS=$(
  python3 -I -c '
import json, sys

record = json.load(open(sys.argv[1], encoding="utf-8"))
values = [record["node"]["path"], record["npm"]["cli"]]
for value in values:
    if not isinstance(value, str) or not value.startswith("/") or "\n" in value:
        sys.exit("malformed runtime record path: %r" % (value,))
print("\n".join(values))
' "$RECORD"
) || fail "could not read node.path / npm.cli from $RECORD"
{
  IFS= read -r NODE_BIN
  IFS= read -r NPM_CLI
} <<<"$FIELDS"

[ -f "$NODE_BIN" ] && [ -x "$NODE_BIN" ] || fail "recorded Node is not an executable file: $NODE_BIN"
[ -f "$NPM_CLI" ] && [ -r "$NPM_CLI" ] || fail "recorded npm-cli.js is not a readable file: $NPM_CLI"

PATH="$(dirname -- "$NODE_BIN"):$PATH"
export PATH

"$NODE_BIN" - "$RECORD" "$REPO_ROOT" <<'JS' || fail "runtime / lock verification failed (see above)"
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const [recordPath, root] = process.argv.slice(2);
const record = JSON.parse(fs.readFileSync(recordPath, "utf8"));
const errors = [];

const realExec = fs.realpathSync(process.execPath);
const realNode = fs.realpathSync(record.node.path);
if (realExec !== realNode) errors.push(`process.execPath ${realExec} is not the recorded Node ${realNode}`);
if (process.version !== record.node.version) {
  errors.push(`Node version ${process.version} is not the recorded ${record.node.version}`);
}

const npmRoot = path.resolve(path.dirname(record.npm.cli), "..");
const npmPkg = JSON.parse(fs.readFileSync(path.join(npmRoot, "package.json"), "utf8"));
if (npmPkg.name !== "npm" || npmPkg.version !== record.npm.version) {
  errors.push(`npm at ${npmRoot} is ${npmPkg.name}@${npmPkg.version}, recorded npm@${record.npm.version}`);
}
// npm's already-bundled semver resolver: no new package is installed for this check
const semver = require(path.join(npmRoot, "node_modules", "semver"));

const lockPath = path.join(root, record.lockfile.path);
const lockBuf = fs.readFileSync(lockPath);
const sha = crypto.createHash("sha256").update(lockBuf).digest("hex");
if (sha !== record.lockfile.sha256) errors.push(`lock drift: ${record.lockfile.path} sha256 ${sha} != ${record.lockfile.sha256}`);
const lock = JSON.parse(lockBuf);

// npm skips an optional package whose os / cpu / libc constraint excludes this host
const header = process.report && process.report.getReport ? process.report.getReport().header : {};
const libc = process.platform === "linux" ? (header.glibcVersionRuntime ? "glibc" : "musl") : null;
let verified = 0;
let engines = 0;
const skipped = [];
for (const [key, entry] of Object.entries(lock.packages || {})) {
  const range = entry.engines && entry.engines.node;
  if (range) {
    engines++;
    if (!semver.satisfies(process.version, range)) errors.push(`engine mismatch: ${key || "<root>"} requires node ${range}`);
  }
  if (key === "") continue;
  const manifest = path.join(root, key, "package.json");
  if (!fs.existsSync(manifest)) {
    const otherOs = Array.isArray(entry.os) && !entry.os.includes(process.platform);
    const otherCpu = Array.isArray(entry.cpu) && !entry.cpu.includes(process.arch);
    const otherLibc = Array.isArray(entry.libc) && (libc === null || !entry.libc.includes(libc));
    if (entry.optional && (otherOs || otherCpu || otherLibc)) {
      skipped.push(key);
      continue;
    }
    errors.push(`missing installed package ${key}`);
    continue;
  }
  const installed = JSON.parse(fs.readFileSync(manifest, "utf8"));
  const expectedName = entry.name || key.slice(key.lastIndexOf("node_modules/") + "node_modules/".length);
  if (installed.name !== expectedName) errors.push(`package identity: ${key} is ${installed.name}, lock says ${expectedName}`);
  if (installed.version !== entry.version) {
    errors.push(`package version: ${key} is ${installed.version}, lock says ${entry.version}`);
  }
  verified++;
}

for (const [name, version] of Object.entries(record.packages || {})) {
  const entry = (lock.packages || {})[`node_modules/${name}`];
  if (!entry || entry.version !== version) errors.push(`recorded ${name}@${version} is not the locked version`);
}

const top = Object.entries(record.packages || {}).map(([n, v]) => `${n}@${v}`).join(" ");
console.log(
  `06-js-verify: node ${process.version} (${realExec}); npm ${npmPkg.version} (${record.npm.cli}); ` +
    `lock sha256 ${sha}; ${verified} installed packages match the lock, ${engines} engine ranges satisfied` +
    `; ${skipped.length} optional packages for other platforms skipped` +
    `; ${top}`,
);
if (errors.length) {
  for (const error of errors) console.error(`06-js-verify: ${error}`);
  process.exit(1);
}
JS

cd -- "$REPO_ROOT"
if [ "$#" -gt 0 ]; then
  exec "$NODE_BIN" "$NPM_CLI" --prefix . test -- "$@"
fi
exec "$NODE_BIN" "$NPM_CLI" --prefix . test
