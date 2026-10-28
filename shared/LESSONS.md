# Lessons

A new session starts with an empty conversation.
These lines are the carry-over: mistakes to avoid, and context that still applies.

## Session memory

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
- [2026-10-28 12:49] qa · context: When plan specifies HTTP endpoints, implementation must be a web server (e.g., PHP built-in server), not a CLI script. Automated validation fails if the runtime cannot start the service. (`15e5ca7f1670`)
- [2026-10-28 12:49] qa · mistake: Scope was wrong for developer: The implementation (CLI) does not match the plan (HTTP backend). The acceptance criteria explicitly require HTTP endpoints and status codes. Developer must either implement an HTTP server or update the plan to accept a CLI tool. (`15e5ca7f1670`)
- [2026-10-28 12:49] developer · mistake: qa sent work back because scope was wrong: The implementation (CLI) does not match the plan (HTTP backend). The acceptance criteria explicitly require HTTP endpoints and status codes. Developer must either implement an HTTP server or update the plan to accept a CLI tool. (`15e5ca7f1670`)
- [2026-10-28 13:19] pm · context: When the input is 'build a simple website', always ask about purpose, page count, styling level, and data source to prevent scope creep. (`1b994b32c1a5`)
- [2026-10-28 13:20] pm · context: When scoping UI/UX tasks based on vague briefs, explicitly confirm content source (hardcoded vs. API mock) and required sections/layout to prevent scope creep. (b956a623435a) (`1b994b32c1a5`)
- [2026-10-28 13:26] qa · context: For Node v24+ environments, avoid importing 'expect' from 'node:test'; use native 'assert' module to prevent export errors. Existing tests using 'describe' without import will fail. (`1b994b32c1a5`)
- [2026-10-28 13:26] qa · mistake: - [high] Automated Validation Blocked by Node Runtime Constraints: Test suite `test_dom_rendering.js` fails with 'document is not defined' because the prototype uses browser-specific DOM APIs (document.createElement, etc.) which are unavailable in Node v24+ without jsdom. This p… (`1b994b32c1a5`)
- [2026-10-28 13:26] developer · mistake: QA sent this back: - [high] Automated Validation Blocked by Node Runtime Constraints: Test suite `test_dom_rendering.js` fails with 'document is not defined' because the prototype uses browser-specific DOM APIs (document.createElement, etc.) which are unavailable in Node v24+ wi… (`1b994b32c1a5`)
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
