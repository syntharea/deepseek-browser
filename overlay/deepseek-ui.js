(() => {
  const STORAGE_KEY = "sidepanel_connections";
  const GROUP_ID = "deepseek-settings-group";
  const isZh = (navigator.language || "").toLowerCase().startsWith("zh");
  const text = isZh
    ? {
        group: "模型",
        title: "DeepSeek",
        configured: "已配置",
        missing: "未配置",
        setup: "配置 DeepSeek",
        check: "检查 DeepSeek",
      }
    : {
        group: "Models",
        title: "DeepSeek",
        configured: "Configured",
        missing: "Not configured",
        setup: "Set up DeepSeek",
        check: "Check DeepSeek",
      };

  let configured = null;
  let observer = null;

  function injectBrandStyle() {
    if (document.getElementById("deepseek-brand-style")) return;
    const style = document.createElement("style");
    style.id = "deepseek-brand-style";
    style.textContent = `
      :root, body, .wb-app {
        --wb-blue: #4d6bfe !important;
        --wb-blue-hover: #3b5bdb !important;
        --wb-accent: #4d6bfe !important;
        --wb-accent-hover: #3b5bdb !important;
        --wb-accent-ink: #ffffff !important;
      }
      .wb-set-account,
      .wb-account-membership,
      .wb-account-upgrade,
      [data-deepseek-hidden="1"] { display: none !important; }
    `;
    document.documentElement.appendChild(style);
  }

  function hideLegacyBranding() {
    for (const group of document.querySelectorAll(".wb-settings-body > .wb-set-group")) {
      const label = (group.querySelector(".wb-set-group-label")?.textContent || "").trim();
      if (/local agent|remote control|远程控制|远程调用|daemon/i.test(label)) {
        group.setAttribute("data-deepseek-hidden", "1");
      }
    }
    for (const row of document.querySelectorAll(".wb-set-row")) {
      const label = (row.textContent || "").trim();
      if (/credits|quota|subscription|membership|usage|feedback|额度|积分|会员|用量|反馈/i.test(label)) {
        row.setAttribute("data-deepseek-hidden", "1");
      }
    }
  }

  function updateStatus() {
    const el = document.getElementById("deepseek-settings-status");
    if (!el) return;
    el.textContent =
      configured === null ? "" : configured ? text.configured : text.missing;
  }

  function openSettings() {
    const url = chrome.runtime.getURL("deepseek.html");
    try {
      chrome.tabs.create({ url });
    } catch {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  }

  function buildGroup() {
    const group = document.createElement("div");
    group.className = "wb-set-group";
    group.id = GROUP_ID;

    const label = document.createElement("div");
    label.className = "wb-set-group-label";
    label.textContent = text.group;

    const card = document.createElement("div");
    card.className = "wb-set-card";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "wb-set-row wb-set-navrow";
    button.style.width = "100%";
    button.addEventListener("click", openSettings);

    const title = document.createElement("span");
    title.className = "wb-set-row-label";
    title.textContent = text.title;

    const status = document.createElement("span");
    status.className = "wb-set-row-value";
    status.id = "deepseek-settings-status";

    button.append(title, status);
    card.appendChild(button);
    group.append(label, card);
    return group;
  }

  function inject() {
    if (configured === null) return;
    const body = document.querySelector(".wb-settings-body");
    if (!body || !body.querySelector(".wb-set-account")) return;
    if (body.querySelector(`#${GROUP_ID}`)) return;
    const group = buildGroup();
    const groups = body.querySelectorAll(":scope > .wb-set-group");
    if (groups.length > 1) body.insertBefore(group, groups[groups.length - 1]);
    else body.appendChild(group);
    updateStatus();
  }

  function ensureChip() {
    if (configured === null) return;
    const toggle = document.querySelector(".wb-composer-model .wb-mode-toggle");
    const composer = document.querySelector(".wb-composer");
    const existing = document.getElementById("deepseek-config-chip");
    if (!toggle || !toggle.disabled) {
      existing?.remove();
      return;
    }
    const label = configured ? text.check : text.setup;
    if (existing) {
      if (existing.textContent !== label) existing.textContent = label;
      return;
    }
    const chip = document.createElement("button");
    chip.type = "button";
    chip.id = "deepseek-config-chip";
    chip.textContent = label;
    chip.style.cssText =
      "display:block;width:calc(100% - 32px);margin:6px 16px 0;padding:9px 14px;" +
      "border-radius:10px;border:1px solid rgba(77,107,254,.35);" +
      "background:#4d6bfe;color:#fff;font:inherit;font-size:13px;font-weight:500;" +
      "line-height:18px;cursor:pointer;text-align:center;" +
      "box-shadow:0 4px 14px rgba(77,107,254,.25)";
    chip.addEventListener("click", openSettings);
    if (composer && composer.parentElement) {
      composer.parentElement.insertBefore(chip, composer);
    } else {
      chip.style.position = "fixed";
      chip.style.left = "16px";
      chip.style.right = "16px";
      chip.style.bottom = "90px";
      chip.style.zIndex = "2147483647";
      document.body.appendChild(chip);
    }
  }

  function schedule() {
    if (observer) return;
    observer = requestAnimationFrame(() => {
      observer = null;
      inject();
      hideLegacyBranding();
      ensureChip();
    });
  }

  async function readConfig() {
    const stored = await chrome.storage.local.get(STORAGE_KEY);
    const all = Array.isArray(stored[STORAGE_KEY]) ? stored[STORAGE_KEY] : [];
    configured = all.some((item) => item && item.presetId === "deepseek" && item.apiKey);
    updateStatus();
    schedule();
  }

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && STORAGE_KEY in changes) void readConfig();
  });

  document.addEventListener(
    "click",
    (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const button = target.closest(".wb-notice-actions button");
      if (!button) return;
      if (!/DeepSeek|配置|Set up|Reconfigure/i.test(button.textContent || "")) return;
      event.preventDefault();
      event.stopPropagation();
      openSettings();
    },
    true,
  );

  injectBrandStyle();
  const rootObserver = new MutationObserver(schedule);
  rootObserver.observe(document.documentElement, { childList: true, subtree: true });

  void readConfig().then(schedule);
})();
