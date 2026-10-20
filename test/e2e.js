const fs = require("fs");
const path = require("path");
const os = require("os");
const assert = require("assert");
const { chromium } = require(process.env.PLAYWRIGHT_CORE_PATH || "playwright-core");

const EXT = process.env.EXT_DIR
  ? path.resolve(process.env.EXT_DIR)
  : path.resolve(__dirname, "..", "work", "deepseek-ext");
const CHROME = process.env.CHROME_PATH || chromium.executablePath();
const MOCK = "http://127.0.0.1:8787";
const KEY = "sk-test-deepseek";
const LOG = "/tmp/mock-deepseek.log";
const TOOL_MODE = process.env.TOOL_MODE === "1";

function lastRequest() {
  const lines = fs.readFileSync(LOG, "utf8").split("\n").filter((line) => line.includes("POST "));
  const line = lines.at(-1);
  assert.ok(line, "mock server received no POST");
  return JSON.parse(line.slice(line.indexOf("body=") + 5));
}

async function sendMessage(panel, text, expected = "MOCK-DEEPSEEK OK") {
  const editor = panel.locator(".wb-editor");
  await editor.click();
  await editor.fill("");
  await editor.pressSequentially(text);
  await panel.locator(".wb-send").click();
  await panel.waitForFunction(
    (wanted) => document.body.innerText.includes(wanted),
    expected,
    { timeout: 45000 },
  );
  await panel.waitForTimeout(500);
  return lastRequest();
}

async function main() {
  fs.writeFileSync(LOG, "");
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "ds-ext-"));
  const context = await chromium.launchPersistentContext(profile, {
    executablePath: CHROME,
    headless: true,
    args: [
      `--disable-extensions-except=${EXT}`,
      `--load-extension=${EXT}`,
      "--no-first-run",
      "--no-default-browser-check",
      "--no-sandbox",
    ],
  });
  let worker = context.serviceWorkers()[0];
  if (!worker) worker = await context.waitForEvent("serviceworker", { timeout: 20000 });
  const id = new URL(worker.url()).host;
  console.log("extension id:", id);

  const prePanel = await context.newPage();
  await prePanel.goto(`chrome-extension://${id}/sidepanel.html`, { waitUntil: "domcontentloaded" });
  await prePanel.waitForSelector(".wb-editor", { timeout: 20000 });
  const chip = prePanel.locator("#deepseek-config-chip");
  await chip.waitFor({ timeout: 10000 });
  assert.match((await chip.innerText()).trim(), /配置 DeepSeek|Set up DeepSeek/);
  const [chipPage] = await Promise.all([context.waitForEvent("page"), chip.click()]);
  await chipPage.waitForLoadState("domcontentloaded");
  assert.match(chipPage.url(), /deepseek\.html$/);
  await chipPage.close();
  console.log("unconfigured model chip ok");
  await prePanel.getByRole("button", { name: "Open settings" }).click();
  await prePanel.waitForSelector("#deepseek-settings-group", { timeout: 10000 });
  assert.match(
    (await prePanel.locator("#deepseek-settings-group").innerText()).trim(),
    /未配置|Not configured/,
  );
  console.log("unconfigured settings entry ok");
  await prePanel.close();

  const setup = await context.newPage();
  await setup.goto(`chrome-extension://${id}/deepseek.html`, { waitUntil: "domcontentloaded" });
  await setup.fill("#key", KEY);
  await setup.fill("#host", MOCK);
  if (TOOL_MODE) await setup.check("#thinking");
  await setup.click("#save");
  await setup.waitForSelector("#status.ok", { timeout: 15000 });
  assert.match(await setup.textContent("#models"), /deepseek-flash/);
  assert.match(await setup.textContent("#models"), /deepseek-v4-pro/);
  const stored = await setup.evaluate(() => chrome.storage.local.get("sidepanel_connections"));
  assert.strictEqual(stored.sidepanel_connections[0].presetId, "deepseek");
  console.log("setup page ok, models discovered");

  const panel = await context.newPage();
  const panelErrors = [];
  panel.on("pageerror", (err) => panelErrors.push(err.message));
  await panel.goto(`chrome-extension://${id}/sidepanel.html`, { waitUntil: "domcontentloaded" });
  await panel.waitForSelector(".wb-editor", { timeout: 20000 });
  await panel.waitForTimeout(1500);
  const media = await panel.evaluate(() => ({
    images: Array.from(document.images).map((img) => ({
      src: img.getAttribute("src") || "",
      width: img.naturalWidth,
    })),
    video: (() => {
      const v = document.querySelector("video");
      return v ? { width: v.videoWidth, height: v.videoHeight, ready: v.readyState } : null;
    })(),
  }));
  console.log("media:", JSON.stringify(media));
  for (const image of media.images) {
    if (/icon\/(48|128)\.png/.test(image.src)) {
      assert.ok(image.width > 0, `broken brand image: ${image.src}`);
    }
  }
  if (media.video) assert.ok(media.video.width > 0, "welcome video did not load");
  const modelButton = panel.locator(".wb-composer-model .wb-mode-toggle");
  assert.match((await modelButton.innerText()).trim(), /DeepSeek/);
  console.log("sidepanel model button:", (await modelButton.innerText()).trim());
  await panel.waitForTimeout(500);
  assert.strictEqual(await panel.locator("#deepseek-config-chip").count(), 0);

  await panel.getByRole("button", { name: "Open settings" }).click();
  await panel.waitForSelector("#deepseek-settings-group", { timeout: 10000 });
  const settingsText = (await panel.locator("#deepseek-settings-group").innerText()).trim();
  assert.match(settingsText, /DeepSeek/);
  assert.match(settingsText, /已配置|Configured/);
  const settingsBodyText = await panel.locator(".wb-settings-body").innerText();
  assert.ok(
    !/local agent remote control|本地 Agent 远程调用/i.test(settingsBodyText),
    "legacy local-agent group should be hidden",
  );
  assert.strictEqual(
    await panel.locator(".wb-set-account").isVisible(),
    false,
    "legacy account card should be hidden",
  );
  const groupLabels = await panel
    .locator(".wb-settings-body > .wb-set-group > .wb-set-group-label")
    .allInnerTexts();
  if (groupLabels.includes("About")) {
    assert.ok(
      groupLabels.indexOf("Models") < groupLabels.indexOf("About"),
      `Models group should precede About: ${groupLabels.join(" | ")}`,
    );
  }
  const [settingsPage] = await Promise.all([
    context.waitForEvent("page"),
    panel.locator("#deepseek-settings-group button").click(),
  ]);
  await settingsPage.waitForLoadState("domcontentloaded");
  assert.match(settingsPage.url(), /deepseek\.html$/);
  await settingsPage.close();
  await panel.getByRole("button", { name: "Close settings" }).click();
  await panel.waitForTimeout(400);
  console.log("settings entry ok:", settingsText.replace(/\n/g, " / "));

  if (TOOL_MODE) {
    const first = await sendMessage(panel, "列出当前标签页", "MOCK-DEEPSEEK TOOL DONE");
    assert.deepStrictEqual(first.thinking, { type: "enabled" });
    assert.strictEqual(first.reasoning_effort, "high");
    const lines = fs
      .readFileSync(LOG, "utf8")
      .split("\n")
      .filter((line) => line.includes("POST "));
    assert.ok(lines.length >= 2, "expected a tool-call round trip");
    const second = JSON.parse(lines.at(-1).slice(lines.at(-1).indexOf("body=") + 5));
    const assistants = second.messages.filter((m) => m.role === "assistant");
    assert.ok(assistants.length > 0, "assistant tool call history missing");
    assert.ok(
      assistants.every((m) => typeof m.reasoning_content === "string"),
      "assistant reasoning_content missing in follow-up",
    );
    assert.ok(
      assistants.some((m) => Array.isArray(m.tool_calls) && m.tool_calls.length > 0),
      "tool call missing in follow-up history",
    );
    console.log("thinking + tool call round trip ok");
    assert.deepStrictEqual(panelErrors, []);
    await context.close();
    console.log("E2E TOOL PASS");
    return;
  }

  const first = await sendMessage(panel, "你好，测试 DeepSeek");
  assert.strictEqual(first.model, "deepseek-flash");
  assert.ok(Number.isInteger(first.max_tokens), "max_tokens must be sent");
  assert.ok(first.max_tokens <= 393216, `max_tokens too large: ${first.max_tokens}`);
  assert.strictEqual(first.max_completion_tokens, undefined);
  assert.deepStrictEqual(first.thinking, { type: "disabled" });
  assert.ok(Array.isArray(first.tools) && first.tools.length > 0);
  console.log("chat ok: max_tokens=", first.max_tokens, "thinking=disabled");

  await modelButton.click();
  await panel.locator(".wb-model-popover").getByText("DeepSeek V4 Pro", { exact: true }).click();
  await panel.getByRole("button", { name: "Switch and start new task" }).click();
  await panel.waitForTimeout(500);
  const second = await sendMessage(panel, "用 V4 Pro 回答");
  assert.strictEqual(second.model, "deepseek-v4-pro");
  console.log("model switch ok:", second.model);

  await panel.evaluate(async () => {
    const key = "sidepanel_connections";
    const stored = await chrome.storage.local.get(key);
    const all = stored[key].map((item) =>
      item.presetId === "deepseek" ? { ...item, thinking: true } : item,
    );
    await chrome.storage.local.set({ [key]: all });
  });
  await panel.waitForTimeout(500);
  const third = await sendMessage(panel, "打开思考模式");
  assert.deepStrictEqual(third.thinking, { type: "enabled" });
  assert.strictEqual(third.reasoning_effort, "high");
  console.log("thinking toggle ok: enabled + high");

  assert.deepStrictEqual(panelErrors, []);
  await panel.screenshot({ path: "/tmp/ds-sidepanel.png", fullPage: false });
  await context.close();
  console.log("E2E PASS");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
