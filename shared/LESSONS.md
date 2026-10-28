# Lessons

A new session starts with an empty conversation.
These lines are the carry-over: mistakes to avoid, and context that still applies.

## Session memory

- [2026-10-25 13:47] pm · mistake: developer sent work back because scope was wrong: The input 'test' lacks functional requirements, target platform, and acceptance criteria. Per the approved plan, no implementation can begin until the human answers the three clarifying questions listed in PLAN.md. (`5e49b15c3f58`)
- [2026-10-25 13:50] qa · mistake: - [high] Validation gap: manual_only: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`5e49b15c3f58`)
- [2026-10-25 13:50] developer · mistake: QA sent this back: - [high] Validation gap: manual_only: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`5e49b15c3f58`)
- [2026-10-25 13:53] pm · context: Released slice: test (`5e49b15c3f58`)
- [2026-10-25 13:57] pm · context: When the brief is 'build a simple website for profolio', always ask about required sections, single vs. multi-page structure, and responsiveness to prevent scope creep. (`b956a623435a`)
- [2026-10-25 13:58] pm · context: When scoping UI/UX tasks based on vague briefs, explicitly confirm content source (hardcoded vs. API mock) and required sections/layout to prevent scope creep. (`b956a623435a`)
- [2026-10-25 13:59] pm · context: When scoping UI/UX tasks based on vague briefs, explicitly confirm content source (hardcoded vs. API mock) and required sections/layout to prevent scope creep. (b956a623435a) (`b956a623435a`)
- [2026-10-25 14:05] qa · mistake: - [high] Validation failed: node tests/contract/test_acceptance_criteria.js: file:///Users/kahhuei/playground/workspace/b956a623435a/tests/contract/test_acceptance_criteria.js:142 assert.ok(!htmlContent.includes('<link href=') || htmlContent.includes('<!--'), 'AC5: No external C… (`b956a623435a`)
- [2026-10-25 14:05] developer · mistake: QA sent this back: - [high] Validation failed: node tests/contract/test_acceptance_criteria.js: file:///Users/kahhuei/playground/workspace/b956a623435a/tests/contract/test_acceptance_criteria.js:142 assert.ok(!htmlContent.includes('<link href=') || htmlContent.includes('<!--'),… (`b956a623435a`)
- [2026-10-25 14:10] qa · context: When creating mock DOM elements for Node.js tests, ensure `addEventListener` is implemented to prevent runtime TypeError. Use a proper jsdom setup or native assert-only logic where possible. (`b956a623435a`)
- [2026-10-25 14:10] qa · mistake: Scope was wrong for pm: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`b956a623435a`)
- [2026-10-25 14:10] pm · mistake: qa sent work back because scope was wrong: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`b956a623435a`)
- [2026-10-25 14:39] qa · mistake: - [high] Test Suite Blocked by Syntax Error: `tests/contract/test_acceptance_criteria.js` line 142: `assert.ok(!htmlContent.includes('<link href=') || htmlContent.includes('<!--'), 'AC5: No external C…` is missing a closing parenthesis. This blocks automated validation of AC5. -… (`b956a623435a`)
- [2026-10-25 14:39] developer · mistake: QA sent this back: - [high] Test Suite Blocked by Syntax Error: `tests/contract/test_acceptance_criteria.js` line 142: `assert.ok(!htmlContent.includes('<link href=') || htmlContent.includes('<!--'), 'AC5: No external C…` is missing a closing parenthesis. This blocks automated v… (`b956a623435a`)
- [2026-10-25 14:39] pm · mistake: Release rejected by supervisor: beed test all passed (`b956a623435a`)
- [2026-10-25 14:39] developer · context: Supervisor rejected release (PM triaging): beed test all passed (`b956a623435a`)
- [2026-10-25 14:40] pm · context: When scoping UI/UX tasks based on vague briefs, explicitly confirm content source (hardcoded vs. API mock) and required sections/layout to prevent scope creep. (b956a623435a) (`b956a623435a`)
- [2026-10-25 14:51] developer · context: For Node v24+ environments, always use native 'assert' module instead of importing from 'node:test' to avoid export errors. Mock DOM elements must implement addEventListener directly on the element instance. (`b956a623435a`)
- [2026-10-25 14:53] qa · context: When creating mock DOM elements for Node.js tests, ensure `addEventListener` is implemented directly on the element instance to prevent runtime TypeError. Use a proper jsdom setup or native assert-only logic where possible. (`b956a623435a`)
- [2026-10-25 14:53] qa · mistake: - [high] Component Test Suite Blocked by Mock DOM Implementation Error: `tests/component/test_dom_rendering.js` crashes with `TypeError: aboutLink.addEventListener is not a function`. The mock element created via `createElement` does not expose the `addEventListener` method, cau… (`b956a623435a`)
- [2026-10-25 14:53] developer · mistake: QA sent this back: - [high] Component Test Suite Blocked by Mock DOM Implementation Error: `tests/component/test_dom_rendering.js` crashes with `TypeError: aboutLink.addEventListener is not a function`. The mock element created via `createElement` does not expose the `addEventLi… (`b956a623435a`)
- [2026-10-25 14:54] pm · context: Released slice: build a simple website for profolio (`b956a623435a`)
- [2026-10-25 14:55] pm · context: Released slice: one-click release (`release_one_click01`)
- [2026-10-27 15:01] qa · mistake: Scope was wrong for pm: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`1227fe2d7465`)
- [2026-10-27 15:01] pm · mistake: qa sent work back because scope was wrong: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`1227fe2d7465`)
- [2026-10-27 15:01] pm · context: When scoping UI/UX tasks based on vague briefs, explicitly confirm content source (hardcoded vs. API mock) and required sections/layout to prevent scope creep. (b956a623435a) (`1227fe2d7465`)
- [2026-10-27 15:12] qa · mistake: - [high] Validation gap: manual_only: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`1227fe2d7465`)
- [2026-10-27 15:12] developer · mistake: QA sent this back: - [high] Validation gap: manual_only: Acceptance criteria were checked manually but no automated validation ran. PM should add testable AC or require Developer-owned automated tests. (`1227fe2d7465`)
- [2026-10-27 15:20] pm · context: When QA provides a final report, the PM must confirm AC coverage against the report evidence before signaling release readiness. (`1227fe2d7465`)
- [2026-10-27 15:30] pm · context: Released slice: build a simple website about my office (`1227fe2d7465`)
