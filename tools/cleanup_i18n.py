#!/usr/bin/env python3
"""Replace the remaining account/membership wording with DeepSeek API setup."""
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parent.parent
EXT = Path(os.environ.get("EXT_DIR", ROOT / "work" / "deepseek-ext"))

ZH = "zh"
EN = "en"

VALUES = {
    "bg.noModelSignin": (
        "在设置中配置 DeepSeek API Key 后，我来帮你处理这个任务。配置完成后会自动继续。",
        "Set up a DeepSeek API key in Settings and I’ll take care of this task. I’ll continue automatically when setup is complete.",
    ),
    "bg.noModelsRetry": (
        "DeepSeek 没有返回可用模型—检查 API Key、余额或网络后点这里重试",
        "DeepSeek returned no usable models — check the API key, balance, or network, then retry here",
    ),
    "bg.noModelsLater": (
        "DeepSeek 没有返回可用模型—检查 API Key、余额或网络后再试",
        "DeepSeek returned no usable models — check the API key, balance, or network and try again",
    ),
    "bg.failQuotaResend": (
        "DeepSeek API 余额不足—充值或稍后重试，再点这里重新发送",
        "DeepSeek API balance is insufficient — top up or wait, then resend here",
    ),
    "bg.failQuotaLater": (
        "DeepSeek API 余额不足—充值或稍后重试",
        "DeepSeek API balance is insufficient — top up or wait, then try again",
    ),
    "bg.reloginResend": (
        "DeepSeek 配置已失效（HTTP {status}）—到设置里检查 API Key 后再发送",
        "DeepSeek configuration expired (HTTP {status}) — check the API key in Settings, then resend",
    ),
    "bg.reloginLater": (
        "DeepSeek 配置已失效（HTTP {status}）—到设置里检查 API Key 后再试",
        "DeepSeek configuration expired (HTTP {status}) — check the API key in Settings, then retry",
    ),
    "settings.signInPrompt": (
        "配置 DeepSeek API Key 后使用模型",
        "Configure a DeepSeek API key to use models",
    ),
    "settings.myQuota": ("DeepSeek 用量", "DeepSeek usage"),
    "settings.signOut": ("清除配置", "Remove configuration"),
    "onboarding.agent.tag": ("本地服务", "Local service"),
    "onboarding.agent.desc": (
        "搭配本地 Agent，远程操控你的浏览器",
        "Works with a local agent to drive your browser.",
    ),
    "capacity.memberBadge": ("可用", "Available"),
    "wall.title": ("配置 DeepSeek 后继续", "Set up DeepSeek to continue"),
    "wall.desc": (
        "在设置中配置 DeepSeek API Key，然后在浏览器侧边栏开始对话",
        "Add a DeepSeek API key in Settings, then chat in the side panel.",
    ),
    "wall.login": ("去配置", "Set up"),
    "wall.awaitingTitle": (
        "请在新打开的页面完成 DeepSeek 配置",
        "Finish setting up DeepSeek on the page that just opened",
    ),
    "wall.awaitingSwitchTitle": (
        "请在打开的页面完成配置",
        "Finish setup on the page that just opened",
    ),
    "wall.successTitle": ("配置完成", "Setup complete"),
    "wall.awaitingSwitchAuth": (
        "请在打开的页面完成配置，这里会自动继续",
        "Finish setup on the page that just opened — this will continue on its own",
    ),
    "wall.verifying": ("正在检查 DeepSeek 配置…", "Checking DeepSeek configuration…"),
    "wall.probing": ("正在检测配置…", "Checking configuration…"),
    "wall.switchToChinaLogin": ("切换配置入口", "Switch setup page"),
    "wall.switchToOverseasLogin": ("切换配置入口", "Switch setup page"),
    "notice.action.signin": ("配置 DeepSeek", "Set up DeepSeek"),
    "notice.action.relogin": ("重新配置", "Reconfigure"),
    "notice.action.upgrade": ("配置 DeepSeek", "Set up DeepSeek"),
    "guest.signinPending": (
        "请在新打开的页面完成 DeepSeek 配置，完成后我会自动继续。",
        "Finish setting up DeepSeek on the page that just opened. I’ll continue automatically.",
    ),
    "guest.signinVerifying": ("正在检查 DeepSeek 配置…", "Checking DeepSeek setup…"),
    "guest.signinCancel": ("取消配置", "Cancel setup"),
    "bg.reasonRelogin": ("DeepSeek 配置已失效", "DeepSeek configuration expired"),
    "bg.reasonSignedOut": ("DeepSeek 未配置", "DeepSeek not configured"),
    "bg.reasonQuota": ("DeepSeek API 余额不足", "DeepSeek API balance is insufficient"),
    "capacity.upgradeBody": ("{name} 当前不可用", "{name} is unavailable"),
    "capacity.upgradeConfirm": ("去配置", "Set up"),
    "guideA.title": ("需要配置 DeepSeek", "DeepSeek setup required"),
    "guideA.desc": (
        "尚未配置 DeepSeek API Key，配置后即可在浏览器侧边栏使用本插件",
        "DeepSeek isn’t configured yet — add an API key to use this extension in the side panel.",
    ),
    "guideA.descWithAccount": (
        "尚未配置 DeepSeek API Key，配置后即可在浏览器侧边栏使用本插件",
        "DeepSeek isn’t configured yet — add an API key to use this extension in the side panel.",
    ),
    "guideA.upgrade": ("配置 DeepSeek", "Set up DeepSeek"),
    "guideA.awaitingPayment": (
        "DeepSeek 配置页已打开，完成后回到这里，配置会立即生效",
        "The DeepSeek setup page is open. Come back when you’re done — it takes effect immediately.",
    ),
    "guideA.recheckFailed": (
        "暂时无法检查 DeepSeek 配置，请检查网络后重试",
        "Can’t check your DeepSeek setup right now. Check your connection and try again.",
    ),
    "signin.authorize": ("配置", "Set up"),
    "signin.reauthorize": ("重新配置", "Reconfigure"),
    "signin.timeout": ("等待配置超时，请重试", "Setup timed out. Try again"),
    "signin.staleSession": (
        "配置已失效，请重新配置后再试",
        "Your setup has expired. Reconfigure and retry",
    ),
    "signin.rateLimited": (
        "配置请求太频繁，请约 {seconds} 秒后重试",
        "Too many setup attempts. Try again in about {seconds} seconds",
    ),
    "signin.failed": ("配置失败，请重试", "Setup failed. Try again"),
    "signin.verifyFailed": (
        "暂时无法确认配置，请检查网络后重试",
        "Can’t confirm your setup right now. Check your connection and try again",
    ),
    "signin.succeeded": ("配置完成，可以开始使用了", "Configured — you’re ready to go"),
    "signin.upgradePlan": ("配置 DeepSeek", "Set up DeepSeek"),
}


def is_zh(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def patch(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    changed = 0
    for key, (zh, en) in VALUES.items():
        pattern = re.compile(r'("' + re.escape(key) + r'":)`([^`]*)`')

        def repl(match: re.Match) -> str:
            value = match.group(2)
            return f'{match.group(1)}`{zh if is_zh(value) else en}`'

        text, count = pattern.subn(repl, text)
        changed += count
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main() -> None:
    total = 0
    for name in ["background.js", "chunks/i18n-pVQL_Rp2.js", "chunks/sidepanel-CUbsl7eV.js"]:
        total += patch(EXT / name)
    print("updated", total, "translation values")


if __name__ == "__main__":
    main()
