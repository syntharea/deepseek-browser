const STORAGE_KEY = "sidepanel_connections";
const PRESET_ID = "deepseek";
const DEFAULT_HOST = "https://api.deepseek.com";

const keyInput = document.getElementById("key");
const hostInput = document.getElementById("host");
const thinkingInput = document.getElementById("thinking");
const statusEl = document.getElementById("status");
const modelsEl = document.getElementById("models");
const saveButton = document.getElementById("save");
const removeButton = document.getElementById("remove");

function normalizeBase(value) {
  let host = (value || "").trim();
  if (!host) return DEFAULT_HOST;
  if (!/^https?:\/\//i.test(host)) host = `https://${host}`;
  host = host.replace(/\/+$/, "");
  if (!/\/v1$/i.test(host)) host += "/v1";
  return host;
}

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = kind;
}

function renderModels(models) {
  if (!models || models.length === 0) {
    modelsEl.textContent = "";
    return;
  }
  const title = document.createElement("div");
  title.textContent = "可用模型：";
  const list = document.createElement("ul");
  for (const model of models) {
    const item = document.createElement("li");
    item.textContent = model;
    list.appendChild(item);
  }
  modelsEl.replaceChildren(title, list);
}

async function loadConnections() {
  const stored = await chrome.storage.local.get(STORAGE_KEY);
  const all = Array.isArray(stored[STORAGE_KEY]) ? stored[STORAGE_KEY] : [];
  return { all, connection: all.find((item) => item && item.presetId === PRESET_ID) };
}

async function saveConnection(connection) {
  const { all } = await loadConnections();
  const next = all.filter((item) => !item || item.presetId !== PRESET_ID);
  next.push(connection);
  await chrome.storage.local.set({ [STORAGE_KEY]: next });
}

async function removeConnection() {
  const { all } = await loadConnections();
  const next = all.filter((item) => !item || item.presetId !== PRESET_ID);
  await chrome.storage.local.set({ [STORAGE_KEY]: next });
}

async function refresh() {
  const { connection } = await loadConnections();
  if (!connection) {
    hostInput.value = "";
    thinkingInput.checked = false;
    renderModels([]);
    setStatus("尚未配置 DeepSeek。填入 API Key 后点击“测试并保存”。");
    saveButton.textContent = "测试并保存";
    return;
  }
  keyInput.value = connection.apiKey || "";
  hostInput.value = connection.hostOverride || "";
  thinkingInput.checked = connection.thinking === true;
  renderModels([]);
  setStatus(
    `已配置。模型会显示在侧边栏的模型选择菜单中。${
      connection.hostOverride ? `\n自定义地址：${connection.hostOverride}` : ""
    }`,
    "ok",
  );
  saveButton.textContent = "测试并保存";
}

async function testAndSave() {
  const apiKey = keyInput.value.trim();
  if (!apiKey) {
    setStatus("请先填写 API Key。", "err");
    keyInput.focus();
    return;
  }
  const base = normalizeBase(hostInput.value);
  saveButton.disabled = true;
  setStatus("正在连接 DeepSeek…");
  try {
    let response;
    try {
      response = await fetch(`${base}/models`, {
        headers: { Authorization: `Bearer ${apiKey}` },
        cache: "no-store",
      });
    } catch (error) {
      setStatus(`网络请求失败：${error instanceof Error ? error.message : String(error)}`, "err");
      return;
    }
    if (response.status === 401 || response.status === 403) {
      setStatus("API Key 无效，或该 Key 没有访问权限。", "err");
      return;
    }
    if (!response.ok) {
      const body = (await response.text().catch(() => "")).slice(0, 300);
      setStatus(`DeepSeek 返回 HTTP ${response.status}${body ? `：${body}` : ""}`, "err");
      return;
    }
    const payload = await response.json().catch(() => null);
    const models = Array.isArray(payload?.data)
      ? payload.data.map((item) => item && item.id).filter((id) => typeof id === "string" && id)
      : [];
    if (models.length === 0) {
      setStatus("连接成功，但没有返回任何模型。", "err");
      return;
    }
    const explicitHost = hostInput.value.trim();
    const hostOverride =
      explicitHost && base !== normalizeBase(DEFAULT_HOST) ? base : undefined;
    await saveConnection({
      id: "deepseek",
      label: "DeepSeek",
      presetId: PRESET_ID,
      apiKey,
      ...(hostOverride ? { hostOverride } : {}),
      ...(thinkingInput.checked ? { thinking: true } : {}),
    });
    renderModels(models);
    setStatus(`已保存，发现 ${models.length} 个模型。回到侧边栏，在模型菜单里选择 DeepSeek。`, "ok");
  } finally {
    saveButton.disabled = false;
  }
}

saveButton.addEventListener("click", () => {
  void testAndSave();
});
removeButton.addEventListener("click", async () => {
  await removeConnection();
  keyInput.value = "";
  hostInput.value = "";
  thinkingInput.checked = false;
  renderModels([]);
  setStatus("已移除 DeepSeek 配置。", "ok");
});
keyInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") void testAndSave();
});

void refresh();
