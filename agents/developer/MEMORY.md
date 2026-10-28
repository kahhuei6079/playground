# Developer Memory

## Verified technical notes
- Prototypes should be self-contained in the thread workspace so QA can review them without extra setup.

## Lessons learned
- Record confirmed root causes and fixes here after approved releases.

## Related files
- Add focused notes (for example `memory/web.md`) when this file would otherwise grow too large.

## Session memory

- [2026-10-25 04:21] developer · context: Supervisor rejected release (PM triaging): PM fix AC (`livegate01`)
- [2026-10-25 04:25] developer · context: Supervisor rejected release (PM triaging): send to pm (`drainrelease01`)
- [2026-10-25 04:25] developer · context: Supervisor rejected release (PM triaging): Fix the button (`rel000000001`)
- [2026-10-25 05:34] developer · mistake: QA sent this back: - [medium] Automated Test Execution Blocked by Node.js Environment: Node v24+ runtime lacks native 'document' API. Tests using DOM APIs fail with 'document is not defined'. This is an environment constraint, not a product defect. Manual smoke tests confirm fun… (`8486d0325d01`)
- [2026-10-25 05:51] developer · context: Supervisor rejected release (PM triaging): validation run failed, can rerun? (`8486d0325d01`)
- [2026-10-25 06:07] developer · mistake: QA sent this back: - [high] Automated Test Execution Blocked by Node.js Environment Constraints: Test files `tests/unit/test_render_logic.js` and `tests/component/test_dom_rendering.js` fail due to missing 'document' API in Node v24+ runtime. Tests using DOM APIs (`document.crea… (`8486d0325d01`)
- [2026-10-25 06:09] developer · context: Supervisor rejected release (PM triaging): test failed (`8486d0325d01`)
- [2026-10-25 07:20] developer · mistake: QA sent this back: - [medium] Automated Test Execution Blocked by Node.js Environment Constraints: Test files `tests/unit/test_render_logic.js`, `tests/component/test_dom_rendering.js`, and `tests/contract/test_acceptance_criteria.js` use DOM APIs (`document.createElement`) whic… (`8486d0325d01`)
- [2026-10-25 13:43] developer · mistake: Scope was wrong for pm: The input 'test' lacks functional requirements, target platform, and acceptance criteria. Per the approved plan, no work can begin until the human clarifies these details. (`5e49b15c3f58`)
- [2026-10-25 13:47] developer · mistake: Scope was wrong for pm: The input 'test' lacks functional requirements, target platform, and acceptance criteria. Per the approved plan, no implementation can begin until the human answers the three clarifying questions listed in PLAN.md. (`5e49b15c3f58`)
- [2026-10-25 13:50] developer · mistake: QA sent this back: - [high] Validation gap: manual_only: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`5e49b15c3f58`)
- [2026-10-25 14:05] developer · mistake: QA sent this back: - [high] Validation failed: node tests/contract/test_acceptance_criteria.js: file:///Users/kahhuei/playground/workspace/b956a623435a/tests/contract/test_acceptance_criteria.js:142 assert.ok(!htmlContent.includes('<link href=') || htmlContent.includes('<!--'),… (`b956a623435a`)
- [2026-10-25 14:39] developer · mistake: QA sent this back: - [high] Test Suite Blocked by Syntax Error: `tests/contract/test_acceptance_criteria.js` line 142: `assert.ok(!htmlContent.includes('<link href=') || htmlContent.includes('<!--'), 'AC5: No external C…` is missing a closing parenthesis. This blocks automated v… (`b956a623435a`)
- [2026-10-25 14:39] developer · context: Supervisor rejected release (PM triaging): beed test all passed (`b956a623435a`)
- [2026-10-25 14:51] developer · context: For Node v24+ environments, always use native 'assert' module instead of importing from 'node:test' to avoid export errors. Mock DOM elements must implement addEventListener directly on the element instance. (`b956a623435a`)
- [2026-10-25 14:53] developer · mistake: QA sent this back: - [high] Component Test Suite Blocked by Mock DOM Implementation Error: `tests/component/test_dom_rendering.js` crashes with `TypeError: aboutLink.addEventListener is not a function`. The mock element created via `createElement` does not expose the `addEventLi… (`b956a623435a`)
- [2026-10-27 15:12] developer · mistake: QA sent this back: - [high] Validation gap: manual_only: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`1227fe2d7465`)
- [2026-10-28 12:49] developer · mistake: qa sent work back because scope was wrong: The implementation (CLI) does not match the plan (HTTP backend). The acceptance criteria explicitly require HTTP endpoints and status codes. Developer must either implement an HTTP server or update the plan to accept a CLI tool. (`15e5ca7f1670`)
- [2026-10-28 13:26] developer · mistake: QA sent this back: - [high] Automated Validation Blocked by Node Runtime Constraints: Test suite `test_dom_rendering.js` fails with 'document is not defined' because the prototype uses browser-specific DOM APIs (document.createElement, etc.) which are unavailable in Node v24+ wi… (`1b994b32c1a5`)
- [2026-10-28 13:27] developer · context: For Node v24+ environments, always use native 'assert' module directly and avoid importing from 'node:test'. Mock DOM elements must implement addEventListener directly on the element instance to prevent TypeError. (`1b994b32c1a5`)
- [2026-10-28 13:28] developer · context: Supervisor rejected release (PM triaging): Fix the button (`rel000000001`)
- [2026-10-28 13:28] developer · context: Supervisor rejected release (PM triaging): send to pm (`drainrelease01`)
- [2026-10-28 13:28] developer · mistake: QA sent this back: - [high] Automated Validation Blocked by Node Runtime Constraints: Test suite `tests/unit/test_scroll_logic.js` and `tests/component/test_dom_rendering.js` fail with 'document is not defined' because the prototype uses browser-specific DOM APIs (document.creat… (`1b994b32c1a5`)
- [2026-10-28 14:54] developer · context: For Node v24+ environments, always use native 'assert' module directly and avoid importing from 'node:test'. Mock DOM elements must implement addEventListener directly on the element instance to prevent TypeError. (`16c67eb9659b`)
- [2026-10-28 14:54] developer · context: When testing HTML structure in Node, parse the file as a string and use regex/includes checks rather than DOM APIs to avoid 'document is not defined' errors. (`16c67eb9659b`)
- [2026-10-28 15:09] developer · mistake: QA sent this back: Authoritative validation output (fix each reported failure; do not attribute assertion failures to the runtime unless the output proves a runtime limitation): - `node tests/component/test_dom_rendering.js` (exit 1): ``` node:assert:400 throw err; ^ AssertionEr… (`16c67eb9659b`)
- [2026-10-28 15:13] developer · context: When testing HTML content in Node, check for HTML entities (e.g., &copy;) not their rendered Unicode equivalents (e.g., ©) since the source file contains the entity encoding. (`16c67eb9659b`)
- [2026-10-28 15:14] developer · mistake: QA sent this back: Other QA findings to address: - [high] Automated Validation Failed: Footer Text Assertion: `tests/component/test_dom_rendering.js` fails because it checks for the literal string '&copy; 2026 Office Prototype', but `index.html` contains the HTML entity '&copy;'… (`16c67eb9659b`)
- [2026-10-28 15:15] developer · context: Supervisor rejected release (PM triaging): Automated Validation Failed: Footer Text Assertion, can have this fix? (`16c67eb9659b`)
- [2026-10-28 15:25] developer · context: For Node v24+ environments, always use native 'assert' module directly and avoid importing from 'node:test'. Mock DOM elements must implement addEventListener directly on the element instance to prevent TypeError. (`16c67eb9659b`)
