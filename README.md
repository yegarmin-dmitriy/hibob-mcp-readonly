# HiBob Read-Only MCP Extension

Internal MCP Desktop Extension for airSlate HR team.
Connects Claude Desktop to HiBob HRIS in read-only mode.

## For IT (installation)

1. Build: `mcpb pack`
2. Upload to Claude Enterprise: Org Settings → Extensions → Upload
3. Add to allowlist
4. Install on user's machine, enter credentials from 1Password vault `IT-Integrations`

## For HR users

The extension is pre-installed. Just ask Claude questions like:
- "Who's out today?"
- "How many people are in Engineering?"
- "Who's starting next week?"
- "What are the active goals for Marketing?"

## Security

- Read-only: no data can be modified through this extension
- Sensitive data (salaries, SSN, addresses) is never accessible
- Token is stored in your OS keychain (encrypted)
- All queries are logged in Claude Enterprise audit logs
