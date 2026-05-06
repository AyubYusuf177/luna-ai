"""
tools.mock — Mock tool implementations for v0.1.

All mock tools implement the same interface as future real tools:
    Input:  ToolRequest  { tool_name, params, workflow_id, user_id }
    Output: ToolResult   { success, data, error, source }

'source' is set to "mock" for all tools in this package, so the
Response Composer and Event Logger can distinguish mock from live data.

Fixture files live in /mocks/ at the repo root.
"""
