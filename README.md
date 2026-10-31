# ClearWorks MCP Server

Let any AI agent (Claude, Hermes, etc.) discover and order ClearWorks services over MCP.

## Tools
- `list_services` — all services + prices
- `get_service {id}` — one service detail
- `place_order {service, name, email, brief}` — creates a real order, returns reference (CW-XXXXXX)
- `check_order {reference?}` — order status

## Install (Claude Desktop / any MCP client)
```json
{"mcpServers": {"clearworks": {"command": "python3", "args": ["/path/to/clearworks_mcp_server.py"]}}}
```

## Tested
initialize → tools/list → place_order (CW-717293 created live) → check_order (found) ✅
