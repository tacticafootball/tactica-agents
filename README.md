# tactica. for AI agents

Football intelligence for the **English Premier League (EPL), EFL Championship, EFL League 1 & EFL League 2**, sold per call to AI agents. There's no account, no API key and no subscription: an agent pays in USDC on Base using the open [x402](https://x402.org) standard, and gets the answer in the same request.

- **MCP server:** `https://app.tacticafootball.co.uk/x402/mcp` (Streamable HTTP, no auth)
- **HTTP API:** `https://app.tacticafootball.co.uk/x402/v1` (the free catalogue, with current USDC prices)
- **OpenAPI:** `https://app.tacticafootball.co.uk/openapi.json`
- **MCP Registry:** `uk.co.tacticafootball/tactica`
- **For AI agents (prices, MCP, examples):** [tacticafootball.co.uk/agents](https://www.tacticafootball.co.uk/agents?utm_source=github-tactica-agents)
- **Website:** [tacticafootball.co.uk](https://tacticafootball.co.uk)

This repo holds listing files and examples only. The tactica. service itself isn't open source.

## WHAT YOU CAN ASK FOR

| MCP tool | HTTP route | What you get | Price (USDC) |
|---|---|---|---|
| `list_fixtures` | (MCP only) | Upcoming fixtures with ids, kick-off times, teams and league | Free |
| `get_track_record` | `GET /x402/v1/track-record` | Our settled record: hit rate and profit by market, league and tier | Free |
| `get_match_forecast` | `GET /x402/v1/forecast/{fixtureId}` | Home, draw and away chances and expected goals for one match | 0.25 |
| `get_case_file` | `GET /x402/v1/case-files/{fixtureId}` | The full Case File: forecast, score grid, evidence and what drove the forecast | 1.00 |
| `get_betting_picks` | `GET /x402/v1/bets/{fixtureId}` | Our picks for one match: market, selection, tier and our chance | 2.00 |
| `get_top_five` | `GET /x402/v1/top-five` | This week's Top 5: weekend set released Thursday 23:00 UK, midweek set Monday 23:00 UK | 10.00 |
| `get_settled_record` | `GET /x402/v1/record?page=N` | Settled picks with results, 20 per page | 1.00 per page |

**What you won't get:** bookmaker prices. Everything we sell is tactica.'s own output.

**When it isn't ready:** if a match has no published forecast or pick yet, the call answers "not available" and **nothing is charged**. The Top 5 can't be bought before its release (Thursday 23:00 UK for the weekend set, Monday 23:00 UK for the midweek set).

## QUICK START: MCP

Add the server to any MCP client. The free tools work straight away. The paid tools answer with an x402 payment request, which an x402-capable client or agent wallet can pay.

**Claude Code**
```bash
claude mcp add --transport http tactica https://app.tacticafootball.co.uk/x402/mcp
```

**Claude Desktop, Cursor, VS Code and most other clients** (`mcpServers` JSON)
```json
{
  "mcpServers": {
    "tactica": { "type": "http", "url": "https://app.tacticafootball.co.uk/x402/mcp" }
  }
}
```

**Paying over MCP:** an unpaid call to a paid tool returns `isError: true` with the x402 `PaymentRequired` object in `structuredContent`. To pay, retry the same call with a signed payment in `params._meta["x402/payment"]`. The receipt comes back in `result._meta["x402/payment-response"]`. This follows the x402 v2 MCP transport.

## QUICK START: HTTP + x402

Any x402 v2 client works. These examples pay 0.25 USDC for one forecast:

- [`examples/typescript`](examples/typescript): uses the official `@x402/fetch` and `@x402/evm` packages.
- [`examples/python`](examples/python): no x402 library, just `eth-account`, so you can see every step.
- [`examples/prediction-market`](examples/prediction-market): compares our chances with a market price you supply, such as a Polymarket or exchange price, and shows the gap.

**Before you run them:** use a wallet that only holds what you're happy to spend. Each example refuses to pay more than a maximum you set.

## AGENT FRAMEWORKS

If your framework supports MCP (ElizaOS, Coinbase AgentKit, LangChain, the Vercel AI SDK, the OpenAI Agents SDK and others), point it at the MCP URL above.

If your agent already has a wallet on Base, it can pay the 402 itself. Otherwise, wrap your HTTP client with an x402 client, as the TypeScript example does.

## PAYMENT DETAILS

| | |
|---|---|
| Network | Base (`eip155:8453`) |
| Asset | USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) |
| Scheme | x402 v2 `exact` (EIP-3009) |
| Facilitator | PayAI |
| Gas | Paid by the facilitator. Your wallet needs USDC only |

## TERMS

- **18+ only.** tactica. forecasts and picks are information, not betting or financial advice, and past results don't guarantee future results.
- **Agent access terms:** section 10A of the [tactica. Terms](https://www.tacticafootball.co.uk/terms). In short:
  - use what you buy for yourself or the person your agent acts for;
  - you can show short parts of it, with credit to tactica.;
  - no reselling, bulk republishing or training other models on it.
- **Privacy:** see the [Privacy Policy](https://www.tacticafootball.co.uk/privacy). Paid calls record the paying wallet and transaction, which are public on-chain anyway.

## CONTACT

hello@tacticafootball.co.uk

The examples in this repo are MIT-licensed (see [LICENSE](LICENSE)). The tactica. name, logo and data are not.
