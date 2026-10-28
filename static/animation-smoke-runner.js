/** Workflow animation smoke — driven by workflow-handoffs.json */
(function () {
  const MANIFEST_URL = "/static/workflow-handoffs.json";

  function logLine(logEl, text, ok) {
    const span = document.createElement("span");
    span.className = ok === true ? "log-pass" : ok === false ? "log-fail" : "";
    span.textContent = text + "\n";
    logEl.appendChild(span);
    logEl.scrollTop = logEl.scrollHeight;
  }

  async function loadManifest() {
    const res = await fetch(MANIFEST_URL);
    if (!res.ok) throw new Error(`Could not load ${MANIFEST_URL}`);
    return res.json();
  }

  async function runPassWorkWithTrace(from, to, direction) {
    const parcel = document.getElementById("work-parcel");
    let parcelShown = false;
    const obs = new MutationObserver(() => {
      if (parcel.classList.contains("show") && !parcel.hidden) parcelShown = true;
    });
    obs.observe(parcel, { attributes: true, attributeFilter: ["class", "hidden"] });
    await window.OfficeWorld.passWork(from, to, { direction });
    obs.disconnect();
    const walker = document.querySelector(`[data-id='${from}']`);
    return {
      parcelShown,
      walkerWalking: walker?.classList.contains("walking") ?? false,
      parcelHidden: parcel.hidden,
    };
  }

  async function waitForMeetingPositions(timeoutMs = 5000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const pm = document.querySelector("[data-id='pm']");
      const human = document.querySelector("[data-id='human']");
      const pmY = parseFloat(pm?.style.top || "0");
      const humanY = parseFloat(human?.style.top || "0");
      if (pmY > 70 && humanY > 70) return true;
      await new Promise((r) => setTimeout(r, 120));
    }
    return false;
  }

  async function runMeeting(meeting) {
    await window.OfficeWorld.startMeeting(meeting.lines || [], { mode: meeting.mode || "" });
    return waitForMeetingPositions();
  }

  function findParcel(manifest, id) {
    return (manifest.parcel || []).find((p) => p.id === id);
  }

  function findMeeting(manifest, id) {
    return (manifest.meetings || []).find((m) => m.id === id);
  }

  async function runScenarioId(manifest, id) {
    const meeting = findMeeting(manifest, id);
    if (meeting) {
      const ok = await runMeeting(meeting);
      return { ok, detail: ok ? "meeting positions" : "meeting positions wrong" };
    }
    const parcel = findParcel(manifest, id);
    if (!parcel) {
      return { ok: false, detail: "unknown scenario id" };
    }
    const r = await runPassWorkWithTrace(parcel.from, parcel.to, parcel.direction);
    const ok = r.parcelShown && !r.walkerWalking && r.parcelHidden;
    return { ok, detail: JSON.stringify(r) };
  }

  function renderScenarioList(manifest, container) {
    container.innerHTML = "";
    const phases = [];
    const addPhase = (phase) => {
      if (!phases.includes(phase)) phases.push(phase);
    };
    (manifest.meetings || []).forEach((m) => addPhase(m.phase));
    (manifest.parcel || []).forEach((p) => addPhase(p.phase));

    phases.forEach((phase) => {
      const h2 = document.createElement("h2");
      h2.textContent = phase;
      container.appendChild(h2);

      (manifest.meetings || [])
        .filter((m) => m.phase === phase)
        .forEach((m) => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "scenario";
          btn.dataset.scenario = m.id;
          btn.innerHTML = `${m.label}<small>${m.graph || m.id}</small>`;
          container.appendChild(btn);
        });

      (manifest.parcel || [])
        .filter((p) => p.phase === phase)
        .forEach((p) => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "scenario";
          btn.dataset.scenario = p.id;
          const arrow = p.direction === "return" ? " ↩" : "";
          btn.innerHTML = `Parcel: ${p.label}${arrow}<small>${p.graph || ""}</small>`;
          container.appendChild(btn);
        });
    });
  }

  window.AnimationSmokeRunner = {
    manifest: null,

    async init({ logEl, scenarioListEl, onBusy }) {
      const manifest = await loadManifest();
      this.manifest = manifest;
      window.WORKFLOW_HANDOFF_MANIFEST = manifest;

      window.runPassWorkSmoke = (from, to, direction = "forward") =>
        window.OfficeWorld.passWork(from, to, { direction });

      window.runPassWorkSmokeWithTrace = (from, to, direction = "forward") =>
        runPassWorkWithTrace(from, to, direction);

      window.runReleaseMeetingSmoke = () =>
        runMeeting(findMeeting(manifest, "gate-release") || { mode: "release", lines: ["QA passed."] });

      window.runWorkflowScenario = (id) => runScenarioId(manifest, id);

      renderScenarioList(manifest, scenarioListEl);

      const runOne = async (id) => {
        onBusy(true);
        logLine(logEl, `— ${id} —`);
        try {
          window.OfficeWorld.endMeeting?.();
          const { ok, detail } = await runScenarioId(manifest, id);
          logLine(logEl, ok ? `PASS  ${id}` : `FAIL  ${id} ${detail}`, ok);
          return ok;
        } catch (e) {
          logLine(logEl, `FAIL  ${id}: ${e.message}`, false);
          return false;
        } finally {
          onBusy(false);
        }
      };

      scenarioListEl.querySelectorAll(".scenario").forEach((btn) => {
        btn.addEventListener("click", () => runOne(btn.dataset.scenario));
      });

      return {
        runAll: async () => {
          logEl.textContent = "";
          logLine(logEl, `Running ${manifest.parcel.length} parcels + ${manifest.meetings.length} meetings…`);
          onBusy(true);
          let passed = 0;
          const ids = [
            ...(manifest.meetings || []).map((m) => m.id),
            ...(manifest.parcel || []).map((p) => p.id),
          ];
          for (const id of ids) {
            window.OfficeWorld.endMeeting?.();
            try {
              const { ok } = await runScenarioId(manifest, id);
              logLine(logEl, ok ? `PASS  ${id}` : `FAIL  ${id}`, ok);
              if (ok) passed += 1;
            } catch (e) {
              logLine(logEl, `FAIL  ${id}: ${e.message}`, false);
            }
          }
          logLine(
            logEl,
            `Done: ${passed}/${ids.length} passed`,
            passed === ids.length,
          );
          onBusy(false);
        },
        playthrough: async () => {
          logEl.textContent = "";
          logLine(logEl, "Workflow playthrough (happy path + one retry)…");
          onBusy(true);
          let passed = 0;
          const order = manifest.playthrough || [];
          for (const id of order) {
            window.OfficeWorld.endMeeting?.();
            await new Promise((r) => setTimeout(r, 200));
            try {
              const { ok, detail } = await runScenarioId(manifest, id);
              logLine(logEl, ok ? `  ✓ ${id}` : `  ✗ ${id} ${detail}`, ok);
              if (ok) passed += 1;
              if (id.startsWith("gate-")) {
                window.OfficeWorld.endMeeting?.();
                await new Promise((r) => setTimeout(r, 400));
              }
            } catch (e) {
              logLine(logEl, `  ✗ ${id}: ${e.message}`, false);
            }
          }
          logLine(
            logEl,
            `Playthrough: ${passed}/${order.length} steps`,
            passed === order.length,
          );
          onBusy(false);
        },
      };
    },
  };
})();
