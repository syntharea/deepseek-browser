#!/usr/bin/env python3
"""Apply DeepSeek support to the upstream browser-agent extension bundle."""
from pathlib import Path
import os
import shutil
import sys

REPO = Path(__file__).resolve().parent.parent
ROOT = Path(os.environ.get("EXT_DIR", REPO / "work" / "deepseek-ext"))
OVERLAY = REPO / "overlay"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path.name}: expected 1 occurrence, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_background() -> None:
    p = ROOT / "background.js"
    replace_once(
        p,
        "var bc=[{id:`kimi-code`,label:`Kimi Code`,storageLabel:`Kimi Code`,"
        "defaultHost:`https://agent-gw.kimi.com`,discovery:`kimi-code-models`}];",
        "var bc=[{id:`kimi-code`,label:`Kimi Code`,storageLabel:`Kimi Code`,"
        "defaultHost:`https://agent-gw.kimi.com`,discovery:`kimi-code-models`},"
        "{id:`deepseek`,label:`DeepSeek`,storageLabel:`DeepSeek`,"
        "defaultHost:`https://api.deepseek.com`,discovery:`deepseek-models`}];",
    )
    replace_once(
        p,
        "function Tc(e,t,n){if(t===`kimi-code`)return wc();"
        "throw Error(`Unknown provider preset: ${t}`)}",
        "function Tc(e,t,n){if(t===`kimi-code`)return wc();"
        "if(t===`deepseek`){let n=e.replace(/\\/+$/,``);"
        "return/\\/v1$/.test(n)?n:n+`/v1`}"
        "throw Error(`Unknown provider preset: ${t}`)}",
    )
    replace_once(
        p,
        "case`kimi-code-models`:return nl({getAccessToken:al,fetchImpl:t,"
        "onDeclaredDefault:t=>lu(e.id,t)});default:",
        "case`kimi-code-models`:return nl({getAccessToken:al,fetchImpl:t,"
        "onDeclaredDefault:t=>lu(e.id,t)});case`deepseek-models`:"
        "return deepseekDiscover(e,t);default:",
    )
    replace_once(
        p,
        "}async function fu(){let e=await jc();",
        "}async function deepseekDiscover(e,t){let n=t??fetch,"
        "r=Ec(e).replace(/\\/+$/,``),i=/\\/v1$/.test(r)?r:r+`/v1`;let a;"
        "try{a=await n(i+`/models`,{headers:{Authorization:`Bearer ${e.apiKey}`}})}"
        "catch(e){throw Rc(e,`DeepSeek`)}"
        "if(a.status===401||a.status===403||!a.ok)throw zc(`DeepSeek`,a.status);"
        "let o=[];try{let e=await a.json();"
        "for(let t of Array.isArray(e?.data)?e.data:[])"
        "if(t&&typeof t.id===`string`&&t.id){let e=deepseekMeta(t.id);"
        "o.push({modelId:t.id,label:e.label,route:`chat-completions`,"
        "...e.maxContextTokens===void 0?{}:{maxContextTokens:e.maxContextTokens}})}"
        "}catch(e){throw Rc(e,`DeepSeek`)}"
        "if(o.length===0)throw Rc(Error(`DeepSeek returned no models`),`DeepSeek`);"
        "return o}"
        "function deepseekMeta(e){switch(e){"
        "case`deepseek-flash`:return{label:`DeepSeek Flash`,maxContextTokens:1000000};"
        "case`deepseek-v4-pro`:return{label:`DeepSeek V4 Pro`,maxContextTokens:1000000};"
        "case`deepseek-chat`:return{label:`DeepSeek Chat`,maxContextTokens:1000000};"
        "case`deepseek-reasoner`:return{label:`DeepSeek Reasoner`,maxContextTokens:1000000};"
        "default:return{label:e,maxContextTokens:1000000}}}"
        "async function fu(){let e=await jc();",
    )
    replace_once(
        p,
        "return{id:n,label:typeof r==`string`&&r?r:o.storageLabel,"
        "presetId:o.id,...l?{hostOverride:l}:{},apiKey:i}",
        "return{id:n,label:typeof r==`string`&&r?r:o.storageLabel,"
        "presetId:o.id,...l?{hostOverride:l}:{},"
        "...typeof t.thinking==`boolean`?{thinking:t.thinking}:{},apiKey:i}",
    )
    replace_once(
        p,
        "this._baseUrl=e.baseUrl??Cy(`KIMI_BASE_URL`)??`https://api.moonshot.ai/v1`,"
        "this._defaultHeaders=e.defaultHeaders",
        "this._baseUrl=e.baseUrl??Cy(`KIMI_BASE_URL`)??`https://api.moonshot.ai/v1`,"
        "this._maxTokensField=e.maxTokensField,this._defaultHeaders=e.defaultHeaders",
    )
    replace_once(
        p,
        "_model;_stream;_apiKey;_baseUrl;_defaultHeaders;",
        "_model;_stream;_apiKey;_baseUrl;_maxTokensField;_defaultHeaders;",
    )
    replace_once(
        p,
        "a.max_completion_tokens===void 0&&a.max_tokens!==void 0&&"
        "(a.max_completion_tokens=a.max_tokens),delete a.max_tokens;",
        "a.max_completion_tokens===void 0&&a.max_tokens!==void 0&&"
        "(a.max_completion_tokens=a.max_tokens),"
        "this._maxTokensField===`max_tokens`?"
        "a.max_completion_tokens!==void 0&&"
        "(a.max_tokens=a.max_completion_tokens,delete a.max_completion_tokens):"
        "delete a.max_tokens;",
    )
    replace_once(
        p,
        "case`kimi`:case`chat-completions`:{let t=new ky({apiKey:e.apiKey,"
        "baseUrl:e.baseUrl,model:e.model,",
        "case`kimi`:case`chat-completions`:{let t=new ky({apiKey:e.apiKey,"
        "baseUrl:e.baseUrl,model:e.model,maxTokensField:e.maxTokensField,",
    )
    replace_once(
        p,
        "RT({route:e.route,baseUrl:e.baseUrl,apiKey:e.apiKey??``,model:e.model,"
        "thinkingLevel:e.thinkingLevel,",
        "RT({route:e.route,baseUrl:e.baseUrl,apiKey:e.apiKey??``,model:e.model,"
        "thinkingLevel:e.thinkingLevel,maxTokensField:e.maxTokensField??"
        "(/api\\.deepseek\\.com/i.test(e.baseUrl)?`max_tokens`:void 0),",
    )
    replace_once(
        p,
        "completionBudgetConfig:Ny({})",
        "completionBudgetConfig:Ny(e.maxOutputSize===void 0?{}:"
        "{maxOutputSize:e.maxOutputSize})",
    )
    replace_once(
        p,
        "return oE({route:e.route,baseUrl:Dc(i,e.route),authResolver:al,"
        "model:e.modelId,systemPrompt:t,trackContext:a})",
        "return oE({route:e.route,baseUrl:Dc(i,e.route),authResolver:al,"
        "maxOutputSize:i.presetId===`deepseek`?384000:void 0,"
        "model:e.modelId,systemPrompt:t,trackContext:a})",
    )
    replace_once(
        p,
        "baseUrl:Dc(o,e.route),...s?{authResolver:al}:{apiKey:o.apiKey},"
        "model:e.modelId,systemPrompt:",
        "baseUrl:Dc(o,e.route),...s?{authResolver:al}:{apiKey:o.apiKey},"
        "maxTokensField:o.presetId===`deepseek`?`max_tokens`:void 0,"
        "maxOutputSize:o.presetId===`deepseek`?384000:void 0,"
        "model:e.modelId,systemPrompt:",
    )
    replace_once(
        p,
        "...e.thinkingLevel===void 0?{}:{thinkingLevel:e.thinkingLevel},"
        "trackContext:{kind:`chat`",
        "...(o.presetId===`deepseek`?(o.thinking?{thinkingLevel:`high`}:"
        "{thinkingLevel:`off`}):(e.thinkingLevel===void 0?{}:"
        "{thinkingLevel:e.thinkingLevel})),trackContext:{kind:`chat`",
    )
    replace_once(
        p,
        "return i.apiKey?oE({route:e.route,baseUrl:Dc(i,e.route),apiKey:i.apiKey,"
        "model:e.modelId,systemPrompt:t,trackContext:a}):null",
        "return i.apiKey?oE({route:e.route,baseUrl:Dc(i,e.route),apiKey:i.apiKey,"
        "maxTokensField:i.presetId===`deepseek`?`max_tokens`:void 0,"
        "maxOutputSize:i.presetId===`deepseek`?384000:void 0,"
        "model:e.modelId,systemPrompt:t,trackContext:a,"
        "...i.presetId===`deepseek`?(i.thinking?{thinkingLevel:`high`}:"
        "{thinkingLevel:`off`}):{}}):null",
    )


def patch_sidepanel() -> None:
    p = ROOT / "chunks" / "sidepanel-CUbsl7eV.js"
    replace_once(
        p,
        "var fE=[{id:`kimi-code`,label:`Kimi Code`,storageLabel:`Kimi Code`,"
        "defaultHost:`https://agent-gw.kimi.com`,discovery:`kimi-code-models`}];",
        "var fE=[{id:`kimi-code`,label:`Kimi Code`,storageLabel:`Kimi Code`,"
        "defaultHost:`https://agent-gw.kimi.com`,discovery:`kimi-code-models`},"
        "{id:`deepseek`,label:`DeepSeek`,storageLabel:`DeepSeek`,"
        "defaultHost:`https://api.deepseek.com`,discovery:`deepseek-models`}];",
    )
    replace_once(
        p,
        "case`kimi-code-models`:return yj({getAccessToken:LT,fetchImpl:t,"
        "onDeclaredDefault:t=>Nj(e.id,t)});default:",
        "case`kimi-code-models`:return yj({getAccessToken:LT,fetchImpl:t,"
        "onDeclaredDefault:t=>Nj(e.id,t)});case`deepseek-models`:"
        "return deepseekDiscover(e,t);default:",
    )
    replace_once(
        p,
        "}async function Ij(){let e=await bE();",
        "}async function deepseekDiscover(e,t){let n=t??fetch,"
        "r=(e.hostOverride||mE(e.presetId).defaultHost).replace(/\\/+$/,``),"
        "i=/\\/v1$/.test(r)?r:r+`/v1`;let a;"
        "try{a=await n(i+`/models`,{headers:{Authorization:`Bearer ${e.apiKey}`}})}"
        "catch(e){throw tj(e,`DeepSeek`)}"
        "if(a.status===401||a.status===403||!a.ok)throw nj(`DeepSeek`,a.status);"
        "let o=[];try{let e=await a.json();"
        "for(let t of Array.isArray(e?.data)?e.data:[])"
        "if(t&&typeof t.id===`string`&&t.id){let e=deepseekMeta(t.id);"
        "o.push({modelId:t.id,label:e.label,route:`chat-completions`,"
        "...e.maxContextTokens===void 0?{}:{maxContextTokens:e.maxContextTokens}})}"
        "}catch(e){throw tj(e,`DeepSeek`)}"
        "if(o.length===0)throw tj(Error(`DeepSeek returned no models`),`DeepSeek`);"
        "return o}"
        "function deepseekMeta(e){switch(e){"
        "case`deepseek-flash`:return{label:`DeepSeek Flash`,maxContextTokens:1000000};"
        "case`deepseek-v4-pro`:return{label:`DeepSeek V4 Pro`,maxContextTokens:1000000};"
        "case`deepseek-chat`:return{label:`DeepSeek Chat`,maxContextTokens:1000000};"
        "case`deepseek-reasoner`:return{label:`DeepSeek Reasoner`,maxContextTokens:1000000};"
        "default:return{label:e,maxContextTokens:1000000}}}"
        "async function Ij(){let e=await bE();",
    )
    replace_once(
        p,
        "return{id:n,label:typeof r==`string`&&r?r:o.storageLabel,"
        "presetId:o.id,...l?{hostOverride:l}:{},apiKey:i}",
        "return{id:n,label:typeof r==`string`&&r?r:o.storageLabel,"
        "presetId:o.id,...l?{hostOverride:l}:{},"
        "...typeof t.thinking==`boolean`?{thinking:t.thinking}:{},apiKey:i}",
    )


def patch_html() -> None:
    p = ROOT / "sidepanel.html"
    text = p.read_text(encoding="utf-8")
    if "deepseek-ui.js" not in text:
        text = text.replace(
            "<body>\n  <div id=\"root\"></div>\n</body>",
            "<body>\n  <div id=\"root\"></div>\n"
            "  <script src=\"deepseek-ui.js\"></script>\n</body>",
        )
        p.write_text(text, encoding="utf-8")


def copy_overlay() -> None:
    for name in ("deepseek.html", "deepseek.js", "deepseek-ui.js"):
        source = OVERLAY / name
        if not source.exists():
            raise SystemExit(f"missing overlay file: {source}")
        shutil.copy2(source, ROOT / name)


def main() -> None:
    if not (ROOT / "manifest.json").exists():
        raise SystemExit(f"upstream extension not found at {ROOT}")
    copy_overlay()
    patch_background()
    patch_sidepanel()
    patch_html()
    print("patched", ROOT)


if __name__ == "__main__":
    sys.exit(main())
