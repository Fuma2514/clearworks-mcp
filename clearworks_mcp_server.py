#!/usr/bin/env python3
"""ClearWorks MCP Server — lets any AI agent discover & buy services from ClearWorks.

Tools:
  list_services   — list all ClearWorks services with prices
  get_service     — details of one service
  place_order     — create an order (returns reference code)
  check_order     — check order status by reference

Run:  python3 clearworks_mcp_server.py   (stdio MCP, JSON-RPC 2.0)
Spec: MCP 2025-03-26 over stdio, no auth needed for read; orders need email.
"""
import json, sys, urllib.request

SITE = "https://ws-11916a11af7614fd.lightvela.site"
RELEASE = None  # fetched at runtime

def _release():
    global RELEASE
    if not RELEASE:
        req = urllib.request.Request(SITE + "/")
        html = urllib.request.urlopen(req).read().decode()
        import re
        m = re.search(r'LIGHTVELA_RELEASE_ID__="([a-z0-9-]+)"', html)
        RELEASE = m.group(1)
    return RELEASE

def _api(path, payload=None):
    hdrs = {"X-Website-Release": _release(), "Content-Type": "application/json",
            "Origin": SITE, "User-Agent": "clearworks-mcp/1.0"}
    if payload is None:
        req = urllib.request.Request(SITE + path, headers=hdrs)
    else:
        req = urllib.request.Request(SITE + path, data=json.dumps(payload).encode(), headers=hdrs, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

SERVICES = [
    {"id": "data-cleaning",    "name": "Data Cleaning ($10–$15 / batch)",           "turnaround": "1 day"},
    {"id": "tracking-extract", "name": "Tracking Number Extraction ($10–$15 / batch)","turnaround": "1 day"},
    {"id": "web-scraping",     "name": "Web Scraping & Research ($5)",              "turnaround": "1 day"},
    {"id": "translation",      "name": "Translation ID ⇄ EN ($5)",                "turnaround": "1 day"},
    {"id": "letters",          "name": "Business Letters & Documents ($5)",         "turnaround": "1 day"},
    {"id": "website-qa",       "name": "Website QA Audit ($5)",                     "turnaround": "1 day"},
    {"id": "design",           "name": "Graphic Design ($5)",                       "turnaround": "1 day"},
    {"id": "research",         "name": "Research Summary ($5)",                     "turnaround": "1 day"},
    {"id": "enrichment",       "name": "Data Enrichment ($5)",                      "turnaround": "1 day"},
    {"id": "resume-rewrite",  "name": "Resume & LinkedIn Rewrite ($5)",            "turnaround": "1 day"},
    {"id": "prompt-pack",      "name": "Jualan Pakai AI — Prompt Pack Rp 29.000","turnaround": "instant"},
    {"id": "custom",           "name": "Custom Commission (quoted)",                "turnaround": "1-3 days"},
]

def tool_list_services(args):
    return {"services": SERVICES, "count": len(SERVICES), "site": SITE}

def tool_get_service(args):
    sid = (args or {}).get("id", "")
    for s in SERVICES:
        if s["id"] == sid:
            return s
    return {"error": f"unknown service id '{sid}'", "available": [s["id"] for s in SERVICES]}

def tool_place_order(args):
    a = args or {}
    for f in ("service", "name", "email", "brief"):
        if not a.get(f):
            return {"error": f"missing field '{f}'", "required": ["service","name","email","brief"]}
    ids = {s["id"]: s["name"] for s in SERVICES}
    svc = ids.get(a["service"], a["service"])
    try:
        r = _api("/api/orders", {"service": svc, "name": a["name"], "email": a["email"], "brief": a["brief"]})
        return {"ok": True, "reference": r.get("reference") or r.get("ref") or "see-response", "raw": r}
    except Exception as e:
        return {"error": str(e)[:200], "hint": "order form at " + SITE}

def tool_check_order(args):
    try:
        r = _api("/api/orders")
        orders = r.get("orders", [])
        ref = (args or {}).get("reference", "")
        if ref:
            hits = [o for o in orders if ref.lower() in json.dumps(o).lower()]
            return {"found": bool(hits), "orders": hits}
        return {"count": len(orders), "latest": orders[-5:]}
    except Exception as e:
        return {"error": str(e)[:200]}

TOOLS = {
    "list_services": (tool_list_services, "List all ClearWorks services with prices and turnaround."),
    "get_service":   (tool_get_service,   "Get one service's details. Args: {id}"),
    "place_order":   (tool_place_order,   "Create a real order. Args: {service, name, email, brief}. Escrow protected."),
    "check_order":   (tool_check_order,   "Check order status. Args: {reference} (optional)."),
}

def rpc_handler(msg):
    m = msg.get("method", "")
    if m == "initialize":
        return {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}},
                "serverInfo": {"name": "clearworks", "version": "1.0.0"}}
    if m == "notifications/initialized":
        return None
    if m == "tools/list":
        return {"tools": [{"name": n, "description": d, "inputSchema": {"type": "object"}}
                          for n, (f, d) in TOOLS.items()]}
    if m == "tools/call":
        name = msg["params"]["name"]
        if name in TOOLS:
            result = TOOLS[name][0](msg["params"].get("arguments"))
            return {"content": [{"type": "text", "text": json.dumps(result, indent=1)}]}
        return {"content": [{"type": "text", "text": f"unknown tool {name}"}], "isError": True}
    if m == "ping":
        return {}
    return {"error": {"code": -32601, "message": f"method not found: {m}"}}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        out = rpc_handler(msg)
        if out is None:
            continue
        resp = {"jsonrpc": "2.0", "id": msg.get("id")}
        if "error" in out:
            resp["error"] = out.pop("error")
        elif "content" in out or "protocolVersion" in out or "tools" in out:
            resp["result"] = out
        else:
            resp["result"] = out
        print(json.dumps(resp), flush=True)

if __name__ == "__main__":
    main()
