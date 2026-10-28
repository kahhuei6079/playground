/* Office floor: rooms, desks, walking actors, idle wandering, interactions */
(function () {
  /* Chair (x,y) + monitor center (sx,sy) on office-aligned.jpg — flash overlay anchors on sx/sy. */
  const DESKS = [
    { id: "pm", x: 30.5, y: 37.5, sx: 30.5, sy: 24.85, role: "pm" },
    { id: "architect", x: 42, y: 37.5, sx: 43.4, sy: 24.85, role: "architect" },
    { id: "designer", x: 54, y: 37.5, sx: 54, sy: 24.85, role: "designer" },
    { id: "developer", x: 30.5, y: 60.9, sx: 30.35, sy: 49.05, role: "developer" },
    { id: "qa", x: 54, y: 60.9, sx: 54.5, sy: 49.05, role: "qa" },
    { id: "human", x: 85.5, y: 26.8, sx: 86.1, sy: 21.15, role: "human", room: "supervisor" },
  ];

  const EXTRA_DESKS = [];

  const NAMES = {
    pm: "PM",
    architect: "Architect",
    designer: "Designer",
    developer: "Developer",
    qa: "QA",
    human: "Supervisor",
  };

  const WANDER_AGENTS = ["human", "pm", "architect", "designer", "developer", "qa"];

  const SUPERVISOR_WAYPOINTS = [
    { x: 70, y: 28, bubble: "Coffee run." },
    { x: 83.5, y: 37, bubble: "Back at my desk." },
  ];

  const WAYPOINTS = [
    { id: "pantry", x: 12, y: 32, bubble: "In the pantry", label: "pantry" },
    { id: "pantry-snack", x: 14, y: 36, bubble: "Coffee counter", label: "pantry" },
    { id: "cooler", x: 16, y: 30, bubble: "Water cooler", label: "water cooler" },
    { id: "hall", x: 48, y: 47, bubble: "Between the rows", label: "hallway" },
    { id: "lounge", x: 50, y: 78, bubble: "Meeting room", label: "lounge" },
    { id: "huddle", x: 50, y: 76, bubble: "At the meeting table", label: "huddle area" },
    { id: "supervisor", x: 85, y: 45, bubble: "Supervisor room", label: "window" },
    { id: "intern", x: 66, y: 47, bubble: "By the back desks", label: "intern bay" },
  ];

  const HOTSPOTS = {
    pantry: { x: 12, y: 22, label: "Pantry", summon: "pantry" },
    supervisor: { x: 86, y: 22, label: "Lead office", summon: "window" },
    cooler: { x: 48, y: 42, label: "Lounge", summon: "cooler" },
    couch: { x: 48, y: 42, label: "Lounge", summon: "lounge" },
    intern: { x: 90, y: 90, label: "Growth pod", summon: "intern" },
    terminal: { x: 60, y: 78, label: "Dev desk", summon: "huddle" },
  };

  const POKE_LINES = {
    pm: [
      "One sec — updating the roadmap.",
      "Got a brief for me?",
      "Scope check!",
      "Let's timebox this slice.",
      "Who's the DRI on that?",
      "I'll write it in the plan doc.",
      "Acceptance criteria or vibes?",
      "We can ship a thin slice first.",
      "Blocking? I'll chase the owner.",
      "Retro after this lands, deal?",
      "Stakeholders want a demo Friday.",
      "I'll keep the scope honest.",
    ],
    architect: [
      "Boxes and arrows time.",
      "UI or API-only?",
      "Let's align delivery shape.",
      "Where does state live?",
      "I'd split that service boundary.",
      "Static site or server render?",
      "We should diagram the data flow.",
      "Non-goals are important too.",
      "That's a cross-cutting concern.",
      "Have we sized the integration?",
      "I'll flag risks for the PM.",
      "One repo or two? Let's decide.",
    ],
    designer: [
      "Pulling up Figma… jk, it's pixels.",
      "Color palette thoughts?",
      "Need a mock?",
      "Mobile-first or desktop-first?",
      "Contrast check passed — barely.",
      "I'll tighten the spacing grid.",
      "Empty states need love too.",
      "This button wants a hover state.",
      "Accessibility isn't optional here.",
      "I'll export assets after sign-off.",
      "Typography hierarchy feels off.",
      "Quick wireframe in five?",
    ],
    developer: [
      "Compiling… always compiling.",
      "Found a bug or a feature?",
      "Keyboard is warm.",
      "One more commit, I swear.",
      "Tests are green locally…",
      "I'll add a guard for that edge case.",
      "Refactor later, ship now?",
      "Merge conflict déjà vu.",
      "Need the API contract clarified.",
      "I'll log it in the workspace.",
      "Works on my machine™.",
      "Lint caught something — fixing.",
    ],
    qa: [
      "I brought the checklist.",
      "Repro steps, please.",
      "Edge cases are my love language.",
      "What happens on empty input?",
      "I'll run the validation suite.",
      "Regression risk on that path.",
      "Mobile viewport is on my list.",
      "Screenshot or it didn't happen.",
      "Flaky test or real bug?",
      "AC four still ambiguous.",
      "I'll file a clear failure note.",
      "Ship when the bar is green.",
    ],
    human: [
      "You rang?",
      "Approval desk is open.",
      "Coffee's in the pantry.",
      "Sign-off or send-back?",
      "I'll read the plan slice.",
      "Keep the thread moving.",
      "Force stop is the red button.",
      "Brief them clearly — I'll wait.",
      "Show me the output when it's ready.",
      "I trust the process… mostly.",
      "Meeting room's that way.",
      "Don't let scope sneak in.",
    ],
  };

  const GOSSIP = [
    ["Did you see the latest deploy?", "Fingers crossed for green CI."],
    ["This hallway needs more plants.", "Agreed. And snacks."],
    ["Scope creep is a lifestyle.", "PM will save us… right?"],
    ["Local model's thinking again.", "Give it two minutes. Or ten."],
    ["Who broke the build?", "It was me. Sorry."],
    ["New acceptance criterion dropped.", "Of course it did."],
    ["The pantry coffee is decent today.", "Bold claim."],
    ["Designer nailed the empty state.", "Finally someone did."],
    ["Architect drew another diagram.", "I framed it mentally."],
    ["QA found a corner case.", "That's their superpower."],
    ["PM wants a demo tomorrow.", "We'll thin the slice."],
    ["Checkpoint saved us.", "SQLite for the win."],
    ["I walked 10k steps in this office.", "Pixel floors count, right?"],
    ["Release gate again?", "Means we're close."],
    ["Human rejected my PR.", "Feedback was fair though."],
    ["Ollama warmed up yet?", "Fans say yes."],
    ["Meeting room or async?", "Async. Always async."],
    ["Tab or spaces?", "Don't start."],
    ["We need more desk plants.", "And fewer meetings."],
    ["Handoff parcel looked heavy.", "Scope always is."],
    ["Developer shipped a fix fast.", "QA will verify."],
    ["Plan gate was painless.", "Rare but nice."],
    ["Memory file grew again.", "Lessons learned stick."],
    ["Is it Friday yet?", "Check the sprint board."],
    ["Water cooler's the real standup.", "Truth serum included."],
    ["I'll ping you after standup.", "We don't do standups."],
    ["Documentation drift is real.", "SOUL.md remembers."],
    ["Flaky Wi‑Fi in the pantry.", "Use ethernet at your desk."],
    ["Someone force-stopped the run.", "Supervisor has that power."],
    ["AC signed — build starts.", "Music to my ears."],
  ];

  /** Seconds-ish ranges; lower waits / higher moveOdds = livelier floor */
  const PERSONA = {
    human: { deskWait: [8, 16], linger: [5, 10], moveOdds: 0.42, homeOdds: 0.55, walkSec: 1.55 },
    pm: { deskWait: [6, 14], linger: [4, 9], moveOdds: 0.55, homeOdds: 0.5, walkSec: 1.35 },
    architect: { deskWait: [7, 14], linger: [4, 8], moveOdds: 0.5, homeOdds: 0.48, walkSec: 1.35 },
    designer: { deskWait: [5, 12], linger: [3, 8], moveOdds: 0.62, homeOdds: 0.42, walkSec: 1.25 },
    developer: { deskWait: [6, 13], linger: [3, 7], moveOdds: 0.58, homeOdds: 0.4, walkSec: 1.2 },
    qa: { deskWait: [5, 12], linger: [4, 8], moveOdds: 0.6, homeOdds: 0.45, walkSec: 1.3 },
  };

  const SUMMON_AGENTS = ["pm", "architect", "designer", "developer", "qa"];
  const MAX_AWAY_FROM_DESK = 3;
  const FIDGET_CLASSES = [
    "fidget-stretch",
    "fidget-look",
    "fidget-type",
    "fidget-nod",
    "fidget-bounce",
    "fidget-wave",
  ];
  const IDLE_THOUGHTS = {
    pm: ["Checking the board…", "Thin slice first.", "Notes for later."],
    architect: ["Sketching boundaries…", "Where does state live?", "Hmm, coupling."],
    designer: ["Spacing check…", "Needs more air.", "Hover state?"],
    developer: ["One more commit…", "Tests locally…", "Lint clean?"],
    qa: ["Edge case list…", "Empty input?", "Regression watch."],
    human: ["Reading the log…", "Coffee soon.", "Approval desk open."],
  };

  const awayFromDesk = new Set();

  function persona(id) {
    return PERSONA[id] || PERSONA.pm;
  }

  function randRange([lo, hi]) {
    return lo + Math.random() * (hi - lo);
  }

  function atHome(id) {
    const node = actorNodes[id];
    if (!node) return true;
    const h = home(id);
    const pos = parsePos(node);
    return Math.abs(pos.x - h.x) < 2.5 && Math.abs(pos.y - h.y) < 2.5;
  }

  let floorEl = null;
  let actorsEl = null;
  let effectsEl = null;
  let parcelEl = null;
  const actorNodes = {};
  const lastModes = {};
  const wanderGen = {};
  const duty = {};
  let walkQueue = Promise.resolve();
  let handoffActive = false;
  let meetingActive = false;
  let meetingTickTimer = null;
  const MEETING_PM = { x: 44, y: 74 };
  const MEETING_HUMAN = { x: 56, y: 78 };
  let lifeStarted = false;
  let interactionsBound = false;
  let onCaption = null;
  let selectedId = null;
  let gossipTimer = null;

  function home(id) {
    return DESKS.find((d) => d.id === id) || DESKS[0];
  }

  function parsePos(node) {
    return {
      x: parseFloat(node.style.left) || 0,
      y: parseFloat(node.style.top) || 0,
    };
  }

  function setPosition(node, x, y, animate, durationSec = 1.55) {
    node.style.transition = animate
      ? `left ${durationSec}s cubic-bezier(0.35, 0.05, 0.2, 1), top ${durationSec}s cubic-bezier(0.35, 0.05, 0.2, 1)`
      : "none";
    node.style.left = `${x}%`;
    node.style.top = `${y}%`;
  }

  function setFacing(node, fromX, toX) {
    const sprite = node.querySelector(".actor-sprite");
    if (!sprite) return;
    const left = toX < fromX;
    sprite.classList.toggle("facing-left", left);
    sprite.classList.toggle("facing-right", !left);
  }

  function wait(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  function waitTransition(node, durationSec = 1.55) {
    return new Promise((resolve) => {
      const done = () => {
        node.removeEventListener("transitionend", done);
        resolve();
      };
      node.addEventListener("transitionend", done, { once: true });
      setTimeout(resolve, durationSec * 1000 + 120);
    });
  }

  function ripple(x, y) {
    if (!effectsEl) return;
    const dot = document.createElement("div");
    dot.className = "floor-ripple";
    dot.style.left = `${x}%`;
    dot.style.top = `${y}%`;
    effectsEl.appendChild(dot);
    setTimeout(() => dot.remove(), 800);
  }

  function footDust(node) {
    if (!effectsEl) return;
    const pos = parsePos(node);
    const puff = document.createElement("div");
    puff.className = "walk-puff";
    puff.style.left = `${pos.x}%`;
    puff.style.top = `${pos.y + 2}%`;
    effectsEl.appendChild(puff);
    setTimeout(() => puff.remove(), 500);
  }

  function pauseWander(id) {
    duty[id] = "desk";
    wanderGen[id] = (wanderGen[id] || 0) + 1;
    awayFromDesk.delete(id);
    const node = actorNodes[id];
    if (node) {
      clearFidget(node);
      node.classList.remove("wandering", "at-desk", "chatting");
    }
  }

  function pauseAllWander() {
    WANDER_AGENTS.forEach(pauseWander);
  }

  async function walkActorTo(id, x, y, { wandering = false } = {}) {
    const node = actorNodes[id];
    if (!node) return;
    const dur = persona(id).walkSec;
    const from = parsePos(node);
    const leavingDesk = wandering && atHome(id);
    if (leavingDesk) awayFromDesk.add(id);
    node.classList.remove("at-desk");
    node.classList.add("walking");
    if (wandering) node.classList.add("wandering");
    if (window.renderRoleSprite) {
      node.querySelector(".actor-sprite").innerHTML = window.renderRoleSprite(id, { pose: "walk" });
    }
    setFacing(node, from.x, x);
    let steps = 0;
    const step = setInterval(() => {
      steps += 1;
      if (steps % 2 === 0) footDust(node);
    }, 520);
    setPosition(node, x, y, true, dur);
    await waitTransition(node, dur);
    clearInterval(step);
    node.classList.remove("walking");
    if (!wandering) node.classList.remove("wandering");
    if (wandering && atHome(id)) awayFromDesk.delete(id);
    updateTeamSeated(id);
    updateSupervisorSeated(id);
  }

  function agentAtHomeDesk(id) {
    const node = actorNodes[id];
    if (!node || node.classList.contains("walking")) return false;
    const h = home(id);
    const pos = parsePos(node);
    return Math.abs(pos.x - h.x) < 2.5 && Math.abs(pos.y - h.y) < 2.5;
  }

  function updateSupervisorSeated(id) {
    if (id !== "human") return;
    const node = actorNodes[id];
    if (!node) return;
    const atDesk = agentAtHomeDesk(id);
    node.classList.toggle("seated", atDesk);
    node.classList.toggle("at-desk", atDesk);
  }

  function updateTeamSeated(id) {
    if (id === "human") {
      updateSupervisorSeated(id);
      return;
    }
    const node = actorNodes[id];
    if (!node) return;
    const atDesk = agentAtHomeDesk(id);
    if (lastModes[id] === "working" && atDesk) {
      node.classList.add("seated", "at-desk");
    }
  }

  /** Supervisor stays at the window desk — no floor wandering like the team. */
  function stayAtSupervisorDesk() {
    pauseWander("human");
    const node = actorNodes.human;
    if (!node || node.classList.contains("walking") || handoffActive || meetingActive) return;
    const h = home("human");
    const pos = parsePos(node);
    const atHome = Math.abs(pos.x - h.x) < 2.5 && Math.abs(pos.y - h.y) < 2.5;
    if (atHome) {
      node.classList.add("seated", "at-desk");
      updateSupervisorSeated("human");
      return;
    }
    goHome("human", true).then(() => {
      node.classList.add("seated", "at-desk");
      updateSupervisorSeated("human");
    });
  }

  function wanderPoint(id) {
    if (id === "human") {
      return SUPERVISOR_WAYPOINTS[Math.floor(Math.random() * SUPERVISOR_WAYPOINTS.length)];
    }
    const wp = WAYPOINTS[Math.floor(Math.random() * WAYPOINTS.length)];
    return { x: wp.x, y: wp.y - 5, bubble: wp.bubble };
  }

  function clearFidget(node) {
    if (!node) return;
    FIDGET_CLASSES.forEach((c) => node.classList.remove(c));
    node.classList.remove("chatting");
  }

  function playFidget(node) {
    if (!node || node.classList.contains("walking")) return;
    clearFidget(node);
    const cls = FIDGET_CLASSES[Math.floor(Math.random() * FIDGET_CLASSES.length)];
    node.classList.add(cls);
    setTimeout(() => node.classList.remove(cls), 1100);
  }

  async function deskIdlePeriod(id, seconds, gen) {
    const node = actorNodes[id];
    if (!node) return;
    const end = Date.now() + seconds * 1000;
    while (Date.now() < end && duty[id] === "roam" && wanderGen[id] === gen && !handoffActive) {
      playFidget(node);
      if (Math.random() < 0.28) {
        const thoughts = IDLE_THOUGHTS[id] || IDLE_THOUGHTS.pm;
        const bubbleEl = node.querySelector(".actor-bubble");
        const line = thoughts[Math.floor(Math.random() * thoughts.length)];
        if (bubbleEl) {
          bubbleEl.textContent = line;
          node.classList.add("chatting");
          await wait(1600 + Math.random() * 900);
          if (duty[id] !== "roam" || wanderGen[id] !== gen) break;
          bubbleEl.textContent = "";
          node.classList.remove("chatting");
        }
      }
      const slice = Math.min(2200 + Math.random() * 2800, Math.max(400, end - Date.now()));
      await wait(slice);
    }
    clearFidget(node);
  }

  function resumeWander(id) {
    if (handoffActive) return;
    const mode = lastModes[id];
    if (id === "human" && mode === "human-needed") return;
    if (mode !== "idle" && mode !== "done") return;
    if (duty[id] === "roam") return;
    duty[id] = "roam";
    const gen = (wanderGen[id] = (wanderGen[id] || 0) + 1);
    const node = actorNodes[id];
    if (!node) return;

    (async () => {
      const p = persona(id);
      while (duty[id] === "roam" && wanderGen[id] === gen && !handoffActive) {
        const h = home(id);
        if (!atHome(id) && Math.random() < 0.55) {
          await walkActorTo(id, h.x, h.y, { wandering: true });
        }
        node.classList.add("at-desk");
        if (id === "human") node.classList.add("seated");
        updateSupervisorSeated(id);
        await deskIdlePeriod(id, randRange(p.deskWait), gen);
        if (duty[id] !== "roam" || wanderGen[id] !== gen) break;

        clearFidget(node);
        node.classList.remove("at-desk", "chatting");
        if (Math.random() > p.moveOdds) continue;
        if (awayFromDesk.size >= MAX_AWAY_FROM_DESK && !awayFromDesk.has(id)) {
          await deskIdlePeriod(id, 4 + Math.random() * 5, gen);
          continue;
        }

        const wp = wanderPoint(id);
        node.classList.remove("seated");
        awayFromDesk.add(id);
        await walkActorTo(id, wp.x, wp.y, { wandering: true });
        updateSupervisorSeated(id);
        if (duty[id] !== "roam" || wanderGen[id] !== gen) break;

        const bubbleEl = node.querySelector(".actor-bubble");
        if (bubbleEl) bubbleEl.textContent = wp.bubble;
        node.classList.add("chatting");
        await wait(randRange(p.linger) * 1000);
        if (duty[id] !== "roam" || wanderGen[id] !== gen) break;

        if (Math.random() < p.homeOdds) {
          await walkActorTo(id, h.x, h.y, { wandering: true });
          awayFromDesk.delete(id);
          updateSupervisorSeated(id);
        }
        if (bubbleEl && (lastModes[id] === "idle" || lastModes[id] === "done")) bubbleEl.textContent = "";
        node.classList.remove("chatting");
      }
      awayFromDesk.delete(id);
      clearFidget(node);
      node?.classList.remove("wandering", "walking", "at-desk", "chatting");
      updateSupervisorSeated(id);
    })();
  }

  function resumeIdleRoamers() {
    if (handoffActive) return;
    WANDER_AGENTS.forEach((id, i) => {
      setTimeout(() => resumeWander(id), i * 800 + Math.random() * 1200);
    });
  }

  async function goHome(id, animate) {
    const h = home(id);
    pauseWander(id);
    if (!animate) {
      const node = actorNodes[id];
      if (node) setPosition(node, h.x, h.y, false);
      return;
    }
    await walkActorTo(id, h.x, h.y);
  }

  function nearestIdleAgent(x, y) {
    let best = null;
    let bestD = Infinity;
    SUMMON_AGENTS.forEach((id) => {
      const mode = lastModes[id];
      if (mode !== "idle" && mode !== "done") return;
      if (lastModes[id] === "working") return;
      const node = actorNodes[id];
      if (!node) return;
      const pos = parsePos(node);
      const d = (pos.x - x) ** 2 + (pos.y - y) ** 2;
      if (d < bestD) {
        bestD = d;
        best = id;
      }
    });
    return best;
  }

  function pickLine(id) {
    const lines = POKE_LINES[id] || ["Hey!"];
    return lines[Math.floor(Math.random() * lines.length)];
  }

  function setBubbleText(el, text) {
    if (!el) return;
    const t = text == null ? "" : String(text);
    el.textContent = t;
    el.title = t;
  }

  function deskMarkup(d, { agent = false } = {}) {
    const classes = [
      "role-desk",
      agent && d.room === "supervisor" ? "desk-supervisor" : "",
      agent ? "agent-desk" : "decor-desk",
    ]
      .filter(Boolean)
      .join(" ");
    const dataDesk = agent ? `data-desk="${d.id}"` : "";
    const role = d.role || d.id || "pm";
    const hasMonitorAnchor = d.sx != null && d.sy != null;
    const anchorX = hasMonitorAnchor ? d.sx : d.x;
    const anchorY = hasMonitorAnchor ? d.sy : d.y;
    const myPct = hasMonitorAnchor ? (d.myPct ?? 0) : (d.myPct ?? 8.5);
    const mxPct = d.mxPct ?? 0;
    return `
      <div class="${classes} bay-${role}" ${dataDesk} style="left:${anchorX}%;top:${anchorY}%;--my-pct:${myPct};--mx-pct:${mxPct}">
        <div class="ws">
          <div class="ws-screen"><i></i></div>
          <div class="ws-neck"></div>
          <div class="ws-top"><i class="ws-kb"></i><i class="ws-mug"></i></div>
          <div class="ws-shadow"></div>
          <div class="ws-chair"></div>
        </div>
        ${d.name ? `<div class="desk-name">${d.name}</div>` : ""}
      </div>`;
  }

  function buildRoomsHtml() {
    return `
      <div class="room-hits">
        <button type="button" class="room-hit hit-pantry office-hotspot" data-hotspot="pantry" title="Pantry"></button>
        <button type="button" class="room-hit hit-meet office-hotspot" data-hotspot="cooler" title="Meeting room"></button>
        <button type="button" class="room-hit hit-super office-hotspot" data-hotspot="supervisor" title="Supervisor room"></button>
      </div>
      <div class="office-effects" aria-hidden="true"></div>
      <div class="office-toast" id="office-toast" hidden></div>
    `;
  }

  function showToast(text) {
    const toast = floorEl?.querySelector("#office-toast");
    if (!toast) return;
    toast.textContent = text;
    toast.hidden = false;
    toast.classList.remove("show");
    void toast.offsetWidth;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => {
        toast.hidden = true;
      }, 300);
    }, 2200);
  }

  async function pokeAgent(id) {
    const node = actorNodes[id];
    if (!node) return;
    selectedId = id;
    Object.values(actorNodes).forEach((n) => n.classList.toggle("selected", n.dataset.id === id));
    node.classList.add("poked");
    const bubbleEl = node.querySelector(".actor-bubble");
    const line = pickLine(id);
    if (bubbleEl) bubbleEl.textContent = line;
    showToast(`${NAMES[id] || id}: ${line}`);
    onCaption?.(`${NAMES[id] || id} — ${line}`);
    ripple(parsePos(node).x, parsePos(node).y);
    if (window.renderRoleSprite) {
      node.querySelector(".actor-sprite").innerHTML = window.renderRoleSprite(id, {
        pose: id === "human" ? "work" : "idle",
      });
    }
    setTimeout(() => node.classList.remove("poked"), 600);

    if (id === "human" && (lastModes[id] === "idle" || lastModes[id] === "done") && Math.random() < 0.25) {
      pauseWander(id);
      const wp = wanderPoint("human");
      await walkActorTo("human", wp.x, wp.y);
      if (bubbleEl) bubbleEl.textContent = wp.bubble || line;
      await wait(2500);
      resumeWander(id);
      return;
    }
    if (id !== "human" && (lastModes[id] === "idle" || lastModes[id] === "done") && Math.random() < 0.12) {
      pauseWander(id);
      const supNode = actorNodes.human;
      const supPos = supNode ? parsePos(supNode) : home("human");
      await walkActorTo(id, supPos.x - 6, supPos.y + 5);
      if (bubbleEl) bubbleEl.textContent = "Quick sync with supervisor?";
      await wait(1500);
      await goHome(id, true);
      resumeWander(id);
    }
  }

  async function summonToHotspot(key) {
    const spot = HOTSPOTS[key];
    if (!spot) return;
    ripple(spot.x, spot.y);
    floorEl.querySelector(`[data-hotspot="${key}"]`)?.classList.add("hotspot-active");
    setTimeout(() => floorEl.querySelector(`[data-hotspot="${key}"]`)?.classList.remove("hotspot-active"), 600);

    const wp = WAYPOINTS.find((w) => w.id === spot.summon) || WAYPOINTS[0];
    const agent = nearestIdleAgent(wp.x, wp.y);
    if (!agent) {
      showToast("Everyone is heads-down on a task.");
      onCaption?.("No idle agents to send — the floor is busy.");
      return;
    }
    pauseWander(agent);
    onCaption?.(`Calling ${NAMES[agent]} to the ${spot.label}…`);
    await walkActorTo(agent, wp.x, wp.y - 5);
    const bubbleEl = actorNodes[agent]?.querySelector(".actor-bubble");
    if (bubbleEl) bubbleEl.textContent = `At the ${spot.label}`;
    showToast(`${NAMES[agent]} → ${spot.label}`);
    await wait(2200);
    if (bubbleEl) bubbleEl.textContent = "";
    resumeWander(agent);
  }

  async function maybeCoolerGossip() {
    if (handoffActive || document.hidden) return;
    if (Math.random() > 0.7) return;
    const idle = WANDER_AGENTS.filter((id) => lastModes[id] === "idle" || lastModes[id] === "done");
    if (idle.length < 2) return;
    const a = idle[Math.floor(Math.random() * idle.length)];
    let b = idle[Math.floor(Math.random() * idle.length)];
    if (b === a) b = idle.find((x) => x !== a);
    if (!b) return;

    const wp = WAYPOINTS.find((w) => w.id === "cooler");
    pauseWander(a);
    pauseWander(b);
    onCaption?.(`${NAMES[a]} and ${NAMES[b]} met at the water cooler.`);
    await Promise.all([
      walkActorTo(a, wp.x - 3, wp.y - 4),
      walkActorTo(b, wp.x + 3, wp.y - 4),
    ]);
    const lines = GOSSIP[Math.floor(Math.random() * GOSSIP.length)];
    const ba = actorNodes[a]?.querySelector(".actor-bubble");
    const bb = actorNodes[b]?.querySelector(".actor-bubble");
    if (ba) ba.textContent = lines[0];
    if (bb) bb.textContent = lines[1];
    floorEl.querySelector('[data-hotspot="cooler"]')?.classList.add("hotspot-active");
    await wait(3200);
    if (ba) ba.textContent = "";
    if (bb) bb.textContent = "";
    floorEl.querySelector('[data-hotspot="cooler"]')?.classList.remove("hotspot-active");
    resumeWander(a);
    resumeWander(b);
  }

  function setupInteractions() {
    if (interactionsBound || !floorEl) return;
    interactionsBound = true;

    floorEl.querySelectorAll(".office-hotspot").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        summonToHotspot(el.dataset.hotspot);
      });
    });

    floorEl.addEventListener("click", (e) => {
      if (e.target.closest(".office-actor") || e.target.closest(".office-hotspot")) return;
      const rect = floorEl.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      ripple(x, y);
    });

    scheduleGossip();
  }

  function scheduleGossip() {
    clearTimeout(gossipTimer);
    const delay = 28000 + Math.random() * 32000;
    gossipTimer = setTimeout(async () => {
      await maybeCoolerGossip();
      scheduleGossip();
    }, delay);
  }

  window.OfficeWorld = {
    DESKS,

    setOnCaption(fn) {
      onCaption = fn;
    },

    summonToHotspot,

    init(floor) {
      if (actorsEl && floorEl === floor) return;
      floorEl = floor;
      floorEl.classList.add("office-floor-interactive");
      floorEl.innerHTML = `
        ${buildRoomsHtml()}
        <div class="office-desks" aria-hidden="true"></div>
        <div class="office-actors" id="office-actors"></div>
        <div class="work-parcel" id="work-parcel" hidden>📦</div>
      `;
      effectsEl = floorEl.querySelector(".office-effects");
      const desksLayer = floorEl.querySelector(".office-desks");
      actorsEl = floorEl.querySelector("#office-actors");
      parcelEl = floorEl.querySelector("#work-parcel");

      desksLayer.innerHTML =
        DESKS.map((d) => deskMarkup(d, { agent: true })).join("") +
        EXTRA_DESKS.map((d) => deskMarkup(d, { agent: false })).join("");

      actorsEl.innerHTML = DESKS.map(
        (d) => `
        <div class="office-actor idle ${d.id === "human" ? "seated is-supervisor" : ""}" data-id="${d.id}" data-home-x="${d.x}" data-home-y="${d.y}" style="left:${d.x}%;top:${d.y}%">
          <div class="actor-select-ring"></div>
          <div class="actor-bubble"></div>
          <div class="actor-tag"></div>
          <div class="actor-sprite facing-right"></div>
          <div class="actor-model"></div>
        </div>`,
      ).join("");

      DESKS.forEach((d) => {
        actorNodes[d.id] = actorsEl.querySelector(`[data-id="${d.id}"]`);
      });

      setupInteractions();

      if (!lifeStarted) {
        lifeStarted = true;
        WANDER_AGENTS.forEach((id, i) => {
          lastModes[id] = "idle";
          if (id === "human") {
            stayAtSupervisorDesk();
            return;
          }
          setTimeout(() => resumeWander(id), i * 900 + Math.random() * 1200);
        });
      }
    },

    getActor(id) {
      return actorNodes[id];
    },

    holdMeetingPositions() {
      if (!meetingActive) return;
      const pm = actorNodes.pm;
      const human = actorNodes.human;
      if (pm && !pm.classList.contains("walking")) {
        pm.classList.remove("seated", "wandering", "at-desk");
        setPosition(pm, MEETING_PM.x, MEETING_PM.y, false);
      }
      if (human && !human.classList.contains("walking")) {
        human.classList.remove("seated", "wandering", "at-desk");
        setPosition(human, MEETING_HUMAN.x, MEETING_HUMAN.y, false);
      }
    },

    updateActor(id, { mode, bubble, tag, model, pose }) {
      const node = actorNodes[id];
      if (!node) return;
      lastModes[id] = mode || "idle";

      if (meetingActive && (id === "human" || id === "pm")) {
        pauseWander(id);
        node.classList.remove("seated", "at-desk");
      } else if (id === "human" && mode === "human-needed") {
        pauseWander(id);
        goHome(id, true).then(() => {
          node.classList.add("seated");
        });
      } else if (id === "human" && (mode === "idle" || mode === "done")) {
        if (!handoffActive && !node.classList.contains("walking")) {
          stayAtSupervisorDesk();
        }
      } else if (mode === "working") {
        pauseWander(id);
        node.classList.remove("seated", "at-desk");
        goHome(id, true).then(() => updateTeamSeated(id));
      } else if (mode === "human-needed") {
        pauseWander(id);
        node.classList.add("needs-you");
      } else {
        node.classList.remove("needs-you");
        if (mode !== "working") {
          node.classList.remove("seated");
        }
        if ((mode === "idle" || mode === "done") && !handoffActive && !node.classList.contains("walking")) {
          resumeWander(id);
        }
      }

      node.classList.remove("idle", "working", "done", "human-needed");
      if (!node.classList.contains("wandering")) {
        node.classList.add(mode || "idle");
      }
      const bubbleEl = node.querySelector(".actor-bubble");
      const keepTalk = meetingActive && (id === "pm" || id === "human");
      if (bubbleEl && !keepTalk && !node.classList.contains("wandering")) setBubbleText(bubbleEl, bubble || "");
      else if (bubbleEl && (mode === "working" || mode === "human-needed")) setBubbleText(bubbleEl, bubble || "");

      node.querySelector(".actor-tag").textContent = tag || "";
      node.querySelector(".actor-model").textContent = model || "";
      const spriteWrap = node.querySelector(".actor-sprite");
      if (window.renderRoleSprite && !node.classList.contains("walking")) {
        const p = pose || (mode === "working" ? "work" : "idle");
        const humanPose =
          id === "human" && (mode === "human-needed" || node.classList.contains("seated")) ? "work" : p;
        spriteWrap.innerHTML = window.renderRoleSprite(id, { pose: id === "human" ? humanPose : p });
        spriteWrap.classList.add("facing-right");
      }
      const desk = floorEl.querySelector(`[data-desk="${id}"]`);
      desk?.classList.toggle("active", mode === "working" && !meetingActive);
      desk?.classList.toggle("done", mode === "done");
      if (selectedId === id) node.classList.add("selected");
      if (meetingActive) this.holdMeetingPositions();
    },

    bindClick(handler) {
      Object.values(actorNodes).forEach((node) => {
        node.onclick = (e) => {
          e.stopPropagation();
          pokeAgent(node.dataset.id);
          handler(node.dataset.id);
        };
      });
    },

    async startMeeting(lines, options = {}) {
      const mode = options.mode || "";
      const talk = (lines || []).filter(Boolean).slice(0, 12);
      if (!talk.length || meetingActive) return;
      meetingActive = true;
      handoffActive = true;
      pauseAllWander();
      await Promise.all([
        walkActorTo("pm", MEETING_PM.x, MEETING_PM.y),
        walkActorTo("human", MEETING_HUMAN.x, MEETING_HUMAN.y),
      ]);
      this.holdMeetingPositions();
      handoffActive = false;
      let i = 0;
      const tick = () => {
        if (!meetingActive) return;
        const pmBubble = actorNodes.pm?.querySelector(".actor-bubble");
        const youBubble = actorNodes.human?.querySelector(".actor-bubble");
        const line = talk[i % talk.length];
        const supervisorPrompt =
          mode === "ac_signoff"
            ? ["Can QA verify this?", "Ready to sign off on AC?", "Is anything missing?", "Testable enough?"][
                i % 4
              ]
            : mode === "release"
              ? ["Ready to ship?", "Any blockers?", "Tests all green?", "Sign release?"][i % 4]
              : "Does this match the brief?";
        const youLead =
          mode === "ac_signoff" ? "Walk me through AC." : mode === "release" ? "Walk me through QA." : "Let’s go through that.";
        if (i % 2 === 0) {
          setBubbleText(pmBubble, line);
          setBubbleText(youBubble, youLead);
        } else {
          setBubbleText(youBubble, supervisorPrompt);
          setBubbleText(pmBubble, line);
        }
        i += 1;
        meetingTickTimer = setTimeout(tick, 3200);
      };
      tick();
    },

    endMeeting() {
      meetingActive = false;
      handoffActive = false;
      if (meetingTickTimer) {
        clearTimeout(meetingTickTimer);
        meetingTickTimer = null;
      }
      const pmBubble = actorNodes.pm?.querySelector(".actor-bubble");
      const youBubble = actorNodes.human?.querySelector(".actor-bubble");
      if (pmBubble) pmBubble.textContent = "";
      if (youBubble) youBubble.textContent = "";
      ["pm", "human"].forEach((id) => {
        const node = actorNodes[id];
        if (!node) return;
        node.classList.remove("wandering", "needs-you");
        pauseWander(id);
      });
      goHome("pm", true);
      goHome("human", true).then(() => {
        stayAtSupervisorDesk();
        resumeIdleRoamers();
      });
    },

    passWork(fromId, toId, opts = {}) {
      walkQueue = walkQueue.then(() => this._passWork(fromId, toId, opts));
      return walkQueue;
    },

    async _passWork(fromId, toId, opts = {}) {
      handoffActive = true;
      pauseAllWander();
      const isReturn = opts.direction === "return";
      const from = home(fromId);
      const to = home(toId);
      const walker = actorNodes[fromId];
      const receiver = actorNodes[toId];
      if (!walker || !to) {
        handoffActive = false;
        resumeIdleRoamers();
        return;
      }

      walker.classList.add("walking");
      walker.classList.toggle("return-walk", isReturn);
      walker.classList.remove("working", "idle", "wandering");
      if (window.renderRoleSprite) {
        walker.querySelector(".actor-sprite").innerHTML = window.renderRoleSprite(fromId, { pose: "walk" });
      }

      parcelEl.hidden = false;
      parcelEl.textContent = isReturn ? "↩️" : "📦";
      parcelEl.classList.toggle("return", isReturn);
      parcelEl.style.left = `${from.x}%`;
      parcelEl.style.top = `${from.y - 8}%`;
      parcelEl.classList.add("show");
      if (isReturn && opts.reason) {
        walker.querySelector(".actor-bubble").textContent = "scope?";
      }

      const fromPos = parsePos(walker);
      const step = setInterval(() => footDust(walker), 260);
      setFacing(walker, fromPos.x, to.x);
      setPosition(walker, to.x, to.y - 4, true);
      setPosition(parcelEl, to.x, to.y - 10, true);
      await waitTransition(walker);
      clearInterval(step);

      parcelEl.classList.add("deliver");
      receiver?.classList.add("receive");
      ripple(to.x, to.y);
      await wait(350);
      parcelEl.classList.remove("show", "deliver", "return");
      parcelEl.hidden = true;
      parcelEl.textContent = "📦";
      walker.querySelector(".actor-bubble").textContent = "";
      receiver?.classList.remove("receive");

      setFacing(walker, to.x, from.x);
      if (window.renderRoleSprite) {
        walker.querySelector(".actor-sprite").innerHTML = window.renderRoleSprite(fromId, { pose: "walk" });
      }
      const stepBack = setInterval(() => footDust(walker), 260);
      setPosition(walker, from.x, from.y, true);
      setPosition(parcelEl, from.x, from.y - 8, false);
      await waitTransition(walker);
      clearInterval(stepBack);

      walker.classList.remove("walking", "return-walk");
      handoffActive = false;
      resumeIdleRoamers();
    },

    resetPositions() {
      pauseAllWander();
      DESKS.forEach((d) => {
        const node = actorNodes[d];
        if (node) setPosition(node, d.x, d.y, false);
      });
      resumeIdleRoamers();
    },
  };
})();
