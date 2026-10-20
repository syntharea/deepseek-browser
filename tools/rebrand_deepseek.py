#!/usr/bin/env python3
"""Rebrand the patched extension as DeepSeek and remove legacy account UI."""
from pathlib import Path
import json
import os
import re
import shutil

ROOT = Path(__file__).resolve().parent.parent
EXT = Path(os.environ.get("EXT_DIR", ROOT / "work" / "deepseek-ext"))

REPLACEMENTS = [
    ("KIMI", "DEEPSEEK"),
    ("Kimi", "DeepSeek"),
    ("kimi", "deepseek"),
    # branding cleanup after the mechanical rename
    ("DeepSeek Member credits", "DeepSeek API credits"),
    ("DeepSeek Member models", "DeepSeek models"),
    ("DeepSeek Member", "DeepSeek"),
    ("DeepSeek 会员", "DeepSeek"),
    ("DeepSeek account required", "DeepSeek API key required"),
    ("需登录 DeepSeek 账号", "需配置 DeepSeek API Key"),
    ("Log in to use DeepSeek models", "Configure DeepSeek to use models"),
    ("登录以使用 DeepSeek 模型", "配置 DeepSeek 后使用模型"),
    ("Log in to chat with DeepSeek", "Configure DeepSeek to start"),
    ("登录后，在浏览器侧边栏与 DeepSeek 对话", "配置 DeepSeek 后，在浏览器侧边栏开始对话"),
    ("DeepSeek Work", "本地 Agent"),
    ("DeepSeek Code", "本地 Agent"),
    ("搭配本地 Agent、本地 Agent 或者其他本地 Agent", "搭配其他本地 Agent"),
    ("Works with 本地 Agent, 本地 Agent, and other local agents", "Works with other local agents"),
    ("https://www.deepseek.ai", "https://www.deepseek.com"),
    ("https://www.deepseek.com/products/deepseek-webbridge", "https://www.deepseek.com"),
]


def replace_all(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def main() -> None:
    for path in list(EXT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".js", ".html", ".css", ".json"}:
            continue
        if "_metadata" in path.parts:
            continue
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = replace_all(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    # manifest: independent DeepSeek identity, no store key / update channel
    manifest_path = EXT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("key", None)
    manifest.pop("update_url", None)
    manifest["name"] = "DeepSeek"
    manifest["short_name"] = "DeepSeek"
    manifest["homepage_url"] = "https://www.deepseek.com"
    manifest["content_security_policy"] = {
        "extension_pages": "script-src 'self'; object-src 'self'; connect-src 'self' ws://*:* wss://*:* http://*:* https://*:*;"
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=3, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # the avatar asset is now referenced as deepseek-avatar.svg after the text pass
    for path in EXT.rglob("*.js"):
        text = path.read_text(encoding="utf-8", errors="replace")
        text = text.replace("icon/deepseek-avatar.svg", "icon/128.png")
        path.write_text(text, encoding="utf-8")

    legacy_avatar = EXT / "icon" / "deepseek-avatar.svg"
    if legacy_avatar.exists():
        legacy_avatar.unlink()
    legacy_avatar = EXT / "icon" / "kimi-avatar.svg"
    if legacy_avatar.exists():
        legacy_avatar.unlink()

    # remove third-party verification metadata and unused onboarding screenshots
    shutil.rmtree(EXT / "_metadata", ignore_errors=True)
    shutil.rmtree(EXT / "onboarding", ignore_errors=True)

    # keep only the DeepSeek provider preset
    for name in ["background.js", "chunks/sidepanel-CUbsl7eV.js"]:
        path = EXT / name
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"\{id:`deepseek-code`,label:[^}]*?discovery:`deepseek-code-models`\},",
            "",
            text,
        )
        text = text.replace(
            "async function fu(){let e=await jc();if(e.some(e=>e.presetId===`deepseek-code`)||!await sl())return e;let t=Sc(`deepseek-code`);return[...e,{id:t.id,label:t.storageLabel,presetId:`deepseek-code`,apiKey:``}]}",
            "async function fu(){return await jc()}",
        )
        text = text.replace(
            "async function Ij(){let e=await bE();if(e.some(e=>e.presetId===`deepseek-code`)||!await RT())return e;let t=mE(`deepseek-code`);return[...e,{id:t.id,label:t.storageLabel,presetId:`deepseek-code`,apiKey:``}]}",
            "async function Ij(){return await bE()}",
        )
        path.write_text(text, encoding="utf-8")

    print("rebranded", EXT)


if __name__ == "__main__":
    main()
