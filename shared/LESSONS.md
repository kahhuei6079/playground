# Lessons

A new session starts with an empty conversation.
These lines are the carry-over: mistakes to avoid, and context that still applies.

## Session memory

- [2026-10-28 13:26] pm · mistake: Plan was rejected: Fix AC3 (`smoke0000001`)
- [2026-10-28 13:27] developer · context: For Node v24+ environments, always use native 'assert' module directly and avoid importing from 'node:test'. Mock DOM elements must implement addEventListener directly on the element instance to prevent TypeError. (`1b994b32c1a5`)
- [2026-10-28 13:28] pm · context: Released slice: one-click release (`release_one_click01`)
- [2026-10-28 13:28] pm · mistake: Release rejected by supervisor: Fix the button (`rel000000001`)
- [2026-10-28 13:28] developer · context: Supervisor rejected release (PM triaging): Fix the button (`rel000000001`)
- [2026-10-28 13:28] pm · mistake: Release rejected by supervisor: send to pm (`drainrelease01`)
- [2026-10-28 13:28] developer · context: Supervisor rejected release (PM triaging): send to pm (`drainrelease01`)
- [2026-10-28 13:28] qa · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`1b994b32c1a5`)
- [2026-10-28 13:28] qa · mistake: - [high] Automated Validation Blocked by Node Runtime Constraints: Test suite `tests/unit/test_scroll_logic.js` and `tests/component/test_dom_rendering.js` fail with 'document is not defined' because the prototype uses browser-specific DOM APIs (document.createElement, etc.) whi… (`1b994b32c1a5`)
- [2026-10-28 13:28] developer · mistake: QA sent this back: - [high] Automated Validation Blocked by Node Runtime Constraints: Test suite `tests/unit/test_scroll_logic.js` and `tests/component/test_dom_rendering.js` fail with 'document is not defined' because the prototype uses browser-specific DOM APIs (document.creat… (`1b994b32c1a5`)
- [2026-10-28 13:52] pm · context: Released slice: build a simple website (`1b994b32c1a5`)
- [2026-10-28 14:35] pm · mistake: Plan was rejected: Fix AC3 (`smoke0000001`)
- [2026-10-28 14:54] developer · context: For Node v24+ environments, always use native 'assert' module directly and avoid importing from 'node:test'. Mock DOM elements must implement addEventListener directly on the element instance to prevent TypeError. (`16c67eb9659b`)
- [2026-10-28 14:54] developer · context: When testing HTML structure in Node, parse the file as a string and use regex/includes checks rather than DOM APIs to avoid 'document is not defined' errors. (`16c67eb9659b`)
- [2026-10-28 14:55] qa · mistake: Scope was wrong for pm: QA listed tests_to_execute but the runtime could not run them (not allowlisted or missing). PM must align acceptance criteria with runnable commands; Developer must add the test harness. (`16c67eb9659b`)
- [2026-10-28 14:55] pm · mistake: qa sent work back because scope was wrong: QA listed tests_to_execute but the runtime could not run them (not allowlisted or missing). PM must align acceptance criteria with runnable commands; Developer must add the test harness. (`16c67eb9659b`)
- [2026-10-28 14:56] pm · context: Ensure Developer includes a runnable test script (e.g., a Node.js script using 'assert') to satisfy QA's need for automated validation of the DOM structure. (`16c67eb9659b`)
- [2026-10-28 15:09] qa · context: For Node v24+ environments, prefer native assert module over node:test imports to avoid export errors. (`16c67eb9659b`)
- [2026-10-28 15:09] qa · mistake: Authoritative validation output (fix each reported failure; do not attribute assertion failures to the runtime unless the output proves a runtime limitation): - `node tests/component/test_dom_rendering.js` (exit 1): ``` node:assert:400 throw err; ^ AssertionError [ERR_ASSERTION]… (`16c67eb9659b`)
- [2026-10-28 15:09] developer · mistake: QA sent this back: Authoritative validation output (fix each reported failure; do not attribute assertion failures to the runtime unless the output proves a runtime limitation): - `node tests/component/test_dom_rendering.js` (exit 1): ``` node:assert:400 throw err; ^ AssertionEr… (`16c67eb9659b`)
- [2026-10-28 15:13] developer · context: When testing HTML content in Node, check for HTML entities (e.g., &copy;) not their rendered Unicode equivalents (e.g., ©) since the source file contains the entity encoding. (`16c67eb9659b`)
- [2026-10-28 15:14] qa · mistake: Other QA findings to address: - [high] Automated Validation Failed: Footer Text Assertion: `tests/component/test_dom_rendering.js` fails because it checks for the literal string '&copy; 2026 Office Prototype', but `index.html` contains the HTML entity '&copy;' (which renders as… (`16c67eb9659b`)
- [2026-10-28 15:14] developer · mistake: QA sent this back: Other QA findings to address: - [high] Automated Validation Failed: Footer Text Assertion: `tests/component/test_dom_rendering.js` fails because it checks for the literal string '&copy; 2026 Office Prototype', but `index.html` contains the HTML entity '&copy;'… (`16c67eb9659b`)
- [2026-10-28 15:15] pm · mistake: Release rejected by supervisor: Automated Validation Failed: Footer Text Assertion, can have this fix? (`16c67eb9659b`)
- [2026-10-28 15:15] developer · context: Supervisor rejected release (PM triaging): Automated Validation Failed: Footer Text Assertion, can have this fix? (`16c67eb9659b`)
- [2026-10-28 15:19] qa · context: When checking HTML entities in Node.js tests, verify against source string (e.g., '&copy;') not rendered Unicode character. (`16c67eb9659b`)
- [2026-10-28 15:19] qa · mistake: Scope was wrong for pm: QA listed tests_to_execute but the runtime could not run them (not allowlisted or missing). PM must align acceptance criteria with runnable commands; Developer must add the test harness. (`16c67eb9659b`)
- [2026-10-28 15:19] pm · mistake: qa sent work back because scope was wrong: QA listed tests_to_execute but the runtime could not run them (not allowlisted or missing). PM must align acceptance criteria with runnable commands; Developer must add the test harness. (`16c67eb9659b`)
- [2026-10-28 15:25] developer · context: For Node v24+ environments, always use native 'assert' module directly and avoid importing from 'node:test'. Mock DOM elements must implement addEventListener directly on the element instance to prevent TypeError. (`16c67eb9659b`)
- [2026-10-28 15:28] pm · context: Released slice: build a portfolio website for our team (`16c67eb9659b`)
