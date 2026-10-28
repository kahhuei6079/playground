const AGENTS = [
  { id: "pm", name: "PM", emoji: "📋", role: "Planning", tab: "plan" },
  { id: "architect", name: "Architect", emoji: "🏗️", role: "Scope", tab: "plan" },
  { id: "designer", name: "Designer", emoji: "🎨", role: "UX spec", tab: "design" },
  { id: "developer", name: "Developer", emoji: "💻", role: "Prototype", tab: "files" },
  { id: "qa", name: "QA", emoji: "🔍", role: "Verification", tab: "qa" },
];

const ROLE_TAGS = {
  pm: "PM_AGENT",
  architect: "ARCH_AGENT",
  human: "YOU",
  designer: "DESIGN_AGENT",
  developer: "DEV_AGENT",
  qa: "QA_AGENT",
};

const OFFICE_IDS = ["pm", "architect", "human", "designer", "developer", "qa"];
let officeReady = false;

const ACTION_LABELS = {
  pm: "ASSIGN TASK",
  designer: "DESIGN SPEC",
  developer: "EXECUTE CODE",
  qa: "RUN CHECKS",
  human_brief: "BRIEFING",
  human_plan: "REVIEW PLAN",
  human_release: "SIGN RELEASE",
  idle: "STANDBY",
  run: "OFFICE ONLINE",
  released: "SHIPPED",
};

const IDLE_LINES = {
  pm: "Waiting for a brief…",
  architect: "Reviewing system shape…",
  designer: "Reviewing the backlog…",
  developer: "Standing by at the terminal…",
  qa: "Test cases ready when you are.",
  human: "On the floor — ping me when you need a sign-off.",
};

const WORK_LINES = {
  pm: "Writing the plan & acceptance criteria…",
  architect: "Classifying UI/UX vs backend vs CLI…",
  designer: "Mapping screens and user flows…",
  developer: "Typing code into the workspace…",
  qa: "Reading files against the checklist…",
};

const STORAGE_KEY = "agentOfficeThread";
const SESSION_LOG_KEY = "agentOfficeSessionLog";
const ACTIVITY_SCOPE_KEY = "agentOfficeActivityScope";

function loadSessionLog() {
  try {
    const raw = sessionStorage.getItem(SESSION_LOG_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

const state = {
  threadId: null,
  working: null,
  busy: false,
  runStatus: "idle",
  done: new Set(),
  interrupt: null,
  artifacts: { plan: null, scope: null, design: null, qa: null, acVerification: null, files: null },
  tab: "plan",
  agentModels: {},
  defaultModelProfile: null,
  modelsInUse: {},
  modelsLastUsed: {},
  modelsConfigPath: "models.yaml",
  caption: "The team is around the office. Send a brief when you're ready.",
  lessonCount: 0,
  meeting: false,
  tasks: [],
  serverActivity: [],
  liveActivityEntries: [],
  _serverActivityLen: 0,
  sessionLog: loadSessionLog(),
  activityScope: sessionStorage.getItem(ACTIVITY_SCOPE_KEY) || "session",
  bubbles: { ...IDLE_LINES },
};

function ensureThread(threadId) {
  if (!threadId) return;
  state.threadId = threadId;
  els.thread.textContent = threadId;
  localStorage.setItem(STORAGE_KEY, threadId);
}

const els = {
  pixelFloor: document.getElementById("pixel-floor"),
  pixelAction: document.getElementById("pixel-action"),
  pixelMemory: document.getElementById("pixel-memory"),
  propTerminal: document.getElementById("prop-terminal"),
  officeScene: document.getElementById("office-scene"),
  officeCaption: document.getElementById("office-caption"),
  officeName: document.getElementById("office-name"),
  officeSign: document.getElementById("office-sign"),
  officeSignText: document.getElementById("office-sign-text"),
  form: document.getElementById("task-form"),
  task: document.getElementById("task"),
  runBtn: document.getElementById("run-btn"),
  stopBtn: document.getElementById("stop-btn"),
  live: document.getElementById("live-output"),
  feedAgent: document.getElementById("feed-agent"),
  history: document.getElementById("history"),
  taskList: document.getElementById("task-list"),
  taskCount: document.getElementById("task-count"),
  status: document.getElementById("status-text"),
  pulse: document.getElementById("pulse-dot"),
  approval: document.getElementById("approval"),
  gateLabel: document.getElementById("gate-label"),
  gatePrompt: document.getElementById("gate-prompt"),
  feedback: document.getElementById("feedback"),
  approve: document.getElementById("approve-btn"),
  reject: document.getElementById("reject-btn"),
  planBrief: document.getElementById("plan-brief"),
  discussStatus: document.getElementById("discuss-status"),
  thread: document.getElementById("thread-label"),
  model: document.getElementById("model-label"),
  modelGrid: document.getElementById("model-grid"),
  modelsConfigPath: document.getElementById("models-config-path"),
  deliverablePanel: document.getElementById("deliverable-panel"),
  deliverablePath: document.getElementById("deliverable-path"),
  deliverablePreview: document.getElementById("deliverable-preview"),
  deliverableOpenFolder: document.getElementById("deliverable-open-folder"),
  deliverableFiles: document.getElementById("deliverable-files"),
};

function agentMeta(id) {
  return AGENTS.find((a) => a.id === id);
}

function statusTag(mode) {
  if (mode === "working") return "busy";
  if (mode === "done") return "online";
  if (mode === "human-needed") return "review";
  return "idle";
}

function isPmDiscussing() {
  const gate = state.interrupt?.gate;
  if (!gate) return false;
  if (state.busy && state.runStatus === "running") return false;
  return gate === "brief" || gate === "plan" || gate === "release";
}

function gateBlocksMeetingResume() {
  return state.busy && state.runStatus === "running";
}

/** Stale plan/brief UI after sign-off — never block the release gate. */
function shouldDismissStaleGateInterrupt(gate) {
  return gateBlocksMeetingResume() && (gate === "plan" || gate === "brief");
}

function stationMode(id) {
  if (id === "human") {
    if (state.interrupt && !gateBlocksMeetingResume()) return "human-needed";
    if (state.runStatus === "released") return "done";
    return "idle";
  }
  if (id === "pm" && isPmDiscussing()) return "human-needed";
  if (state.working === id) return "working";
  if (state.done.has(id)) return "done";
  return "idle";
}

function bubbleText(id) {
  const atGate = state.interrupt && !gateBlocksMeetingResume();
  if (id === "human") {
    if (atGate && state.interrupt?.gate === "brief") return "A few questions before the plan.";
    if (atGate && state.interrupt?.gate === "plan") return "Let's verify AC before sign-off.";
    if (atGate && state.interrupt?.gate === "release") return "Ready for release sign-off.";
    if (state.runStatus === "released") return "Shipped. Nice work.";
    return state.bubbles.human;
  }
  if (id === "pm") {
    if (atGate && state.interrupt?.gate === "brief") return "I have a few questions before I plan.";
    if (atGate && state.interrupt?.gate === "plan") return "Walk through AC — ready to sign off?";
    if (atGate && state.interrupt?.gate === "release") return "QA passed — I verified every AC. Ready to ship?";
  }
  const mode = stationMode(id);
  if (mode === "working") return WORK_LINES[id] || "Working…";
  if (mode === "done") return "Wrapped this round.";
  return state.bubbles[id] || IDLE_LINES[id];
}

function ensureDiscussMeeting() {
  if (state.meeting || !state.interrupt || gateBlocksMeetingResume()) return;
  if (state.interrupt.gate === "brief") openBriefMeeting(state.interrupt);
  if (state.interrupt.gate === "plan") openPlanMeeting();
  if (state.interrupt.gate === "release") openReleaseMeeting();
}

function rosterStatus(agentId) {
  if (state.working === agentId && state.modelsInUse[agentId]) return "in-use";
  if (state.modelsInUse[agentId] && state.working === agentId) return "in-use";
  if (state.modelsLastUsed[agentId]) return "last-used";
  return "configured";
}

function agentModelMeta(agentId) {
  return state.agentModels[agentId] || state.defaultModelProfile;
}

function syncAgentModelsFromMeta(data) {
  state.defaultModelProfile = data.default || null;
  const fromServer = data.agents || {};
  state.agentModels = {};
  AGENTS.forEach((agent) => {
    state.agentModels[agent.id] = fromServer[agent.id] || state.defaultModelProfile;
  });
}

function formatModelCard(agent) {
  const meta = agentModelMeta(agent.id);
  const label = agent.name;
  const status = rosterStatus(agent.id);
  const live = state.modelsInUse[agent.id] || state.modelsLastUsed[agent.id];
  const configured = meta ? `${meta.provider}/${meta.model}` : null;
  const displayModel = status === "in-use" && live ? live : live || configured || "—";
  const statusLabel =
    status === "in-use" ? "IN USE NOW" : status === "last-used" ? "LAST USED" : "CONFIGURED";
  const provider = meta?.provider || (live?.includes("/") ? live.split("/")[0] : "—");
  const keyLine = meta
    ? meta.provider === "openai"
      ? meta.api_key_set
        ? `Key: ${meta.api_key_env}`
        : `Missing ${meta.api_key_env || "API key"}`
      : meta.base_url || "local Ollama"
    : "Restart UI server if roster stays empty";
  const warn = meta?.provider === "openai" && !meta.api_key_set ? " warn" : "";
  const active = status === "in-use" ? " active in-use" : status === "last-used" ? " last-used" : "";
  return `<article class="model-card${active}" data-agent="${agent.id}">
    <div class="model-card-top">
      <strong>${label}</strong>
      <span class="provider-pill">${provider}</span>
    </div>
    <div class="model-status">${statusLabel}</div>
    <div class="model-name" title="${displayModel}">${displayModel}</div>
    ${configured && live && configured !== live ? `<div class="model-meta">yaml: ${configured}</div>` : ""}
    <div class="model-meta${warn}">${keyLine}</div>
    ${meta ? `<div class="model-meta">temp ${meta.temperature}</div>` : ""}
  </article>`;
}

function applyLiveModels(live) {
  if (!live) return;
  if (live.models_in_use) state.modelsInUse = { ...live.models_in_use };
  if (live.models_last_used) state.modelsLastUsed = { ...live.models_last_used };
}

function renderModelRoster() {
  els.modelGrid.innerHTML = AGENTS.map((agent) => formatModelCard(agent)).join("");
  if (els.modelsConfigPath && state.modelsConfigPath) {
    els.modelsConfigPath.textContent = state.modelsConfigPath.split("/").pop() || state.modelsConfigPath;
    els.modelsConfigPath.title = state.modelsConfigPath;
  }
}

function pixelActionLabel() {
  if (state.interrupt?.gate === "brief") return ACTION_LABELS.human_brief;
  if (state.interrupt?.gate === "plan") return ACTION_LABELS.human_plan;
  if (state.interrupt?.gate === "release") return ACTION_LABELS.human_release;
  if (state.runStatus === "released") return ACTION_LABELS.released;
  if (state.working) return ACTION_LABELS[state.working] || "WORKING";
  if (state.busy) return ACTION_LABELS.run;
  return ACTION_LABELS.idle;
}

function modelLineFor(id) {
  if (id === "human") return "supervised";
  if (state.working === id && state.modelsInUse[id]) return state.modelsInUse[id];
  if (state.modelsInUse[id]) return state.modelsInUse[id];
  if (state.modelsLastUsed[id]) return state.modelsLastUsed[id];
  const model = agentModelMeta(id);
  return model ? `${model.provider}/${model.model}` : "—";
}

function onActorClick(id) {
  if (id === "human" && state.interrupt) {
    els.approval.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }
  const agent = agentMeta(id);
  if (!agent?.tab) return;
  state.tab = agent.tab;
  document.querySelectorAll(".tabs button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === agent.tab);
  });
  showArtifact();
}

function syncOfficeWorld() {
  if (!window.OfficeWorld) return;
  window.OfficeWorld.init(els.pixelFloor);
  if (!officeReady) {
    window.OfficeWorld.setOnCaption?.(setCaption);
    window.OfficeWorld.bindClick(onActorClick);
    els.propTerminal?.addEventListener("click", () => {
      window.OfficeWorld.summonToHotspot?.("terminal");
    });
    officeReady = true;
  }
  OFFICE_IDS.forEach((id) => {
    const mode = stationMode(id);
    const pose = mode === "working" ? "work" : "idle";
    window.OfficeWorld.updateActor(id, {
      mode,
      bubble: bubbleText(id),
      tag: statusTag(stationMode(id)),
      model: modelLineFor(id),
      pose,
    });
  });
}

function renderOffice() {
  ensureDiscussMeeting();
  renderModelRoster();
  els.officeScene.classList.toggle("busy", state.busy || Boolean(state.working));
  els.officeCaption.textContent = state.caption;

  const kept = state.lessonCount || 0;
  els.pixelMemory.textContent = kept ? `MEMORY · ${kept} kept` : "MEMORY · empty";
  els.pixelMemory.title = "Lessons kept for the next session. A new run starts with an empty chat.";

  const action = pixelActionLabel();
  els.pixelAction.textContent = action;
  els.pixelAction.classList.toggle("hot", Boolean(state.working || state.interrupt));
  els.propTerminal.classList.toggle("active", Boolean(state.working));

  syncOfficeWorld();

  const names = { pm: "PM", designer: "Designer", developer: "Developer", qa: "QA", human: "You" };
  els.feedAgent.textContent = state.working
    ? names[state.working] || state.working
    : state.interrupt
      ? "You (approval)"
      : "—";
}

function setStatus(text, busy) {
  state.busy = busy;
  els.status.textContent = text;
  els.pulse.hidden = !busy;
}

function setCaption(text) {
  state.caption = text;
  els.officeCaption.textContent = text;
}

function applyOfficeBranding(office) {
  const cfg = office || {};
  const sign = cfg.sign || {};
  const name = (cfg.name || "Agent Office").trim() || "Agent Office";
  state.officeName = name;
  document.title = name;
  if (els.officeName) els.officeName.textContent = name;

  const scene = els.officeScene;
  const signEl = els.officeSign;
  const signText = els.officeSignText;
  if (!signEl || !scene?.classList.contains("wood")) return;

  const atBottom = sign.position === "bottom";
  signEl.classList.toggle("sign-bottom", atBottom);
  if (sign.top_percent != null) {
    scene.style.setProperty("--office-sign-top", `${sign.top_percent}%`);
  }
  if (sign.bottom_percent != null) {
    scene.style.setProperty("--office-sign-bottom", `${sign.bottom_percent}%`);
  }
  if (sign.width_percent != null) {
    scene.style.setProperty("--office-sign-width", `${sign.width_percent}%`);
  }

  const hideBaked = sign.hide_baked_label !== false;
  const showLabel = sign.show !== false;
  signEl.classList.toggle("hide-cover", !hideBaked);
  signEl.classList.toggle("cover-only", hideBaked && !showLabel);
  if (signText) signText.textContent = name;
  signEl.hidden = !hideBaked && !showLabel;
}

function setLive(text, streaming) {
  const value = text || "";
  els.live.textContent = value || "Model output streams here while someone is at their desk.";
  els.live.classList.toggle("empty", !value);
  if (streaming) els.live.scrollTop = els.live.scrollHeight;
}

function esc(value) {
  return String(value).replace(/[&<>]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[ch]));
}

function filePreviewUrl(threadId, relPath) {
  if (!threadId || !relPath) return "#";
  return `/preview/${encodeURIComponent(threadId)}/${relPath.split("/").map(encodeURIComponent).join("/")}`;
}

async function copyText(text) {
  if (!text) return false;
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

async function openOutputFolder(threadId) {
  const id = threadId || state.threadId;
  if (!id) return;
  const folderPath =
    state.deliverableFolder ||
    state.tasks?.find((t) => t.thread_id === id)?.folder ||
    els.deliverablePath?.textContent?.trim() ||
    "";
  try {
    const res = await fetch(`/api/thread/${encodeURIComponent(id)}/open-folder`, { method: "POST" });
    if (!res.ok) {
      const detail = await res.text();
      if (folderPath && await copyText(folderPath)) {
        setStatus(`Could not open Finder — path copied to clipboard`, false);
      } else {
        setStatus(`Could not open folder: ${detail}`, false);
      }
      return;
    }
    const data = await res.json();
    setStatus(`Opened folder in Finder`, false);
    if (data.folder) {
      els.deliverablePath.textContent = data.folder;
      els.deliverablePath.title = data.folder;
    }
  } catch (err) {
    if (folderPath && await copyText(folderPath)) {
      setStatus(`Could not open Finder — path copied to clipboard`, false);
    } else {
      setStatus(`Could not open folder: ${err.message}`, false);
    }
  }
}

function renderDeliverable(data) {
  const panel = els.deliverablePanel;
  if (!panel) return;
  const threadId = data?.thread_id || state.threadId;
  const deliverable = data?.deliverable;
  const paths = deliverable?.files?.length
    ? deliverable.files
    : Object.keys(data?.files || {});
  if (!paths.length) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  const folder = deliverable?.folder || deliverable?.relative_folder || `workspace/${threadId}`;
  state.deliverableFolder = folder;
  els.deliverablePath.textContent = folder;
  els.deliverablePath.title = `Open in Finder: ${folder}`;
  const hasHtml = Boolean(deliverable?.has_html_preview ?? deliverable?.preview_path);
  if (els.deliverablePreview) {
    if (hasHtml && deliverable?.preview_url) {
      els.deliverablePreview.hidden = false;
      els.deliverablePreview.href = deliverable.preview_url;
      els.deliverablePreview.textContent = "Open in browser";
    } else {
      els.deliverablePreview.hidden = true;
    }
  }
  els.deliverableFiles.innerHTML = paths
    .map(
      (p) =>
        `<li><a href="${filePreviewUrl(threadId, p)}" target="_blank" rel="noopener">${esc(p)}</a></li>`,
    )
    .join("");
}

function listItems(items) {
  if (!items || !items.length) return "";
  return `<ul>${items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;
}

function renderBrief(payload) {
  if (!els.planBrief || !payload) return;
  const questions = payload.questions || [];
  const assumptions = payload.assumptions || [];
  els.planBrief.className = "plan-brief";
  els.planBrief.innerHTML = `
    ${payload.message ? `<p>${esc(payload.message)}</p>` : ""}
    ${questions.length ? `<h4>Questions for you</h4>${listItems(questions)}` : ""}
    ${assumptions.length ? `<h4>Assumptions if we proceed</h4>${listItems(assumptions)}` : ""}
  `;
}

function briefMeetingLines(payload) {
  const lines = [];
  if (payload?.message) lines.push(payload.message);
  (payload?.questions || []).forEach((q) => lines.push(q));
  return lines.length ? lines : ["Quick check before I draft the plan."];
}

function openBriefMeeting(payload) {
  if (gateBlocksMeetingResume() || state.meeting || state.interrupt?.gate !== "brief") return;
  state.meeting = true;
  if (els.discussStatus) {
    els.discussStatus.textContent = "PM is in the meeting room to confirm scope before planning.";
  }
  setCaption("PM walked into the meeting room with questions about your brief.");
  window.OfficeWorld?.startMeeting(briefMeetingLines(payload));
}

function setApprovalButtons(gate) {
  if (gate === "brief") {
    els.approve.textContent = "Send answers";
    els.reject.textContent = "Use assumptions";
    els.feedback.placeholder = "Answer the PM's questions here (optional if you use their assumptions).";
    return;
  }
  if (gate === "plan") {
    els.approve.textContent = "Sign off AC";
    els.reject.textContent = "AC needs changes";
    els.feedback.placeholder = "What acceptance criteria or scope should the PM fix? Required if you send back.";
    return;
  }
  if (gate === "release") {
    els.approve.textContent = "Sign release";
    els.reject.textContent = "Send back to PM";
    els.feedback.placeholder =
      "What is wrong with scope, AC, or the build? PM will triage with the team. Required if you send back.";
    return;
  }
  els.approve.textContent = "Agree";
  els.reject.textContent = "Send back";
  els.feedback.placeholder = "Say what to change. Required if you reject.";
}

const PROJECT_TYPE_LABEL = {
  ui_ux: "UI / UX",
  fullstack_web: "Full-stack web",
  backend_service: "Backend service",
  api_only: "API only",
  cli_tool: "CLI / console",
  data_script: "Data / script",
  mixed: "Mixed",
};

function renderScopeBrief(scope) {
  if (!els.planBrief || !scope) return;
  const arch = scope.architecture_brief || {};
  const agree = scope.scope_agreement || {};
  const ptype = PROJECT_TYPE_LABEL[agree.project_type || arch.project_type] || agree.project_type || "—";
  const track = agree.needs_designer === false ? "No Designer track (build-focused)" : "Includes UI/UX design";
  els.planBrief.className = "plan-brief scope-brief";
  let html = `<h3>Scope — Architect ↔ PM</h3><p class="scope-type"><strong>${esc(ptype)}</strong> · ${esc(track)}</p>`;
  if (agree.aligned_summary) html += `<p>${esc(agree.aligned_summary)}</p>`;
  else if (arch.summary) html += `<p>${esc(arch.summary)}</p>`;
  if (arch.delivery_shape) html += `<h4>Delivery shape</h4><p>${esc(arch.delivery_shape)}</p>`;
  if (arch.system_components?.length) {
    html += `<h4>Components</h4><ul>${arch.system_components.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>`;
  }
  if (agree.architect_response) {
    html += `<h4>PM response</h4><p>${esc(agree.architect_response)}</p>`;
  }
  const lines = scope.dialogue || [];
  if (lines.length) {
    html += `<h4>Scope huddle</h4><ul class="scope-dialogue">`;
    lines.forEach((line) => {
      const who = ACTOR_NAMES[line.from] || line.from;
      html += `<li><strong>${esc(who)}</strong> ${esc(line.text || "")}</li>`;
    });
    html += `</ul>`;
  }
  els.planBrief.innerHTML = html;
}

function renderPlanSignoff(plan, scope) {
  if (!els.planBrief || !plan) return;
  const ac = plan.acceptance_criteria || [];
  const agree = scope?.scope_agreement || scope || {};
  const scopeLine =
    agree.project_type
      ? `<p class="scope-type-inline">Delivery: <strong>${esc(
          PROJECT_TYPE_LABEL[agree.project_type] || agree.project_type,
        )}</strong>${agree.needs_designer === false ? " · skipping Designer" : ""}</p>`
      : "";
  els.planBrief.className = "plan-brief ac-signoff";
  els.planBrief.innerHTML = `
    ${scopeLine}
    <p class="ac-intro">You and the PM are in the meeting room. Confirm each criterion is testable, then sign off.</p>
    <h4>Acceptance criteria</h4>
    ${
      ac.length
        ? `<ul class="ac-checklist">${ac.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`
        : "<p class='ac-warn'>No acceptance criteria — send the plan back.</p>"
    }
    <h4>Goal</h4>
    <p>${esc(plan.goal || "Plan")}</p>
    ${plan.scope ? `<p>${esc(plan.scope)}</p>` : ""}
    ${plan.requirements?.length ? `<h4>To do</h4>${listItems(plan.requirements)}` : ""}
    ${plan.out_of_scope?.length ? `<h4>Out of scope</h4>${listItems(plan.out_of_scope)}` : ""}
  `;
}

function acSignoffMeetingLines(plan) {
  if (!plan) return ["Let's verify acceptance criteria before sign-off."];
  const lines = ["Let's walk through acceptance criteria before you sign off."];
  (plan.acceptance_criteria || []).forEach((item, index) => {
    lines.push(`AC ${index + 1}: ${item}`);
  });
  if (!plan.acceptance_criteria?.length) {
    lines.push("We need testable acceptance criteria before design can start.");
  } else {
    lines.push("If these are complete and testable, sign off below. Otherwise tell me what to change.");
  }
  return lines;
}

function renderQaReport(qa) {
  if (!els.planBrief) return;
  if (!qa) {
    els.planBrief.className = "plan-brief empty";
    els.planBrief.textContent = "Waiting for QA results.";
    return;
  }
  els.planBrief.className = "plan-brief qa-report";
  let html = `<h3>${esc(qa.summary || "QA report")}</h3>`;
  if (qa.test_plan) {
    html += `<h4>Test plan</h4><pre class="qa-md">${esc(qa.test_plan)}</pre>`;
  }
  if (qa.test_matrix?.length) {
    html += `<h4>Test matrix</h4><table class="qa-table"><thead><tr><th>Requirement</th><th>Case</th><th>Status</th></tr></thead><tbody>`;
    qa.test_matrix.forEach((row) => {
      html += `<tr><td>${esc(row.requirement)}</td><td>${esc(row.test_case)}</td><td>${esc(row.status)}</td></tr>`;
    });
    html += `</tbody></table>`;
  }
  if (qa.validation_runs?.length) {
    html += `<h4>Validation runs</h4><ul class="qa-runs">`;
    qa.validation_runs.forEach((run) => {
      html += `<li class="${run.passed ? "pass" : "fail"}"><code>${esc(run.command)}</code> — ${
        run.passed ? "passed" : "failed"
      }</li>`;
    });
    html += `</ul>`;
  }
  if (qa.findings?.length) {
    html += `<h4>Findings</h4><ul>${qa.findings
      .map((f) => `<li>[${esc(f.severity)}] ${esc(f.title)}</li>`)
      .join("")}</ul>`;
  }
  if (qa.qa_artifacts_written?.length) {
    html += `<p class="qa-artifacts">Saved: ${qa.qa_artifacts_written.map((p) => esc(p)).join(", ")}</p>`;
  }
  els.planBrief.innerHTML = html;
}

function renderAcVerificationBlock(ac) {
  if (!ac || (!ac.summary && !(ac.coverage || []).length)) return "";
  const met = ac.all_ac_met;
  let html = `<h4>PM AC verification</h4>`;
  html += `<p class="ac-verified-flag ${met ? "pass" : "fail"}">${met ? "All acceptance criteria met" : "Gaps remain"} — ${esc(
    ac.summary || "",
  )}</p>`;
  if (ac.coverage?.length) {
    html += `<table class="qa-table"><thead><tr><th>Criterion</th><th>Met</th><th>Evidence</th></tr></thead><tbody>`;
    ac.coverage.forEach((row) => {
      html += `<tr><td>${esc(row.criterion)}</td><td>${row.met ? "yes" : "no"}</td><td>${esc(row.evidence || "")}</td></tr>`;
    });
    html += `</tbody></table>`;
  }
  if (ac.gaps?.length) {
    html += `<h4>AC gaps</h4><ul>${ac.gaps.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>`;
  }
  return html;
}

function renderReleaseReview(qa, acVerification) {
  if (!els.planBrief) return;
  els.planBrief.className = "plan-brief";
  els.planBrief.innerHTML = "";
  renderQaReport(qa);
  if (acVerification) {
    els.planBrief.innerHTML += renderAcVerificationBlock(acVerification);
  }
}

function showArtifact() {
  if (state.interrupt?.gate === "brief") {
    renderBrief(state.interrupt);
    return;
  }
  if (state.interrupt?.gate === "release") {
    renderReleaseReview(state.artifacts.qa, state.artifacts.acVerification);
    return;
  }
  if (state.interrupt?.gate === "plan" && state.artifacts.plan) {
    renderPlanSignoff(state.artifacts.plan, state.artifacts.scope);
    return;
  }
  const plan = state.artifacts.plan;
  if (!els.planBrief) return;
  if (!plan) {
    if (state.artifacts.scope) {
      renderScopeBrief(state.artifacts.scope);
      return;
    }
    els.planBrief.className = "plan-brief empty";
    els.planBrief.textContent = "Architect and PM will align scope, then the PM will draft the plan.";
    return;
  }
  els.planBrief.className = "plan-brief";
  els.planBrief.innerHTML = `
    <h3>${esc(plan.goal || "Plan")}</h3>
    ${plan.scope ? `<p>${esc(plan.scope)}</p>` : ""}
    ${plan.requirements?.length ? `<h4>To do</h4>${listItems(plan.requirements)}` : ""}
    ${plan.acceptance_criteria?.length ? `<h4>Done when</h4>${listItems(plan.acceptance_criteria)}` : ""}
    ${plan.out_of_scope?.length ? `<h4>Out of scope</h4>${listItems(plan.out_of_scope)}` : ""}
  `;
}

function openPlanMeeting() {
  if (gateBlocksMeetingResume() || state.meeting || state.interrupt?.gate !== "plan") return;
  state.meeting = true;
  if (els.discussStatus) {
    els.discussStatus.textContent =
      "Verify each acceptance criterion with the PM. Sign off when QA could test the slice as written.";
  }
  setCaption("PM is in the meeting room to review acceptance criteria with you.");
  window.OfficeWorld?.startMeeting(acSignoffMeetingLines(state.artifacts.plan), { mode: "ac_signoff" });
}

function releaseMeetingLines(qa, acVerification) {
  const lines = [];
  if (qa?.summary) lines.push(`QA summary: ${qa.summary}`);
  if (acVerification?.summary) lines.push(`PM AC review: ${acVerification.summary}`);
  (acVerification?.coverage || []).slice(0, 5).forEach((row) => {
    lines.push(`${row.met ? "Met" : "Gap"}: ${row.criterion}`);
  });
  return lines.length ? lines : ["QA passed and I confirmed every acceptance criterion."];
}

function openReleaseMeeting() {
  if (state.meeting || state.interrupt?.gate !== "release") return;
  state.meeting = true;
  if (els.discussStatus) {
    els.discussStatus.textContent =
      "PM walks through QA results and AC coverage. Sign release or send back to PM.";
  }
  setCaption("PM is in the meeting room for release sign-off.");
  window.OfficeWorld?.startMeeting(
    releaseMeetingLines(state.artifacts.qa, state.artifacts.acVerification),
    { mode: "release" },
  );
}

const ACTOR_NAMES = {
  pm: "PM",
  architect: "Architect",
  designer: "Designer",
  developer: "Developer",
  qa: "QA",
  human: "You",
};
const KIND_LABELS = {
  handoff: "Handoff",
  gate: "Review",
  work: "Progress",
  validation: "Tests",
  dialogue: "Discussion",
};

function actorLabel(id) {
  if (!id) return "";
  return ACTOR_NAMES[id] || id;
}

function actorLine(entry) {
  const from = actorLabel(entry.from);
  const to = actorLabel(entry.to);
  if (!from && !to) return "";
  if (from && to) {
    const arrow = entry.direction === "return" ? "↩" : "→";
    return `${from} ${arrow} ${to}`;
  }
  return from || to;
}

function activityEntryKey(entry) {
  const e = typeof entry === "string" ? { text: entry } : entry;
  return `${e.thread_id || ""}|${e.kind || "work"}|${e.from || ""}|${e.to || ""}|${e.text || ""}`;
}

function ingestActivityForSession(threadId, entries) {
  if (!entries?.length) return;
  const seen = new Set(state.sessionLog.map(activityEntryKey));
  for (const raw of entries) {
    const item =
      typeof raw === "string"
        ? { kind: "work", text: raw, thread_id: threadId }
        : { ...raw, thread_id: threadId || raw.thread_id };
    const key = activityEntryKey(item);
    if (seen.has(key)) continue;
    seen.add(key);
    state.sessionLog.push(item);
  }
  try {
    sessionStorage.setItem(SESSION_LOG_KEY, JSON.stringify(state.sessionLog.slice(-800)));
  } catch {
    /* quota */
  }
}

function fullTaskActivityLog() {
  return [...(state.serverActivity || []), ...(state.liveActivityEntries || [])];
}

function activityEntriesForDisplay() {
  if (state.activityScope === "session") return state.sessionLog;
  return fullTaskActivityLog();
}

function normalizeActivityFromValues(values) {
  const activity = values?.activity || [];
  if (activity.length) return activity;
  return (values?.history || []).map((text) => ({ kind: "work", text }));
}

function setActivityScope(scope) {
  state.activityScope = scope === "task" ? "task" : "session";
  sessionStorage.setItem(ACTIVITY_SCOPE_KEY, state.activityScope);
  document.querySelectorAll(".activity-scope-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.scope === state.activityScope);
  });
  els.history?.classList.toggle("whole-session", state.activityScope === "session");
  renderActivityLog();
}

function renderActivityLog(entries) {
  const list = (entries ?? activityEntriesForDisplay()).map((item) =>
    typeof item === "string" ? { kind: "work", text: item } : item,
  );
  if (!list.length) {
    const empty =
      state.activityScope === "session"
        ? "No office activity this browser session yet."
        : "No office activity for this task yet.";
    els.history.innerHTML = `<li class="activity-empty">${empty}</li>`;
    return;
  }
  const showThread = state.activityScope === "session";
  els.history.innerHTML = list
    .map((entry) => {
      const kind = entry.kind || "work";
      const actors = actorLine(entry);
      const ret = entry.direction === "return" ? " activity-return" : "";
      const dlg = kind === "dialogue" ? " activity-dialogue" : "";
      const threadTag =
        showThread && entry.thread_id
          ? `<span class="activity-thread">${esc(entry.thread_id)}</span>`
          : "";
      return `<li class="activity-item activity-${kind}${ret}${dlg}">
        <span class="activity-badge">${esc(KIND_LABELS[kind] || kind)}</span>
        ${threadTag}
        ${actors ? `<span class="activity-actors">${esc(actors)}</span>` : ""}
        <p class="activity-text">${esc(entry.text || "")}</p>
      </li>`;
    })
    .join("");
  els.history.scrollTop = els.history.scrollHeight;
}

function syncActivityFromThread(values) {
  const server = normalizeActivityFromValues(values);
  const prevLen = state._serverActivityLen || 0;
  if (server.length > prevLen) {
    ingestActivityForSession(state.threadId, server.slice(prevLen));
  } else if (server.length && prevLen === 0) {
    ingestActivityForSession(state.threadId, server);
  }
  state.serverActivity = server;
  state._serverActivityLen = server.length;
  if (server.length >= prevLen && server.length > 0) {
    state.liveActivityEntries = state.liveActivityEntries.filter((live) => {
      const key = activityEntryKey({ ...live, thread_id: state.threadId });
      return !server.some((s) => activityEntryKey({ ...s, thread_id: state.threadId }) === key);
    });
  }
  renderActivityLog();
}

function appendLiveActivity(entry) {
  state.liveActivityEntries = state.liveActivityEntries || [];
  state.liveActivityEntries.push(entry);
  ingestActivityForSession(state.threadId, [entry]);
  renderActivityLog();
}

const STATUS_LABEL = {
  released: "Released",
  awaiting_brief: "Briefing",
  scoping: "Scope alignment",
  awaiting_plan_approval: "Plan review",
  awaiting_release: "Release review",
  designing: "Designing",
  implementing: "Building",
  testing: "Testing",
  verifying_ac: "AC verification",
  revising: "Revising",
  blocked: "Blocked",
};

function canContinueTask(task) {
  return Boolean(task?.can_continue || task?.pending_nodes?.length);
}

const TASK_GROUP_KEY = "agentOfficeTaskGroups";

function parseTaskDate(updated) {
  const m = String(updated || "").match(/(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return { iso: "unknown", monthKey: "unknown", dayKey: "unknown", monthLabel: "Unknown", dayLabel: "Unknown date" };
  const iso = `${m[1]}-${m[2]}-${m[3]}`;
  const date = new Date(`${iso}T12:00:00Z`);
  const monthKey = `${m[1]}-${m[2]}`;
  const monthLabel = date.toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
  const dayLabel = date.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
  return { iso, monthKey, dayKey: iso, monthLabel, dayLabel };
}

function loadTaskGroupState() {
  try {
    return JSON.parse(sessionStorage.getItem(TASK_GROUP_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function saveTaskGroupState(map) {
  sessionStorage.setItem(TASK_GROUP_KEY, JSON.stringify(map));
}

function isTaskGroupOpen(key, defaultOpen) {
  const map = loadTaskGroupState();
  if (Object.prototype.hasOwnProperty.call(map, key)) return Boolean(map[key]);
  return defaultOpen;
}

function setTaskGroupOpen(key, open) {
  const map = loadTaskGroupState();
  map[key] = open;
  saveTaskGroupState(map);
}

function groupTasksByMonthDay(tasks) {
  const months = new Map();
  for (const task of tasks) {
    const info = parseTaskDate(task.updated);
    if (!months.has(info.monthKey)) {
      months.set(info.monthKey, {
        key: info.monthKey,
        label: info.monthLabel,
        days: new Map(),
      });
    }
    const month = months.get(info.monthKey);
    if (!month.days.has(info.dayKey)) {
      month.days.set(info.dayKey, {
        key: info.dayKey,
        label: info.dayLabel,
        iso: info.iso,
        tasks: [],
      });
    }
    month.days.get(info.dayKey).tasks.push(task);
  }
  return [...months.values()].map((month) => ({
    ...month,
    days: [...month.days.values()],
  }));
}

function renderTaskCard(task) {
  const active = task.thread_id === state.threadId ? " active" : "";
  const label = STATUS_LABEL[task.status] || task.status || "Unknown";
  const parts = [];
  if (task.preview_url) {
    parts.push(
      `<a class="task-output-link" href="${esc(task.preview_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Preview</a>`,
    );
  }
  if (task.folder) {
    parts.push(
      `<a href="#" class="task-output-link" data-open-folder="${esc(task.thread_id)}">Folder</a>`,
    );
  }
  if (canContinueTask(task)) {
    parts.push(
      `<button type="button" class="task-output-link task-continue" data-continue-thread="${esc(task.thread_id)}">Continue</button>`,
    );
  }
  const outputLink = parts.length ? parts.join("") : "";
  return `<li class="task-row${active}">
      <button type="button" class="task-item" data-thread="${esc(task.thread_id)}">
      <span class="task-status status-${esc(task.status)}">${esc(label)}</span>
      <span class="task-title">${esc(task.task)}</span>
      <span class="task-meta">${esc(task.thread_id)} · ${esc(task.owner)} · ${esc(task.updated)}</span>
    </button>${outputLink ? `<div class="task-links">${outputLink}</div>` : ""}</li>`;
}

function renderTasks(tasks) {
  state.tasks = tasks || [];
  if (els.taskCount) els.taskCount.textContent = String(state.tasks.length);
  if (!els.taskList) return;
  if (!state.tasks.length) {
    els.taskList.innerHTML = '<li class="task-empty">No tasks yet.</li>';
    return;
  }

  const groups = groupTasksByMonthDay(state.tasks);
  const newestMonth = groups[0]?.key;
  const newestDay = groups[0]?.days[0]?.key;

  els.taskList.innerHTML = groups
    .map((month) => {
      const monthCount = month.days.reduce((n, d) => n + d.tasks.length, 0);
      const monthOpen = isTaskGroupOpen(`m:${month.key}`, month.key === newestMonth);
      const daysHtml = month.days
        .map((day) => {
          const dayOpen = isTaskGroupOpen(`d:${day.key}`, day.key === newestDay);
          return `<li class="task-group task-day${dayOpen ? "" : " collapsed"}" data-group="d:${esc(day.key)}">
            <button type="button" class="task-group-toggle" aria-expanded="${dayOpen}">
              <span class="task-group-chevron" aria-hidden="true"></span>
              <span class="task-group-label">${esc(day.label)}</span>
              <span class="task-group-count">${day.tasks.length}</span>
            </button>
            <ul class="task-group-body">${day.tasks.map(renderTaskCard).join("")}</ul>
          </li>`;
        })
        .join("");
      return `<li class="task-group task-month${monthOpen ? "" : " collapsed"}" data-group="m:${esc(month.key)}">
        <button type="button" class="task-group-toggle" aria-expanded="${monthOpen}">
          <span class="task-group-chevron" aria-hidden="true"></span>
          <span class="task-group-label">${esc(month.label)}</span>
          <span class="task-group-count">${monthCount}</span>
        </button>
        <ul class="task-group-body task-day-list">${daysHtml}</ul>
      </li>`;
    })
    .join("");
}

let loadTasksTimer = null;

function scheduleLoadTasks() {
  if (loadTasksTimer) clearTimeout(loadTasksTimer);
  loadTasksTimer = setTimeout(() => {
    loadTasksTimer = null;
    loadTasks();
  }, 350);
}

async function refreshStopButton() {
  if (!els.stopBtn) return;
  try {
    const res = await fetch("/api/active");
    if (!res.ok) return;
    const data = await res.json();
    els.stopBtn.disabled = !(data.active || []).length;
  } catch {
    els.stopBtn.disabled = false;
  }
}

async function forceStopOffice() {
  if (!confirm("Force stop all active agent runs? The current model call may finish before the office halts.")) {
    return;
  }
  setStatus("Stopping the office…", true);
  try {
    const res = await fetch("/api/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ all: true }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    const n = (data.requested || []).length;
    setStatus(n ? `Stop requested for ${n} run(s)` : "No active runs to stop", false);
    setCaption("Agents will halt after the current step completes.");
    appendLiveActivity({
      kind: "gate",
      from: "human",
      text: n ? `Force stop requested (${n} active run(s)).` : "Force stop — nothing was running.",
    });
    loadTasks();
  } catch (err) {
    setStatus(`Stop failed: ${err.message}`, false);
  }
}

async function loadTasks() {
  try {
    const res = await fetch("/api/tasks", { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    renderTasks(data.tasks || []);
    refreshStopButton();
  } catch (err) {
    console.error("Failed to load /api/tasks", err);
  }
}

function pendingAgentLabel(nodes) {
  const n = nodes?.[0];
  return { pm: "PM", developer: "Developer", qa: "QA", designer: "Designer", pm_ac_verify: "PM" }[n] || n || "team";
}

function shouldAutoResumePending(nodes, values) {
  if (values?.status === "awaiting_release") return false;
  if (nodes?.includes("review")) return false;
  const allowed = new Set(["pm", "developer", "qa", "designer", "pm_ac_verify"]);
  return nodes?.length && nodes.every((n) => allowed.has(n));
}

function clearAutoResumeKeys(threadId) {
  if (!threadId) return;
  const prefix = `autoResume:${threadId}:`;
  for (let i = sessionStorage.length - 1; i >= 0; i--) {
    const key = sessionStorage.key(i);
    if (key?.startsWith(prefix)) sessionStorage.removeItem(key);
  }
}

async function maybeAutoResumePending(data) {
  const tid = state.threadId;
  const pending = data.pending_nodes || [];
  const live = data.live || {};
  if (!tid || !pending.length || data.interrupt || live.busy || state.busy) return;
  if (!shouldAutoResumePending(pending, data.values)) return;
  const key = `autoResume:${tid}:${pending.join(">")}`;
  if (sessionStorage.getItem(key)) return;
  sessionStorage.setItem(key, "1");
  const who = pendingAgentLabel(pending);
  setCaption(`Handoff paused — waking up ${who}…`);
  await continueTask(tid, `Resume pending step: ${pending.join(" → ")}`);
}

async function continueTask(threadId, note = "") {
  if (!threadId) return;
  if (state.busy && state.threadId === threadId) {
    setStatus("This thread is still running — try Force stop first.", false);
    return;
  }
  ensureThread(threadId);
  const url = new URL(window.location.href);
  url.searchParams.set("thread", threadId);
  history.replaceState(null, "", url);
  els.runBtn.disabled = true;
  const pending = note.includes("Resume pending") ? note.split(": ").pop() : "";
  setStatus(
    pending
      ? `Resuming ${pendingAgentLabel(pending.split(" → "))}…`
      : "Continuing thread — picking up where you left off…",
    true,
  );
  setCaption("The office is resuming this task.");
  try {
    const res = await fetch(`/api/thread/${encodeURIComponent(threadId)}/continue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: note || els.feedback?.value?.trim() || "" }),
    });
    if (!res.ok) {
      const detail = await res.text();
      setStatus(`Could not continue: ${detail}`, false);
      els.runBtn.disabled = false;
      return;
    }
    if (els.feedback) els.feedback.value = "";
    state.interrupt = null;
    state.busy = true;
    state.runStatus = "running";
    state.done = new Set();
    showApproval(null);
    renderOffice();
    await refreshThread();
    loadTasks();
  } catch (err) {
    els.runBtn.disabled = false;
    setStatus(`Could not continue: ${err.message}`, false);
  }
}

async function openTask(threadId) {
  if (!threadId || threadId === state.threadId) return;
  if (state.meeting) {
    state.meeting = false;
    window.OfficeWorld?.endMeeting?.();
  }
  ensureThread(threadId);
  const url = new URL(window.location.href);
  url.searchParams.set("thread", threadId);
  history.replaceState(null, "", url);
  state.artifacts = { plan: null, scope: null, design: null, qa: null, acVerification: null, files: null };
  state.done = new Set();
  state.interrupt = null;
  state.serverActivity = [];
  state.liveActivityEntries = [];
  state._serverActivityLen = 0;
  showApproval(null);
  await loadTasks();
  await refreshThread();
}

function showApproval(payload) {
  state.interrupt = payload;
  els.approval.hidden = !payload;
  if (!payload) {
    renderOffice();
    return;
  }
  const gate = payload.gate || "human";
  els.gateLabel.textContent = gate === "brief" ? "Briefing" : `${gate} gate`;
  els.gatePrompt.textContent =
    gate === "brief"
      ? "Confirm scope before the plan"
      : payload.prompt || "Approve to continue?";
  setApprovalButtons(gate);
  if (gate === "brief") {
    els.discussStatus.textContent = "Reply in the box below, or let the PM proceed with their assumptions.";
  }
  if (gate === "plan") {
    state.tab = "plan";
    if (payload.plan) state.artifacts.plan = payload.plan;
    els.gateLabel.textContent = "AC sign-off";
    els.gatePrompt.textContent = "Verify acceptance criteria with the PM";
    els.discussStatus.textContent =
      "Meet in the meeting room. Confirm each AC is testable, then sign off or send back for changes.";
    if (payload.scope_agreement || payload.architecture_brief) {
      state.artifacts.scope = {
        scope_agreement: payload.scope_agreement || {},
        architecture_brief: payload.architecture_brief || {},
      };
    }
    renderPlanSignoff(state.artifacts.plan, state.artifacts.scope);
  }
  if (gate === "release") {
    if (payload.test_results) state.artifacts.qa = payload.test_results;
    if (payload.ac_verification) state.artifacts.acVerification = payload.ac_verification;
    els.gatePrompt.textContent = "Release — QA tests + PM AC sign-off";
    els.discussStatus.textContent =
      payload.prompt || "Review QA results and the PM’s AC coverage check before you sign release.";
    renderReleaseReview(state.artifacts.qa, state.artifacts.acVerification);
  }
  showArtifact();
  if (gate === "brief") openBriefMeeting(payload);
  else if (gate === "plan") openPlanMeeting();
  else if (gate === "release") openReleaseMeeting();
  renderOffice();
  if (payload) {
    els.approval?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

async function refreshThread() {
  if (!state.threadId) return;
  const res = await fetch(`/api/thread/${state.threadId}`);
  if (!res.ok) return;
  const data = await res.json();
  const values = data.values || {};
  if (values.plan) state.artifacts.plan = values.plan;
  if (values.architecture_brief || values.scope_agreement || values.dialogue?.length) {
    state.artifacts.scope = {
      architecture_brief: values.architecture_brief || state.artifacts.scope?.architecture_brief,
      scope_agreement: values.scope_agreement || state.artifacts.scope?.scope_agreement,
      dialogue: values.dialogue || state.artifacts.scope?.dialogue || [],
    };
  }
  if (values.design_spec) state.artifacts.design = values.design_spec;
  if (values.test_results) state.artifacts.qa = values.test_results;
  if (values.ac_verification) state.artifacts.acVerification = values.ac_verification;
  if (data.files) state.artifacts.files = data.files;
  syncActivityFromThread(values);
  renderDeliverable({ ...data, thread_id: state.threadId });
  showArtifact();
  const live = data.live || {};
  applyLiveModels(live);
  if (live.working_agent) {
    state.working = live.working_agent;
    state.busy = Boolean(live.busy);
  }
  renderModelRoster();
  if (!["plan", "brief", "release"].includes(data.interrupt?.gate) && state.meeting) {
    state.meeting = false;
    window.OfficeWorld?.endMeeting?.();
  }
  if (
    !data.interrupt &&
    data.pending_nodes?.includes("review") &&
    data.values?.status === "awaiting_release" &&
    !live.busy &&
    !state.busy
  ) {
    const gateKey = `releaseGateOpen:${state.threadId}`;
    if (!sessionStorage.getItem(gateKey)) {
      sessionStorage.setItem(gateKey, "1");
      void fetch(`/api/thread/${encodeURIComponent(state.threadId)}/open-release-gate`, { method: "POST" });
    }
  }
  if (!data.interrupt && data.pending_nodes?.length && !live.busy && !state.busy) {
    const who = pendingAgentLabel(data.pending_nodes);
    setStatus(`Paused before ${who} — resuming or click Continue`, false);
    setCaption(`The graph is waiting for ${who} to run (this can take several minutes on a local model).`);
    void maybeAutoResumePending({ ...data, values });
  }
  if (data.interrupt) {
    if (shouldDismissStaleGateInterrupt(data.interrupt.gate)) {
      state.interrupt = null;
      state.meeting = false;
      window.OfficeWorld?.endMeeting?.();
      els.approval.hidden = true;
      renderOffice();
    } else {
      state.runStatus = "awaiting_human";
      els.runBtn.disabled = false;
      const gate = data.interrupt.gate;
      if (gate === "brief") {
        setStatus("PM needs your input before drafting the plan", false);
        setCaption("PM is in the meeting room with questions about your brief.");
      } else if (gate === "plan") {
        setStatus("Meet the PM — verify acceptance criteria before sign-off", false);
        setCaption("PM is in the meeting room to review AC with you.");
      } else {
        setStatus("PM verified AC — review and approve release", false);
        setCaption("QA passed and PM confirmed every AC is met. Your release sign-off is next.");
      }
      showApproval(data.interrupt);
    }
  } else {
    renderOffice();
  }
  scheduleLoadTasks();
}

function handleEvent(event) {
  if (event.thread_id && ["run_started", "waiting_approval", "run_finished", "error"].includes(event.type)) {
    if (!state.threadId || event.type === "waiting_approval" || event.type === "run_started") {
      ensureThread(event.thread_id);
    }
  }
  if (event.type === "tasks_updated") scheduleLoadTasks();
  if (["run_started", "waiting_approval", "run_finished", "run_stopped"].includes(event.type)) scheduleLoadTasks();
  if (event.type === "state_update") scheduleLoadTasks();
  if (state.threadId && event.thread_id && event.thread_id !== state.threadId) return;

  const names = { pm: "PM", architect: "Architect", designer: "Designer", developer: "Developer", qa: "QA" };

  if (event.type === "run_stopped") {
    state.working = null;
    state.busy = false;
    state.runStatus = "blocked";
    els.runBtn.disabled = false;
    if (els.stopBtn) els.stopBtn.disabled = true;
    setStatus("Run force-stopped", false);
    setCaption("The office was halted by supervisor. You can brief a new task or resume from a gate if one was open.");
    appendLiveActivity({
      kind: "gate",
      from: "human",
      text: "Office run force-stopped.",
    });
    window.OfficeWorld?.endMeeting?.();
    renderOffice();
    refreshThread();
    loadTasks();
  }
  if (event.type === "pending_handoff") {
    const nodes = event.nodes || [];
    appendLiveActivity({
      kind: "handoff",
      from: "system",
      text: `Paused before ${nodes.join(" → ")}.`,
    });
    if (event.thread_id) ensureThread(event.thread_id);
    void maybeAutoResumePending({
      pending_nodes: nodes,
      interrupt: null,
      live: { busy: false },
      values: state.artifacts,
    });
  }
  if (event.type === "run_started") {
    clearAutoResumeKeys(event.thread_id);
    if (event.thread_id) sessionStorage.removeItem(`releaseGateOpen:${event.thread_id}`);
    const newThread = event.thread_id && event.thread_id !== state.threadId;
    state.done = new Set();
    if (newThread) {
      state.serverActivity = [];
      state.liveActivityEntries = [];
      state._serverActivityLen = 0;
    }
    state.working = null;
    state.interrupt = null;
    state.runStatus = "running";
    state.meeting = false;
    window.OfficeWorld?.endMeeting?.();
    window.OfficeWorld?.resetPositions();
    showApproval(null);
    setLive("", false);
    setStatus("Brief received — the office is waking up", true);
    setCaption("Everyone is heading to their desks.");
    els.runBtn.disabled = true;
    if (els.stopBtn) els.stopBtn.disabled = false;
    renderOffice();
    if (event.thread_id) refreshThread();
    refreshStopButton();
  }
  if (event.type === "qa_validation") {
    const runs = event.runs || [];
    if (runs.length) {
      const passed = runs.filter((r) => r.passed).length;
      appendLiveActivity({
        kind: "validation",
        from: "qa",
        text: `Ran ${runs.length} validation command(s): ${passed} passed, ${runs.length - passed} failed.`,
      });
      const text = runs
        .map(
          (run) =>
            `${run.passed ? "PASS" : "FAIL"}: ${run.command}\n${run.stdout || ""}${run.stderr ? `\n${run.stderr}` : ""}`,
        )
        .join("\n\n---\n\n");
      setLive(text, false);
      els.feedAgent.textContent = "QA";
    }
  }
  if (event.type === "agent_started") {
    state.working = event.agent;
    appendLiveActivity({
      kind: "work",
      from: event.agent,
      text: `${names[event.agent] || event.agent} started work.`,
    });
    setLive("", false);
    setStatus(`${names[event.agent] || event.agent} is at their desk`, true);
    setCaption(`${names[event.agent] || event.agent} picked up the assignment.`);
    renderOffice();
  }
  if (event.type === "model_selected") {
    if (event.agent && event.model) {
      state.modelsInUse[event.agent] = event.model;
      state.working = event.agent;
    }
    setCaption(`${names[event.agent] || event.agent} is using ${event.model}.`);
    renderModelRoster();
    syncOfficeWorld();
  }
  if (event.type === "token" && event.text) {
    const current = els.live.classList.contains("empty") ? "" : els.live.textContent;
    setLive(current + event.text, true);
  }
  if (event.type === "handoff") {
    const from = event.from;
    const to = event.to;
    const isReturn = event.direction === "return";
    const toResolved = to || (from === "pm" ? "human" : "");
    appendLiveActivity({
      kind: "handoff",
      from,
      to: toResolved,
      direction: event.direction,
      text:
        event.reason ||
        (isReturn ? "Sent work back for revision." : "Passed work to the next role."),
    });
    const toName = toResolved === "human" ? "You" : names[toResolved] || toResolved || "next role";
    setCaption(
      isReturn
        ? `${names[from] || from} is walking back to ${toName} — scope needs fixing.`
        : `${names[from] || from} is walking over to pass the work to ${toName}.`,
    );
    renderOffice();
    scheduleLoadTasks();
    if (from && toResolved && window.OfficeWorld) {
      window.OfficeWorld.passWork(from, toResolved, { direction: event.direction, reason: event.reason }).then(() => {
        setCaption(isReturn ? `${toName} received the scope issue.` : `${toName} received the handoff.`);
        syncOfficeWorld();
      });
    }
  }
  if (event.type === "agent_finished") {
    if (event.agent) {
      state.done.add(event.agent);
      if (state.modelsInUse[event.agent]) {
        state.modelsLastUsed[event.agent] = state.modelsInUse[event.agent];
      }
    }
    state.working = null;
    renderOffice();
    refreshThread();
    scheduleLoadTasks();
  }
  if (event.type === "waiting_approval") {
    const gate = (event.payload || event).gate;
    if (shouldDismissStaleGateInterrupt(gate)) {
      window.OfficeWorld?.endMeeting?.();
      return;
    }
    state.working = null;
    state.busy = false;
    state.runStatus = "awaiting_human";
    els.runBtn.disabled = false;
    els.approve.disabled = false;
    els.reject.disabled = false;
    const gateFrom = { brief: "pm", plan: "pm", release: "pm" }[gate] || "pm";
    if (gate === "release" && state.threadId) {
      sessionStorage.removeItem(`releaseGateOpen:${state.threadId}`);
    }
    appendLiveActivity({
      kind: "gate",
      from: gateFrom,
      to: "human",
      text: `Waiting for you (${gate} gate).`,
    });
    if (gate === "brief") {
      setStatus("PM needs your input before drafting the plan", false);
      setCaption("PM is walking into the meeting with questions.");
    } else if (gate === "plan") {
      setStatus("Verify acceptance criteria with the PM", false);
      setCaption("PM is walking into the meeting for AC sign-off.");
    } else {
      setStatus("Your turn — review for release", false);
      setCaption("QA and PM AC review are done — release needs your signature.");
    }
    showApproval(event.payload || event);
    refreshThread();
    loadMeta();
    loadTasks();
  }
  if (event.type === "run_finished") {
    state.working = null;
    state.busy = false;
    state.runStatus = event.status || "done";
    els.runBtn.disabled = false;
    els.approve.disabled = false;
    els.reject.disabled = false;
    if (event.message) {
      setStatus(event.message, false);
    } else {
      setStatus(
        event.status === "released"
          ? "Released — the office is closing for this task."
          : `Run finished (${event.status || "done"})`,
        false,
      );
    }
    setCaption(
      event.status === "released"
        ? "Shipped — use the Output panel or Open in browser to view the result."
        : "This run is done.",
    );
    renderOffice();
    refreshThread();
    loadMeta();
    loadTasks();
  }
  if (event.type === "error") {
    state.working = null;
    els.runBtn.disabled = false;
    setStatus(`Error: ${event.message}`, false);
    setCaption("Something went wrong on the floor.");
    renderOffice();
  }
}

function connectStream() {
  const source = new EventSource("/api/stream");
  source.onmessage = (message) => handleEvent(JSON.parse(message.data));
}

els.stopBtn?.addEventListener("click", () => forceStopOffice());

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  els.runBtn.disabled = true;
  setStatus("Sending the brief…", true);
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task: els.task.value }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    ensureThread(data.thread_id);
    const url = new URL(window.location.href);
    url.searchParams.set("thread", data.thread_id);
    history.replaceState(null, "", url);
    loadTasks();
    state.artifacts = { plan: null, scope: null, design: null, qa: null, acVerification: null, files: null };
    state.done = new Set();
    renderDeliverable(null);
    showArtifact();
  } catch (err) {
    els.runBtn.disabled = false;
    setStatus(`Could not start: ${err.message}`, false);
  }
});

async function decide(approved) {
  if (!state.threadId) {
    setStatus("No active thread — run a task first.", false);
    return;
  }
  const gate = state.interrupt?.gate;
  let feedback = els.feedback.value.trim();
  if (gate === "brief" && !approved) {
    approved = true;
    if (!feedback) feedback = "Proceed with your stated assumptions.";
  }
  if (!approved && !feedback) {
    setStatus("Add feedback before rejecting.", false);
    return;
  }
  if (!gate) {
    await refreshThread();
    if (!state.interrupt?.gate) {
      setStatus("No gate is open on this thread — use Continue on blocked/revising tasks.", false);
      return;
    }
    return decide(approved);
  }
  els.approve.disabled = true;
  els.reject.disabled = true;
  if (gate === "plan" || gate === "brief" || gate === "release") {
    state.meeting = false;
    window.OfficeWorld?.endMeeting?.();
  }
  setStatus(
    approved
      ? "You signed off — team is resuming…"
      : gate === "release"
        ? "Sending back to PM for triage…"
        : "Sending revisions to the team…",
    true,
  );
  setCaption(
    approved
      ? "You approved. The next person is heading to their desk."
      : gate === "release"
        ? "PM will revise the plan and route Developer → QA again (no new plan gate)."
        : "You sent revisions back to the team.",
  );
  try {
    const res = await fetch("/api/decide", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: state.threadId, approved, feedback }),
    });
    if (!res.ok) {
      const detail = await res.text();
      const label = approved ? "approve" : "send back";
      setStatus(`Could not ${label}: ${detail}`, false);
      if (detail.includes("still running")) {
        setCaption("An agent is still working — wait a few seconds or Force stop, then try again.");
      } else if (detail.includes("Nothing is waiting")) {
        setCaption("This gate already closed — check the office log or use Continue on the task.");
      }
      await refreshThread();
      els.approve.disabled = false;
      els.reject.disabled = false;
      return;
    }
    els.feedback.value = "";
    state.interrupt = null;
    showApproval(null);
    state.busy = true;
    state.runStatus = "running";
    els.runBtn.disabled = true;
    if (els.stopBtn) els.stopBtn.disabled = false;
    renderOffice();
    await refreshThread();
    loadTasks();
    if (approved && gate === "release") {
      state.runStatus = "released";
      state.meeting = false;
      window.OfficeWorld?.endMeeting?.();
      setStatus("Released — this task is complete.", false);
      setCaption("Shipped. Check Output or Open in browser for the build.");
      renderOffice();
    }
  } catch (err) {
    setStatus(`Could not approve: ${err.message}`, false);
    await refreshThread();
    els.approve.disabled = false;
    els.reject.disabled = false;
  }
}

els.taskList?.addEventListener("click", (event) => {
  const groupToggle = event.target.closest(".task-group-toggle");
  if (groupToggle) {
    event.preventDefault();
    event.stopPropagation();
    const group = groupToggle.closest(".task-group");
    if (!group) return;
    const key = group.dataset.group;
    const open = group.classList.contains("collapsed");
    group.classList.toggle("collapsed", !open);
    groupToggle.setAttribute("aria-expanded", String(open));
    if (key) setTaskGroupOpen(key, open);
    return;
  }
  const continueBtn = event.target.closest("[data-continue-thread]");
  if (continueBtn) {
    event.preventDefault();
    event.stopPropagation();
    continueTask(continueBtn.dataset.continueThread);
    return;
  }
  const folderBtn = event.target.closest("[data-open-folder]");
  if (folderBtn) {
    event.preventDefault();
    event.stopPropagation();
    openOutputFolder(folderBtn.dataset.openFolder);
    return;
  }
  const button = event.target.closest(".task-item");
  if (!button) return;
  openTask(button.dataset.thread);
});
els.deliverableOpenFolder?.addEventListener("click", () => openOutputFolder());
els.deliverablePath?.addEventListener("click", () => openOutputFolder());
els.approve.addEventListener("click", () => decide(true));
els.reject.addEventListener("click", () => decide(false));
document.querySelectorAll(".tabs button").forEach((button) => {
  button.addEventListener("click", () => {
    state.tab = button.dataset.tab;
    document.querySelectorAll(".tabs button").forEach((item) => item.classList.toggle("active", item === button));
    showArtifact();
  });
});

document.querySelectorAll(".activity-scope-btn").forEach((btn) => {
  btn.addEventListener("click", () => setActivityScope(btn.dataset.scope));
});
setActivityScope(state.activityScope);

renderOffice();
connectStream();
async function loadMeta() {
  try {
    const res = await fetch("/api/meta");
    const data = await res.json();
    els.model.textContent = data.default
      ? `${data.default.provider}/${data.default.model}`
      : data.model || "models";
    syncAgentModelsFromMeta(data);
    state.modelsConfigPath = data.models_config || "models.yaml";
    const officePathEl = document.getElementById("office-config-path");
    if (officePathEl) officePathEl.textContent = data.office_config || "office.yaml";
    state.lessonCount = data.memory_lessons || 0;
    state.officeConfigPath = data.office_config || "office.yaml";
    applyOfficeBranding(data.office);
    const missing = AGENTS.filter((a) => !(data.agents || {})[a.id]);
    if (missing.length) {
      console.warn(
        `Roster missing ${missing.map((a) => a.id).join(", ")} — restart UI: python main.py ui`,
      );
    }
    if (!Object.keys(data.agents || {}).length) {
      console.warn("Model roster empty — restart: python main.py ui");
    }
    renderModelRoster();
    renderOffice();
  } catch (err) {
    console.error("Failed to load /api/meta", err);
  }
}
loadMeta();

const params = new URLSearchParams(window.location.search);
const initialThread = params.get("thread") || localStorage.getItem(STORAGE_KEY);
if (initialThread) {
  ensureThread(initialThread);
  refreshThread();
}
loadTasks();
refreshStopButton();
setInterval(() => {
  if (state.threadId) refreshThread();
  loadTasks();
}, 4000);
