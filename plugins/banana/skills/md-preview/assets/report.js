(() => {
  "use strict";

  const root = document.documentElement;
  const body = document.body;
  const toast = document.getElementById("toast");
  const themeButton = document.getElementById("theme-toggle");
  const themeLabel = document.getElementById("theme-label");
  const themeIcon = document.getElementById("theme-icon");
  const widthButton = document.getElementById("width-toggle");
  const densityButton = document.getElementById("density-toggle");
  const sourceDialog = document.getElementById("source-dialog");
  const diagramDialog = document.getElementById("diagram-dialog");
  const diagramStage = document.getElementById("diagram-stage");
  const tocPanel = document.getElementById("toc-panel");
  const tocToggle = document.getElementById("toc-toggle");
  const tocClose = document.getElementById("toc-close");
  const tocScrim = document.getElementById("toc-scrim");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const darkPreference = window.matchMedia("(prefers-color-scheme: dark)");

  let toastTimer = 0;
  let diagramScale = 1;
  let mermaidEpoch = 0;

  function storageGet(key, fallback) {
    try {
      return localStorage.getItem(key) || fallback;
    } catch {
      return fallback;
    }
  }

  function storageSet(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch {
      // Reading preferences are optional.
    }
  }

  function showToast(message) {
    window.clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add("is-visible");
    toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 1800);
  }

  function resolvedTheme(theme) {
    if (theme === "system") {
      return darkPreference.matches ? "dark" : "light";
    }
    return theme;
  }

  function applyTheme(theme, rerender = true) {
    const safeTheme = ["system", "light", "dark"].includes(theme) ? theme : "system";
    root.dataset.theme = safeTheme;
    root.dataset.resolvedTheme = resolvedTheme(safeTheme);
    const labels = {
      system: ["◐", "跟随系统"],
      light: ["☀", "浅色"],
      dark: ["◒", "深色"],
    };
    themeIcon.textContent = labels[safeTheme][0];
    themeLabel.textContent = labels[safeTheme][1];
    themeButton.setAttribute("aria-label", `当前${labels[safeTheme][1]}，切换颜色主题`);
    storageSet("rr-theme", safeTheme);
    if (rerender) {
      renderDiagrams();
    }
  }

  function cycleTheme() {
    const order = ["system", "dark", "light"];
    const current = root.dataset.theme || "system";
    applyTheme(order[(order.indexOf(current) + 1) % order.length]);
  }

  function applyReadingPreference(key, value) {
    root.dataset[key] = value;
    storageSet(`rr-${key}`, value);
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) {
      throw new Error("copy failed");
    }
  }

  function openDialog(dialog) {
    if (!dialog) return;
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      dialog.setAttribute("open", "");
    }
  }

  function closeDialog(dialog) {
    if (!dialog) return;
    if (typeof dialog.close === "function") {
      dialog.close();
    } else {
      dialog.removeAttribute("open");
    }
  }

  function diagramThemeVariables() {
    const style = getComputedStyle(root);
    const dark = root.dataset.resolvedTheme === "dark";
    return {
      background: style.getPropertyValue("--surface-solid").trim(),
      primaryColor: dark ? "#183e41" : "#d8eeee",
      primaryTextColor: style.getPropertyValue("--ink").trim(),
      primaryBorderColor: style.getPropertyValue("--accent").trim(),
      secondaryColor: dark ? "#39251d" : "#f7dfd2",
      secondaryTextColor: style.getPropertyValue("--ink").trim(),
      secondaryBorderColor: style.getPropertyValue("--signal").trim(),
      tertiaryColor: style.getPropertyValue("--paper").trim(),
      tertiaryTextColor: style.getPropertyValue("--ink").trim(),
      tertiaryBorderColor: style.getPropertyValue("--line-strong").trim(),
      lineColor: style.getPropertyValue("--ink-soft").trim(),
      textColor: style.getPropertyValue("--ink").trim(),
      fontFamily: style.getPropertyValue("--sans").trim(),
    };
  }

  async function renderDiagrams() {
    if (!window.mermaid) return;
    const epoch = ++mermaidEpoch;
    window.mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      deterministicIds: true,
      suppressErrorRendering: true,
      flowchart: { useMaxWidth: true, htmlLabels: false },
      themeVariables: diagramThemeVariables(),
    });

    const figures = [...document.querySelectorAll("[data-diagram]")];
    for (let index = 0; index < figures.length; index += 1) {
      if (epoch !== mermaidEpoch) return;
      const figure = figures[index];
      const source = figure.querySelector(".mermaid-source")?.content.textContent?.trim() || "";
      const canvas = figure.querySelector(".mermaid-canvas");
      if (!source || !canvas) continue;
      canvas.replaceChildren();
      canvas.setAttribute("aria-busy", "true");
      try {
        const id = `rr-mermaid-${epoch}-${index}`;
        const result = await window.mermaid.render(id, source);
        if (epoch !== mermaidEpoch) return;
        canvas.innerHTML = result.svg;
        result.bindFunctions?.(canvas);
        const svg = canvas.querySelector("svg");
        if (svg) {
          svg.removeAttribute("height");
          svg.setAttribute("aria-hidden", "true");
          svg.setAttribute("focusable", "false");
        }
      } catch (error) {
        const message = document.createElement("p");
        message.className = "diagram-error";
        message.textContent = `图表渲染失败：${error instanceof Error ? error.message : "未知错误"}`;
        canvas.appendChild(message);
      } finally {
        canvas.removeAttribute("aria-busy");
      }
    }
  }

  function openDiagram(button) {
    const target = button.dataset.diagramTarget;
    const figure = document.querySelector(`[data-diagram="${CSS.escape(target)}"]`);
    const svg = figure?.querySelector(".mermaid-canvas svg");
    if (!svg) {
      showToast("结构图尚未成功渲染");
      return;
    }
    const title = figure.querySelector("figcaption")?.textContent || "结构图";
    document.getElementById("diagram-dialog-title").textContent = title;
    diagramStage.replaceChildren(svg.cloneNode(true));
    diagramScale = 1;
    diagramStage.style.setProperty("--diagram-scale", "1");
    openDialog(diagramDialog);
  }

  function updateDiagramScale(next) {
    diagramScale = Math.min(3, Math.max(0.4, next));
    diagramStage.style.setProperty("--diagram-scale", String(diagramScale));
    document.getElementById("diagram-zoom-reset").textContent = `${Math.round(diagramScale * 100)}%`;
  }

  function openToc() {
    body.classList.add("toc-open");
    tocToggle.setAttribute("aria-expanded", "true");
    tocScrim.hidden = false;
    tocClose.focus();
  }

  function closeToc(restoreFocus = false) {
    body.classList.remove("toc-open");
    tocToggle.setAttribute("aria-expanded", "false");
    tocScrim.hidden = true;
    if (restoreFocus) tocToggle.focus();
  }

  function bindScrollProgress() {
    const progress = document.getElementById("reading-progress-bar");
    const backToTop = document.getElementById("back-to-top");
    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const ratio = max > 0 ? Math.min(1, window.scrollY / max) : 0;
      progress.style.width = `${ratio * 100}%`;
      backToTop.classList.toggle("is-visible", window.scrollY > 800);
    };
    document.addEventListener("scroll", update, { passive: true });
    update();
  }

  function bindScrollSpy() {
    const links = [...document.querySelectorAll(".toc-list a[href^='#']")];
    const targets = links
      .map((link) => document.getElementById(link.getAttribute("href").slice(1)))
      .filter(Boolean);
    if (!targets.length || !("IntersectionObserver" in window)) return;

    const setActive = (id) => {
      links.forEach((link) => {
        const active = link.getAttribute("href") === `#${id}`;
        link.classList.toggle("is-active", active);
        if (active) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    };

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-15% 0px -72% 0px", threshold: [0, 1] }
    );
    targets.forEach((target) => observer.observe(target));
  }

  function bindEvents() {
    themeButton.addEventListener("click", cycleTheme);
    widthButton.addEventListener("click", () => {
      const next = root.dataset.width === "wide" ? "balanced" : "wide";
      applyReadingPreference("width", next);
      showToast(next === "wide" ? "已切换到宽幅阅读" : "已切换到平衡阅读");
    });
    densityButton.addEventListener("click", () => {
      const next = root.dataset.density === "compact" ? "comfortable" : "compact";
      applyReadingPreference("density", next);
      showToast(next === "compact" ? "已切换到紧凑排版" : "已切换到舒适排版");
    });
    document.getElementById("print-report").addEventListener("click", () => window.print());
    document.getElementById("source-open").addEventListener("click", () => openDialog(sourceDialog));
    document.querySelectorAll("[data-open-source]").forEach((button) => {
      button.addEventListener("click", () => openDialog(sourceDialog));
    });
    document.querySelectorAll("[data-close-dialog]").forEach((button) => {
      button.addEventListener("click", () => closeDialog(document.getElementById(button.dataset.closeDialog)));
    });
    document.querySelectorAll(".copy-code").forEach((button) => {
      button.addEventListener("click", async () => {
        const target = document.getElementById(button.dataset.copyTarget);
        try {
          await copyText(target?.textContent || "");
          showToast("代码已复制");
        } catch {
          showToast("无法自动复制，请手动选择");
        }
      });
    });
    document.querySelectorAll(".expand-diagram").forEach((button) => {
      button.addEventListener("click", () => openDiagram(button));
    });

    document.getElementById("diagram-zoom-in").addEventListener("click", () => updateDiagramScale(diagramScale + 0.2));
    document.getElementById("diagram-zoom-out").addEventListener("click", () => updateDiagramScale(diagramScale - 0.2));
    document.getElementById("diagram-zoom-reset").addEventListener("click", () => updateDiagramScale(1));
    document.getElementById("back-to-top").addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: reduceMotion.matches ? "auto" : "smooth" });
    });

    tocToggle.addEventListener("click", openToc);
    tocClose.addEventListener("click", () => closeToc(true));
    tocScrim.addEventListener("click", () => closeToc(true));
    tocPanel.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 900) closeToc(false);
      });
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && body.classList.contains("toc-open")) {
        closeToc(true);
      }
    });

    [sourceDialog, diagramDialog].forEach((dialog) => {
      dialog.addEventListener("click", (event) => {
        if (event.target === dialog) closeDialog(dialog);
      });
    });

    darkPreference.addEventListener?.("change", () => {
      if (root.dataset.theme === "system") applyTheme("system");
    });
  }

  function init() {
    applyReadingPreference("width", storageGet("rr-width", "balanced"));
    applyReadingPreference("density", storageGet("rr-density", "comfortable"));
    applyTheme(storageGet("rr-theme", "system"), false);
    bindEvents();
    bindScrollProgress();
    bindScrollSpy();
    renderDiagrams();
  }

  init();
})();
