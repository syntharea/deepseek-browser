# DeepSeek Browser Agent

An unofficial, reproducible build pipeline that turns an upstream Chrome browser-agent extension (MV3, version 2.0.24) into a DeepSeek-branded browser agent: DeepSeek-only model provider, API-key setup page, DeepSeek icons, welcome media, and a clean side-panel UI.

This repository contains **only original tooling, UI overlay, tests and documentation**. It does **not** redistribute the upstream extension bundle. You need your own local copy of the upstream 2.0.24 extension to build.

> Not affiliated with, endorsed by, or sponsored by DeepSeek or the upstream extension authors. DeepSeek and the DeepSeek logo are trademarks of their respective owner; they are used only to identify the model backend. See [NOTICE.md](NOTICE.md).

## What it does

- Registers a DeepSeek provider in the extension's existing OpenAI-compatible LLM layer (`https://api.deepseek.com/v1`).
- Discovers models from `GET /v1/models` (`deepseek-flash`, `deepseek-v4-pro` today; future models appear automatically).
- Adds a DeepSeek API-key page (API key, custom base URL, thinking toggle) and a visible "Set up DeepSeek" entry when no model is configured.
- Fixes two protocol differences: sends `max_tokens` (not `max_completion_tokens`) and caps output at DeepSeek's 384K limit.
- Supports DeepSeek thinking mode; when enabled, multi-turn tool calls round-trip `reasoning_content`.
- Rebrands the extension: name, short name, icons, welcome video/poster, titles and user-visible copy; removes legacy account/member/local-agent UI; drops the upstream signing key and update URL so the result has its own extension ID.

## Requirements

- Python 3.10+ with Pillow (`pip install pillow`)
- `ffmpeg`, `zip`
- Node.js 18+ and `npm` (tests only)
- A Chrome/Chromium executable (tests only)
- A local copy of the upstream browser-agent extension **2.0.24** (Chrome MV3)

## Build

```bash
git clone https://github.com/syntharea/deepseek-browser.git
cd deepseek-browser

# 1. Place the upstream 2.0.24 bundle at work/deepseek-ext
mkdir -p work
cp -a /path/to/upstream/2.0.24_0 work/deepseek-ext
chmod -R u+w work/deepseek-ext

# 2. Apply model support, rebranding and UI copy
python3 tools/patch_extension.py       # provider, discovery, max_tokens, thinking
python3 tools/rebrand_deepseek.py      # manifest, icons, copy, remove legacy account UI
python3 tools/cleanup_i18n.py          # account/membership wording
python3 tools/make_brand_assets.py     # downloads official mark, generates icons and welcome video

# 3. Package
(cd work/deepseek-ext && zip -qr ../../dist/deepseek-browser-2.0.24.zip . -x '_metadata/*')
```

Use `EXT_DIR=/path/to/ext` on any script to build in a different directory. `make_brand_assets.py` downloads the official mark from `deepseek.com` and stores it under `brand/` (gitignored), then generates `icon/16..256.png` and `welcome/browser-intro*.{mp4,jpg}`.

Load `work/deepseek-ext` in `chrome://extensions` with Developer mode enabled. Remove any previous copy first: the upstream signing key is removed, so this build gets a different extension ID.

## Configure

1. Open the side panel.
2. Click the blue **Set up DeepSeek** banner (or Settings → Models → DeepSeek).
3. Enter your DeepSeek API key (base URL optional; thinking optional) and click **Test and save**.
4. Pick `DeepSeek Flash` or `DeepSeek V4 Pro` in the model menu.

The API key is stored locally in `chrome.storage.local`. Output is capped at DeepSeek's documented 384K limit.

## Tests

```bash
npm install

# Terminal 1
node test/mock-deepseek.js

# Terminal 2
CHROME_PATH=/usr/bin/google-chrome node test/e2e.js
```

If `CHROME_PATH` is omitted, the test uses `chromium.executablePath()` from `playwright-core`; set it to your Chrome/Chromium binary if that path is unavailable.

Thinking + tools round trip:

```bash
MOCK_TOOL=1 node test/mock-deepseek.js
TOOL_MODE=1 CHROME_PATH=/usr/bin/google-chrome node test/e2e.js
```

The tests cover key configuration, model discovery, the setup entry/banner, a normal chat turn (`max_tokens=384000`, thinking off), model switching, a thinking turn, and a multi-turn tool call that requires `reasoning_content` to be returned. Use `EXT_DIR=/path/to/ext` to test a build outside `work/deepseek-ext`.

## Layout

| Path | Purpose |
| --- | --- |
| `overlay/` | DeepSeek setup page and side-panel settings entry |
| `tools/patch_extension.py` | Adds the DeepSeek provider/discovery/token fixes to the upstream bundle |
| `tools/rebrand_deepseek.py` | Manifest identity, copy, icons/welcome removal, legacy UI removal |
| `tools/cleanup_i18n.py` | Replaces account/membership wording with API-key setup |
| `tools/make_brand_assets.py` | Downloads the official mark and generates icons/posters/video |
| `test/mock-deepseek.js` | OpenAI-compatible mock, validates token/thinking/reasoning behaviour |
| `test/e2e.js` | Playwright end-to-end test with Chrome extensions |

## Legal

- The MIT license in this repository covers only the original code here. The upstream extension is a third-party work, is not included, and remains under its own license and terms. Obtain your own copy legally; do not redistribute it without permission.
- This project is an independent local modification. It is not an official DeepSeek product.
- DeepSeek and the DeepSeek logo are trademarks of their respective owner. They are used for identification only.
- No warranty; use at your own risk.

## References

- Model and pricing: https://api-docs.deepseek.com/quick_start/pricing
- Thinking mode: https://api-docs.deepseek.com/guides/thinking_mode
- Chat completions: https://api-docs.deepseek.com/api/create-chat-completion
