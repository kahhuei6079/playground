/* Role-based coworker sprites — idle / walk / work poses */
(function () {
  const ROLES = {
    pm: {
      label: "PM",
      skin: "#fde68a",
      hair: "#5c3d2e",
      outfit: "#1d4ed8",
      accent: "#fef08a",
      prop: "clipboard",
    },
    architect: {
      label: "Arch",
      skin: "#e0e7ff",
      hair: "#312e81",
      outfit: "#6366f1",
      accent: "#c7d2fe",
      prop: "clipboard",
    },
    designer: {
      label: "Design",
      skin: "#fecdd3",
      hair: "#881337",
      outfit: "#c026d3",
      accent: "#fae8ff",
      prop: "palette",
    },
    developer: {
      label: "Dev",
      skin: "#bbf7d0",
      hair: "#14532d",
      outfit: "#16a34a",
      accent: "#052e16",
      prop: "laptop",
    },
    qa: {
      label: "QA",
      skin: "#fef08a",
      hair: "#44403c",
      outfit: "#eab308",
      accent: "#fefce8",
      prop: "magnifier",
    },
    human: {
      label: "You",
      skin: "#ffe4e6",
      hair: "#9a3412",
      outfit: "#e11d48",
      accent: "#fff1f2",
      prop: "coffee",
    },
  };

  function px(x, y, w, h, c) {
    return `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${c}"/>`;
  }

  function head(skin, hair) {
    return `
      ${px(10, 2, 20, 7, hair)}
      ${px(9, 5, 3, 8, hair)}
      ${px(28, 5, 3, 8, hair)}
      ${px(11, 8, 18, 16, skin)}
      ${px(14, 14, 4, 4, "#fff")}
      ${px(22, 14, 4, 4, "#fff")}
      ${px(15, 15, 2, 2, "#1f2937")}
      ${px(23, 15, 2, 2, "#1f2937")}
      ${px(16, 16, 1, 1, "#fff")}
      ${px(24, 16, 1, 1, "#fff")}
      ${px(13, 19, 2, 1, "#fda4af")}
      ${px(25, 19, 2, 1, "#fda4af")}
      ${px(17, 21, 6, 2, "#f472b6")}
    `;
  }

  function body(outfit, pants, pose) {
    const legs =
      pose === "walk"
        ? `${px(13, 36, 6, 10, pants)}${px(23, 37, 6, 9, pants)}`
        : `${px(14, 36, 5, 10, pants)}${px(21, 36, 5, 10, pants)}`;
    const arms =
      pose === "work"
        ? `${px(6, 26, 5, 4, outfit)}${px(29, 26, 5, 4, outfit)}${px(5, 29, 6, 3, "#fde68a")}${px(29, 29, 6, 3, "#fde68a")}`
        : pose === "walk"
          ? `${px(8, 27, 4, 6, outfit)}${px(28, 28, 4, 6, outfit)}`
          : `${px(9, 27, 4, 7, outfit)}${px(27, 27, 4, 7, outfit)}`;
    return `${px(12, 24, 16, 12, outfit)}${arms}${legs}${px(13, 46, 6, 3, "#1f2937")}${px(21, 46, 6, 3, "#1f2937")}`;
  }

  function prop(prop, pose, accent) {
    if (prop === "clipboard") {
      return pose === "work"
        ? `${px(28, 22, 10, 12, accent)}${px(29, 24, 8, 1, "#94a3b8")}${px(29, 27, 8, 1, "#94a3b8")}`
        : `${px(26, 28, 8, 10, accent)}`;
    }
    if (prop === "palette") {
      return `${px(3, 24, 8, 8, accent)}${px(4, 25, 2, 2, "#ef4444")}${px(7, 26, 2, 2, "#3b82f6")}${px(5, 28, 2, 2, "#22c55e")}`;
    }
    if (prop === "laptop") {
      return pose === "work"
        ? `${px(2, 32, 12, 6, "#334155")}${px(3, 33, 10, 4, "#38bdf8")}`
        : `${px(4, 30, 8, 5, "#475569")}`;
    }
    if (prop === "magnifier") {
      return `${px(28, 20, 9, 9, "#e0f2fe")}${px(31, 23, 4, 4, "#bae6fd")}${px(32, 24, 1, 1, "#fff")}`;
    }
    if (prop === "coffee") {
      return `${px(3, 30, 5, 6, "#fff")}${px(4, 28, 3, 2, "#fff")}${px(4, 34, 3, 1, "#78350f")}`;
    }
    return "";
  }

  window.renderRoleSprite = function (id, options = {}) {
    const role = ROLES[id] || ROLES.human;
    const pose = options.pose || "idle";
    const pants = role.outfit === role.accent ? "#312e81" : "#1f2937";
    return `
      <svg class="role-sprite" viewBox="0 0 40 52" width="56" height="73" shape-rendering="crispEdges">
        <g class="sprite-pose pose-${pose}">
          ${head(role.skin, role.hair)}
          ${body(role.outfit, pants, pose)}
          ${prop(role.prop, pose, role.accent)}
        </g>
      </svg>
    `;
  };

  window.roleLabel = function (id) {
    return (ROLES[id] || ROLES.human).label;
  };
})();
