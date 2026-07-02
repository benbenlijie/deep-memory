from __future__ import annotations

import asyncio
import sys

import pytest


def test_deep_memory_mcp_stdio_client_add_search_and_stats(tmp_path):
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    db = tmp_path / "mcp-client-smoke.db"

    async def run_smoke() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "deep_memory.mcp_server"],
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                tools = await session.list_tools()
                tool_names = {tool.name for tool in tools.tools}
                assert {"add", "search", "stats"}.issubset(tool_names)

                add_result = await session.call_tool(
                    "add",
                    {
                        "db_path": str(db),
                        "content": "MCP client smoke: agent can write through stdio",
                        "kind": "semantic",
                        "scope": "project",
                        "scope_id": "mcp-client-smoke",
                        "source": "mcp-client-test",
                    },
                )
                assert add_result.isError is False
                added = add_result.structuredContent
                assert added["content"] == "MCP client smoke: agent can write through stdio"
                assert added["scope"] == "project"
                assert added["scope_id"] == "mcp-client-smoke"

                search_result = await session.call_tool(
                    "search",
                    {
                        "db_path": str(db),
                        "query": "agent can write through stdio",
                        "scope": "project",
                        "scope_id": "mcp-client-smoke",
                        "include_global": False,
                        "limit": 3,
                    },
                )
                assert search_result.isError is False
                rows = search_result.structuredContent["result"]
                assert rows
                assert rows[0]["record"]["id"] == added["id"]
                assert rows[0]["record"]["content"] == added["content"]

                stats_result = await session.call_tool("stats", {"db_path": str(db)})
                assert stats_result.isError is False
                assert stats_result.structuredContent["semantic"] == 1
                assert stats_result.structuredContent["total"] == 1

    asyncio.run(run_smoke())
