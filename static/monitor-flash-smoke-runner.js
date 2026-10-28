/** Wood-floor monitor overlay smoke — desk.active + .ws-screen flash when agent is working */
(function () {
  const ROLES = ["pm", "architect", "designer", "developer", "qa"];

  function wait(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  function deskFor(role) {
    return document.querySelector(`.role-desk[data-desk="${role}"]`);
  }

  function actorFor(role) {
    return document.querySelector(`.office-actor[data-id="${role}"]`);
  }

  function screenVisible(desk) {
    if (!desk) return false;
    const screen = desk.querySelector(".ws-screen");
    if (!screen) return false;
    const cs = getComputedStyle(screen);
    return cs.visibility !== "hidden" && parseFloat(cs.opacity || "0") > 0.05;
  }

  function screenAnimating(desk) {
    const screen = desk?.querySelector(".ws-screen");
    const inner = screen?.querySelector("i");
    if (!screen || !inner) return false;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      const shadow = getComputedStyle(screen).boxShadow || "";
      return shadow.length > 4 && shadow !== "none";
    }
    const glow = getComputedStyle(screen).animationName || "";
    const flash = getComputedStyle(inner).animationName || "";
    return glow !== "none" && flash !== "none";
  }

  /** Monitor should sit on the desk (north of the agent), not on the torso. */
  function screenAligned(role) {
    const actor = actorFor(role);
    const screen = deskFor(role)?.querySelector(".ws-screen");
    if (!actor || !screen) return false;
    const ar = actor.getBoundingClientRect();
    const sr = screen.getBoundingClientRect();
    if (ar.width < 2 || sr.width < 2) return false;
    const actorCx = ar.left + ar.width / 2;
    const screenCx = sr.left + sr.width / 2;
    const horizontalOk = Math.abs(screenCx - actorCx) <= Math.max(ar.width * 0.85, 36);
    const screenNorthOfActor = sr.top + sr.height / 2 < ar.top + ar.height * 0.55;
    return horizontalOk && screenNorthOfActor;
  }

  async function waitSeated(role, timeoutMs = 4000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const node = actorFor(role);
      if (node?.classList.contains("at-desk") || node?.classList.contains("seated")) return true;
      await wait(80);
    }
    return false;
  }

  async function settleWorking(role) {
    window.OfficeWorld.endMeeting?.();
    window.OfficeWorld.resetPositions?.();
    ROLES.forEach((id) => {
      window.OfficeWorld.updateActor(id, { mode: "idle", tag: "idle", bubble: "" });
    });
    await wait(80);
    window.OfficeWorld.updateActor(role, {
      mode: "working",
      tag: "busy",
      bubble: "Monitor flash smoke…",
    });
    await waitSeated(role);
    await wait(150);
    return deskFor(role);
  }

  async function testRole(role) {
    if (!ROLES.includes(role)) {
      return { ok: false, role, detail: "unknown role" };
    }
    const desk = await settleWorking(role);
    const deskActive = Boolean(desk?.classList.contains("active"));
    const visible = screenVisible(desk);
    const animating = deskActive && screenAnimating(desk);
    const aligned = deskActive && screenAligned(role);
    const ok = deskActive && visible && animating;
    return {
      ok,
      role,
      deskActive,
      screenVisible: visible,
      animating,
      aligned,
      detail: ok
        ? aligned
          ? "active + visible + animating + on monitor"
          : "active + visible + animating (overlay offset — tune DESKS sx/sy)"
        : JSON.stringify({ deskActive, visible, animating, aligned }),
    };
  }

  window.MonitorFlashSmoke = {
    roles: ROLES,
    testRole,
    async runAll() {
      const results = [];
      for (const role of ROLES) {
        results.push(await testRole(role));
      }
      const passed = results.filter((r) => r.ok).length;
      return { passed, total: results.length, results };
    },
  };
})();
