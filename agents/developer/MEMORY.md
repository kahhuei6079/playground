# Developer Memory

## Verified technical notes
- Prototypes should be self-contained in the thread workspace so QA can review them without extra setup.

## Lessons learned
- Record confirmed root causes and fixes here after approved releases.

## Related files
- Add focused notes (for example `memory/web.md`) when this file would otherwise grow too large.

## Session memory

- [2026-10-25 02:53] developer · context: Supervisor rejected release (PM triaging): fix bugs (`t`)
- [2026-10-25 02:54] developer · context: Supervisor rejected release (PM triaging): Fix the button (`rel000000001`)
- [2026-10-25 03:06] developer · mistake: QA sent this back: - [high] Automated test execution blocked by Node.js environment constraints: Test files tests/unit/test_render_logic.js and tests/component/test_dom_rendering.js use describe from node:test which is not available in Node v24+ without explicit import. This blo… (`8486d0325d01`)
- [2026-10-25 03:48] developer · context: Supervisor rejected release (PM triaging): check why failed run (`8486d0325d01`)
- [2026-10-25 04:00] developer · mistake: QA sent this back: - [high] Validation failed: node tests/contract/test_acceptance_criteria.js: ✗ AC2 failed: document is not defined - [high] Validation failed: node tests/unit/test_render_logic.js: ✗ XSS escaping test failed: document is not defined - [high] Validation gap: fa… (`8486d0325d01`)
- [2026-10-25 04:01] developer · context: Supervisor rejected release (PM triaging): node test failed fix it (`8486d0325d01`)
- [2026-10-25 04:03] developer · context: Supervisor rejected release (PM triaging): PM must fix AC (`releasegate98`)
- [2026-10-25 04:04] developer · context: Supervisor rejected release (PM triaging): Fix the button (`rel000000001`)
- [2026-10-25 04:06] developer · context: Supervisor rejected release (PM triaging): nope (`releasegate98`)
- [2026-10-25 04:12] developer · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`8486d0325d01`)
- [2026-10-25 04:15] developer · mistake: QA sent this back: - [high] Automated Test Execution Blocked by Node.js Environment Constraints: Test files `tests/unit/test_render_logic.js` and `tests/contract/test_acceptance_criteria.js` use DOM APIs (`document.createElement`) which are not available in the Node runtime with… (`8486d0325d01`)
- [2026-10-25 04:18] developer · context: Supervisor rejected release (PM triaging): check why node test fail (`8486d0325d01`)
- [2026-10-25 04:21] developer · context: Supervisor rejected release (PM triaging): PM please fix AC wording (`releasetest1`)
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
