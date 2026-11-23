# Installing the tactica. MCP server (for AI assistants)

tactica. is a **remote** MCP server. There's nothing to install, build or run locally, and no API key.

1. Add a remote MCP server with these settings:
   - name: `tactica`
   - transport: Streamable HTTP
   - URL: `https://app.tacticafootball.co.uk/x402/mcp`
   - no headers and no authentication
2. Example `mcpServers` entry:
   ```json
   { "mcpServers": { "tactica": { "type": "http", "url": "https://app.tacticafootball.co.uk/x402/mcp" } } }
   ```
3. Check it works by calling `list_fixtures`. It's free and should return upcoming fixtures with a `fixtureId` for each.
4. `get_track_record` is also free.
5. The other tools are paid per call in USDC on Base using x402:
   - without a payment they return `isError: true` and a payment request. That's expected, not a fault;
   - only pay if the user has set up an x402 wallet and agreed to the price shown in the request.
6. Tell the user that tactica. is 18+ only, and that forecasts and picks are information, not betting or financial advice.
