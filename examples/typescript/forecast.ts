// Buy one tactica. forecast (0.25 USDC on Base) with the official x402 v2 client.
//
//   npm install
//   TACTICA_FIXTURE_ID=<fixtureId> WALLET_KEY_FILE=~/.config/my-agent-wallet.hex MAX_USDC=0.25 npx tsx forecast.ts
//
// Fixture ids come from the free MCP tool list_fixtures (see ../python: `python tactica_x402.py fixtures`).
// Use a wallet that holds only what you are happy to spend. Gas is paid by the facilitator.
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { wrapFetchWithPaymentFromConfig, decodePaymentResponseHeader } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm";
import { privateKeyToAccount } from "viem/accounts";

const fixtureId = process.env.TACTICA_FIXTURE_ID;
const keyFile = (process.env.WALLET_KEY_FILE ?? "").replace(/^~/, homedir());
const maxUsdc = Number(process.env.MAX_USDC ?? "0");
if (!fixtureId || !keyFile || !(maxUsdc > 0)) {
  throw new Error("Set TACTICA_FIXTURE_ID, WALLET_KEY_FILE and MAX_USDC");
}
const url = `https://app.tacticafootball.co.uk/x402/v1/forecast/${fixtureId}`;

// 1. Check the price before signing anything.
const offer = await fetch(url);
if (offer.status !== 402) throw new Error(`expected a payment request, got HTTP ${offer.status}: ${await offer.text()}`);
const required = JSON.parse(Buffer.from(offer.headers.get("PAYMENT-REQUIRED") ?? "", "base64").toString());
const price = Number(required.accepts[0].amount) / 1_000_000;
if (price > maxUsdc) throw new Error(`price ${price} USDC is above MAX_USDC ${maxUsdc}`);

// 2. Pay and fetch in one call.
const key = readFileSync(keyFile, "utf8").trim();
const account = privateKeyToAccount((key.startsWith("0x") ? key : `0x${key}`) as `0x${string}`);
const fetchWithPayment = wrapFetchWithPaymentFromConfig(fetch, {
  schemes: [{ network: "eip155:8453", client: new ExactEvmScheme(account) }],
});
const response = await fetchWithPayment(url, { method: "GET" });
if (!response.ok) throw new Error(`HTTP ${response.status}: ${await response.text()}`);

const forecast = await response.json();
const receipt = response.headers.get("PAYMENT-RESPONSE");
console.log(JSON.stringify(forecast, null, 2));
if (receipt) console.log("transaction:", decodePaymentResponseHeader(receipt).transaction);
