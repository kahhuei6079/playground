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

- [2026-10-24 15:46] qa · context: When validating row counts in CSV metadata tools, remember that row_count = total_rows - 1 (excluding header). Test assertions must reflect this. (`960b759c82d2`)
- [2026-10-24 15:46] qa · mistake: - [high] Test script assertion mismatch on happy path: test_happy_path() asserts 'Rows: 2' but CLI correctly outputs 'Rows: 3' for a CSV with 3 data rows. This is a test logic error that blocks validation. - [high] Validation failed: python -m pytest -q: /Users/kahhuei/playgroun… (`960b759c82d2`)
- [2026-10-24 16:31] qa · mistake: - [high] Validation failed: node tests/unit/test_theme_logic.js: file:///Users/kahhuei/playground/workspace/c1a81a1794bb/tests/unit/test_theme_logic.js:17 describe('Theme Logic', () => { ^ ReferenceError: describe is not defined at file:///Users/kahhuei/playground/workspace/c1a8… (`c1a81a1794bb`)
- [2026-10-25 02:26] qa · mistake: - [high] Validation failed: node tests/unit/test_render_logic.js: file:///Users/kahhuei/playground/workspace/8486d0325d01/tests/unit/test_render_logic.js:1 import { describe, it, expect } from 'node:test'; ^^^^^^ SyntaxError: The requested module 'node:test' does not provide an… (`8486d0325d01`)
- [2026-10-25 02:33] qa · context: For Node.js test suites targeting browser APIs, avoid importing 'expect' from 'node:test'; use native 'assert' module instead to prevent export errors in Node v24+. (`8486d0325d01`)
- [2026-10-25 02:33] qa · mistake: - [medium] Automated test execution blocked by Node.js environment constraints: Tests `tests/unit/test_render_logic.js` and `tests/component/test_dom_rendering.js` fail due to missing 'expect' export from 'node:test' and DOM not available in Node runtime. These are tooling limit… (`8486d0325d01`)
- [2026-10-25 02:50] qa · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`8486d0325d01`)
- [2026-10-25 02:50] qa · mistake: - [high] Automated test execution blocked by Node.js environment constraints: Test files `tests/unit/test_render_logic.js` and `tests/contract/test_acceptance_criteria.js` use `describe` from `node:test` which is not available in Node v24+ without explicit import. This blocks au… (`8486d0325d01`)
- [2026-10-25 03:06] qa · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`8486d0325d01`)
- [2026-10-25 03:06] qa · mistake: - [high] Automated test execution blocked by Node.js environment constraints: Test files tests/unit/test_render_logic.js and tests/component/test_dom_rendering.js use describe from node:test which is not available in Node v24+ without explicit import. This blocks automated valid… (`8486d0325d01`)
- [2026-10-25 04:00] qa · mistake: - [high] Validation failed: node tests/contract/test_acceptance_criteria.js: ✗ AC2 failed: document is not defined - [high] Validation failed: node tests/unit/test_render_logic.js: ✗ XSS escaping test failed: document is not defined - [high] Validation gap: failed_runs: Automate… (`8486d0325d01`)
- [2026-10-25 04:15] qa · context: DOM APIs (document.createElement, etc.) are not available in Node.js without jsdom. Tests relying on these must either run in a browser or use a mock DOM environment. (`8486d0325d01`)
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
