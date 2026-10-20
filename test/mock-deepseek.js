const http = require("http");
const fs = require("fs");

const PORT = Number(process.env.PORT || 8787);
const LOG = process.env.LOG || "/tmp/mock-deepseek.log";
const TOOL_MODE = process.env.MOCK_TOOL === "1";
let requestCount = 0;

function log(line) {
  fs.appendFileSync(LOG, `${new Date().toISOString()} ${line}\n`);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://127.0.0.1:${PORT}`);
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "*",
      "Access-Control-Allow-Methods": "*",
    });
    res.end();
    return;
  }
  if (req.method === "GET" && url.pathname.endsWith("/models")) {
    const auth = req.headers.authorization || "";
    log(`GET ${url.pathname} auth=${auth.slice(0, 22)}`);
    if (auth !== "Bearer sk-test-deepseek") {
      res.writeHead(401, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: { message: "Authentication Fails" } }));
      return;
    }
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        object: "list",
        data: [
          { id: "deepseek-flash", object: "model", owned_by: "deepseek" },
          { id: "deepseek-v4-pro", object: "model", owned_by: "deepseek" },
        ],
      }),
    );
    return;
  }
  if (req.method === "POST" && url.pathname.endsWith("/chat/completions")) {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    let body;
    try {
      body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    } catch {
      body = null;
    }
    log(`POST ${url.pathname} body=${JSON.stringify(body)}`);
    if (!body || !Array.isArray(body.messages)) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: { message: "bad request" } }));
      return;
    }
    if (body.max_completion_tokens !== undefined) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          error: {
            message: "max_completion_tokens is not accepted; use max_tokens",
          },
        }),
      );
      return;
    }
    if (body.max_tokens === undefined) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: { message: "max_tokens is required" } }));
      return;
    }
    requestCount += 1;
    const assistantMessages = body.messages.filter((m) => m.role === "assistant");
    if (
      TOOL_MODE &&
      body.thinking?.type === "enabled" &&
      assistantMessages.some((m) => typeof m.reasoning_content !== "string")
    ) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          error: { message: "reasoning_content must be passed back with tools" },
        }),
      );
      return;
    }
    const model = body.model || "deepseek-flash";
    const create = Math.floor(Date.now() / 1000);
    const id = `chatcmpl-mock-${Date.now()}`;
    const hasToolCall = assistantMessages.some(
      (m) => Array.isArray(m.tool_calls) && m.tool_calls.length > 0,
    );
    const content = TOOL_MODE && !hasToolCall ? "" : TOOL_MODE ? "MOCK-DEEPSEEK TOOL DONE" : "MOCK-DEEPSEEK OK";
    if (!body.stream) {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          id,
          object: "chat.completion",
          created: create,
          model,
          choices: [
            {
              index: 0,
              message: { role: "assistant", content },
              finish_reason: "stop",
            },
          ],
          usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        }),
      );
      return;
    }
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    });
    const send = (payload) => res.write(`data: ${JSON.stringify(payload)}\n\n`);
    send({
      id,
      object: "chat.completion.chunk",
      created: create,
      model,
      choices: [{ index: 0, delta: { role: "assistant" }, finish_reason: null }],
    });
    if (TOOL_MODE && !hasToolCall) {
      send({
        id,
        object: "chat.completion.chunk",
        created: create,
        model,
        choices: [
          {
            index: 0,
            delta: { reasoning_content: "I should list the open tabs first." },
            finish_reason: null,
          },
        ],
      });
      send({
        id,
        object: "chat.completion.chunk",
        created: create,
        model,
        choices: [
          {
            index: 0,
            delta: {
              tool_calls: [
                {
                  index: 0,
                  id: "call_mock_1",
                  type: "function",
                  function: { name: "list_tabs", arguments: "{}" },
                },
              ],
            },
            finish_reason: null,
          },
        ],
      });
      send({
        id,
        object: "chat.completion.chunk",
        created: create,
        model,
        choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }],
        usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
      });
    } else {
      for (const piece of content.match(/.{1,16}/gs) || []) {
        send({
          id,
          object: "chat.completion.chunk",
          created: create,
          model,
          choices: [{ index: 0, delta: { content: piece }, finish_reason: null }],
        });
      }
      send({
        id,
        object: "chat.completion.chunk",
        created: create,
        model,
        choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
        usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
      });
    }
    res.write("data: [DONE]\n\n");
    res.end();
    return;
  }
  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: { message: "not found" } }));
});

server.listen(PORT, "127.0.0.1", () => {
  log(`listening on ${PORT}`);
  console.log(`mock deepseek on http://127.0.0.1:${PORT}`);
});
