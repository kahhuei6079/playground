# QA Memory

## Recurring checks
- Does the prototype exist as real files?
- Are acceptance criteria actually implemented?
- Are empty, error, and success states present if the spec required them?
- Are there obvious security issues (secrets, unsafe eval, unrestricted paths)?

## Lessons learned
- Record confirmed regression patterns here after approved releases.


## 2026-10-24

- Simple batch scripts using 'set -e' are effective for sequential execution but rely on the shell environment having 'set -o pipefail' disabled or commands not piping to avoid unexpected exits in some contexts. For this scope, current approach is acceptable.

## Session memory

- [2026-10-25 04:15] qa · mistake: - [high] Automated Test Execution Blocked by Node.js Environment Constraints: Test files `tests/unit/test_render_logic.js` and `tests/contract/test_acceptance_criteria.js` use DOM APIs (`document.createElement`) which are not available in the Node runtime without jsdom. This blo… (`8486d0325d01`)
- [2026-10-25 05:34] qa · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`8486d0325d01`)
- [2026-10-25 05:34] qa · context: DOM APIs (document.createElement, etc.) are not available in Node.js without jsdom. Tests relying on these must either run in a browser or use a mock DOM environment. (`8486d0325d01`)
- [2026-10-25 05:34] qa · mistake: - [medium] Automated Test Execution Blocked by Node.js Environment: Node v24+ runtime lacks native 'document' API. Tests using DOM APIs fail with 'document is not defined'. This is an environment constraint, not a product defect. Manual smoke tests confirm functionality. - [high… (`8486d0325d01`)
- [2026-10-25 06:07] qa · mistake: - [high] Automated Test Execution Blocked by Node.js Environment Constraints: Test files `tests/unit/test_render_logic.js` and `tests/component/test_dom_rendering.js` fail due to missing 'document' API in Node v24+ runtime. Tests using DOM APIs (`document.createElement`) are not… (`8486d0325d01`)
- [2026-10-25 07:20] qa · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`8486d0325d01`)
- [2026-10-25 07:20] qa · context: DOM APIs (document.createElement, etc.) are not available in Node.js without jsdom. Tests relying on these must either run in a browser or use a mock DOM environment. (`8486d0325d01`)
- [2026-10-25 07:20] qa · mistake: - [medium] Automated Test Execution Blocked by Node.js Environment Constraints: Test files `tests/unit/test_render_logic.js`, `tests/component/test_dom_rendering.js`, and `tests/contract/test_acceptance_criteria.js` use DOM APIs (`document.createElement`) which are not available… (`8486d0325d01`)
- [2026-10-25 13:46] qa · mistake: Scope was wrong for pm: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`5e49b15c3f58`)
- [2026-10-25 13:50] qa · mistake: - [high] Validation gap: manual_only: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`5e49b15c3f58`)
- [2026-10-25 14:05] qa · mistake: - [high] Validation failed: node tests/contract/test_acceptance_criteria.js: file:///Users/kahhuei/playground/workspace/b956a623435a/tests/contract/test_acceptance_criteria.js:142 assert.ok(!htmlContent.includes('<link href=') || htmlContent.includes('<!--'), 'AC5: No external C… (`b956a623435a`)
- [2026-10-25 14:10] qa · context: When creating mock DOM elements for Node.js tests, ensure `addEventListener` is implemented to prevent runtime TypeError. Use a proper jsdom setup or native assert-only logic where possible. (`b956a623435a`)
- [2026-10-25 14:10] qa · mistake: Scope was wrong for pm: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`b956a623435a`)
- [2026-10-25 14:39] qa · mistake: - [high] Test Suite Blocked by Syntax Error: `tests/contract/test_acceptance_criteria.js` line 142: `assert.ok(!htmlContent.includes('<link href=') || htmlContent.includes('<!--'), 'AC5: No external C…` is missing a closing parenthesis. This blocks automated validation of AC5. -… (`b956a623435a`)
- [2026-10-25 14:53] qa · context: When creating mock DOM elements for Node.js tests, ensure `addEventListener` is implemented directly on the element instance to prevent runtime TypeError. Use a proper jsdom setup or native assert-only logic where possible. (`b956a623435a`)
- [2026-10-25 14:53] qa · mistake: - [high] Component Test Suite Blocked by Mock DOM Implementation Error: `tests/component/test_dom_rendering.js` crashes with `TypeError: aboutLink.addEventListener is not a function`. The mock element created via `createElement` does not expose the `addEventListener` method, cau… (`b956a623435a`)
- [2026-10-27 15:01] qa · mistake: Scope was wrong for pm: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`1227fe2d7465`)
- [2026-10-27 15:12] qa · mistake: - [high] Validation gap: manual_only: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`1227fe2d7465`)
- [2026-10-28 12:49] qa · context: When plan specifies HTTP endpoints, implementation must be a web server (e.g., PHP built-in server), not a CLI script. Automated validation fails if the runtime cannot start the service. (`15e5ca7f1670`)
- [2026-10-28 12:49] qa · mistake: Scope was wrong for developer: The implementation (CLI) does not match the plan (HTTP backend). The acceptance criteria explicitly require HTTP endpoints and status codes. Developer must either implement an HTTP server or update the plan to accept a CLI tool. (`15e5ca7f1670`)
- [2026-10-28 13:26] qa · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`1b994b32c1a5`)
- [2026-10-28 13:26] qa · mistake: - [high] Automated Validation Blocked by Node Runtime Constraints: Test suite `test_dom_rendering.js` fails with 'document is not defined' because the prototype uses browser-specific DOM APIs (document.createElement, etc.) which are unavailable in Node v24+ without jsdom. This p… (`1b994b32c1a5`)
- [2026-10-28 13:28] qa · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`1b994b32c1a5`)
- [2026-10-28 13:28] qa · mistake: - [high] Automated Validation Blocked by Node Runtime Constraints: Test suite `tests/unit/test_scroll_logic.js` and `tests/component/test_dom_rendering.js` fail with 'document is not defined' because the prototype uses browser-specific DOM APIs (document.createElement, etc.) whi… (`1b994b32c1a5`)
- [2026-10-28 14:55] qa · mistake: Scope was wrong for pm: QA listed tests_to_execute but the runtime could not run them (not allowlisted or missing). PM must align acceptance criteria with runnable commands; Developer must add the test harness. (`16c67eb9659b`)
- [2026-10-28 15:09] qa · context: For Node v24+ environments, prefer native assert module over node:test imports to avoid export errors. (`16c67eb9659b`)
- [2026-10-28 15:09] qa · mistake: Authoritative validation output (fix each reported failure; do not attribute assertion failures to the runtime unless the output proves a runtime limitation): - `node tests/component/test_dom_rendering.js` (exit 1): ``` node:assert:400 throw err; ^ AssertionError [ERR_ASSERTION]… (`16c67eb9659b`)
- [2026-10-28 15:14] qa · mistake: Other QA findings to address: - [high] Automated Validation Failed: Footer Text Assertion: `tests/component/test_dom_rendering.js` fails because it checks for the literal string '&copy; 2026 Office Prototype', but `index.html` contains the HTML entity '&copy;' (which renders as… (`16c67eb9659b`)
- [2026-10-28 15:19] qa · context: When checking HTML entities in Node.js tests, verify against source string (e.g., '&copy;') not rendered Unicode character. (`16c67eb9659b`)
- [2026-10-28 15:19] qa · mistake: Scope was wrong for pm: QA listed tests_to_execute but the runtime could not run them (not allowlisted or missing). PM must align acceptance criteria with runnable commands; Developer must add the test harness. (`16c67eb9659b`)
