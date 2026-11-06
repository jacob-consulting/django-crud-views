'use strict';
const assert = require('node:assert/strict');
const {loadAssets, assetFor} = require('./cancel-navigation.cjs');

function requiredCases(selection) {
    assert(['smoke', 'all'].includes(selection));
    return ['native-first-page', 'required-recovery-page'];
}
function validateEvidence(report, selection) {
    for (const id of requiredCases(selection)) assert(report.cases.some(item => item.id === id && item.passed), `Missing case: ${id}`);
    assert.deepEqual(report.failures, []);
    assert(report.cleanup.stopped && report.cleanup.databaseRemoved, 'Owned cleanup incomplete');
}
module.exports = {requiredCases, validateEvidence, loadAssets, assetFor};
