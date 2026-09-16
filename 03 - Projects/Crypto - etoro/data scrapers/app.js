// ============================================================
// CryptoQuant API v1 — Multi-Asset On-Chain Scraper · PRO
// Personal Plan: 20 req/min → 3s delay between requests
// ALL coins supported via ASSETS × TEMPLATES → dynamic ENDPOINT_CONFIG
// ============================================================

// BASE_URL is read from UI input #baseUrl (default: local proxy on :8787)
function getBaseUrl() {
  const v = document.getElementById("baseUrl")?.value?.trim();
  return v || "http://localhost:8787/v1";
}
const DELAY_MS = 3100;
const SNAPSHOT_KEY = "cqs_snapshots_v3";
const MAX_SNAPSHOTS = 10;

// ============================================================
// SUPPORTED ASSETS — every coin CryptoQuant typically exposes
// ============================================================
const SUPPORTED_ASSETS = [
  // Layer 1
  { code: "btc",   name: "Bitcoin",         icon: "₿",  group: "L1",         hasPerp: true,  hasIndicators: true,  isPoW: true  },
  { code: "eth",   name: "Ethereum",        icon: "Ξ",  group: "L1",         hasPerp: true,  hasIndicators: true,  isPoW: false },
  { code: "xrp",   name: "XRP",             icon: "✕",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: false },
  { code: "sol",   name: "Solana",          icon: "◎",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: false },
  { code: "ada",   name: "Cardano",         icon: "₳",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: false },
  { code: "doge",  name: "Dogecoin",        icon: "Ð",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: true  },
  { code: "ltc",   name: "Litecoin",        icon: "Ł",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: true  },
  { code: "trx",   name: "TRON",            icon: "₸",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: false },
  { code: "bch",   name: "Bitcoin Cash",    icon: "Ƀ",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: true  },
  { code: "etc",   name: "Ethereum Classic",icon: "ξ",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: true  },
  { code: "avax",  name: "Avalanche",       icon: "▲",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: false },
  { code: "dot",   name: "Polkadot",        icon: "●",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: false },
  { code: "atom",  name: "Cosmos",          icon: "⚛",  group: "L1",         hasPerp: true,  hasIndicators: false, isPoW: false },

  // L2 / Smart contract platforms
  { code: "matic", name: "Polygon",         icon: "⬡",  group: "L2",         hasPerp: true,  hasIndicators: false, isPoW: false },

  // Exchange tokens
  { code: "bnb",   name: "BNB",             icon: "ᴮ",  group: "Exchange",   hasPerp: true,  hasIndicators: false, isPoW: false },

  // DeFi
  { code: "link",  name: "Chainlink",       icon: "⛓",  group: "DeFi",       hasPerp: true,  hasIndicators: false, isPoW: false },
  { code: "uni",   name: "Uniswap",         icon: "🦄", group: "DeFi",       hasPerp: true,  hasIndicators: false, isPoW: false },
  { code: "aave",  name: "Aave",            icon: "Ⱥ",  group: "DeFi",       hasPerp: true,  hasIndicators: false, isPoW: false },

  // Meme
  { code: "shib",  name: "Shiba Inu",       icon: "🐕", group: "Meme",       hasPerp: true,  hasIndicators: false, isPoW: false },

  // Stablecoins
  { code: "usdt",  name: "Tether",          icon: "₮",  group: "Stablecoin", hasPerp: false, hasIndicators: false, isPoW: false, isStable: true },
  { code: "usdc",  name: "USD Coin",        icon: "$",  group: "Stablecoin", hasPerp: false, hasIndicators: false, isPoW: false, isStable: true },
];

const STABLES = ["usdt","usdc"];
const PoW_COINS = ["btc","ltc","bch","doge","etc"];
const ALL_ASSETS = SUPPORTED_ASSETS.map(a => a.code);

// ============================================================
// EXCHANGES — for per-exchange variant expansion (Max Mode)
// ============================================================
const SUPPORTED_EXCHANGES = [
  "binance", "okx", "bybit", "coinbase_pro", "kraken",
  "bitfinex", "bitmex", "deribit", "huobi_global"
];
// Suffixes that benefit from per-exchange breakdown
const PER_EXCHANGE_SUFFIXES = new Set([
  "funding", "oi", "longshort", "taker", "liquidations",
  "inflow", "outflow", "reserve", "netflow", "whale_ratio", "exchange_supply_ratio"
]);

// ============================================================
// ENDPOINT TEMPLATES — define once, applied per asset
//   path: relative (will be prefixed by /{asset})
//   onlyFor:  array of asset codes (or null = all)
//   skipFor:  array of asset codes to skip
//   weight, direction, essential: scoring metadata
// ============================================================
const ENDPOINT_TEMPLATES = [
  // ── Market Data (price/cap) ──
  { suffix:"ohlcv", label:"OHLCV", category:"ohlcv",
    path:"/market-data/price-ohlcv?${q}",
    valueFields:["close_price","close","price_usd"],
    weight:0, direction:null, essential:true },
  { suffix:"capitalization", label:"Market Cap", category:"ohlcv",
    path:"/market-data/capitalization?${q}",
    valueFields:["market_cap","market_capitalization","value"],
    weight:0, direction:null, essential:false },

  // ── Exchange Flows ──
  { suffix:"inflow", label:"Exchange Inflow", category:"flow",
    path:"/exchange-flows/inflow?${qex}",
    valueFields:["inflow_total","inflow","value"],
    weight:1, direction:"low_bull", essential:true },
  { suffix:"outflow", label:"Exchange Outflow", category:"flow",
    path:"/exchange-flows/outflow?${qex}",
    valueFields:["outflow_total","outflow","value"],
    weight:1, direction:"high_bull", essential:false },
  { suffix:"reserve", label:"Exchange Reserve", category:"flow",
    path:"/exchange-flows/reserve?${qex}",
    valueFields:["reserve","value"],
    weight:2, direction:"change_low_bull", essential:true },
  { suffix:"netflow", label:"Exchange Netflow", category:"flow",
    path:"/exchange-flows/netflow?${qex}",
    valueFields:["netflow_total","netflow","value"],
    weight:2, direction:"low_bull", essential:false },
  { suffix:"exchange_tx", label:"Exchange Tx Count", category:"flow",
    path:"/exchange-flows/transactions-count?${qex}",
    valueFields:["transactions_count","value"],
    weight:0, direction:null, essential:false },
  { suffix:"in_house_flow", label:"In-House Flow", category:"flow",
    path:"/exchange-flows/in-house-flow?${qex}",
    valueFields:["flow_total","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc","eth"] },

  // Stablecoin reserve (inverted scoring)
  { suffix:"reserve_stable", label:"Stablecoin Exchange Reserve", category:"flow",
    path:"/exchange-flows/reserve?${qex}",
    valueFields:["reserve","value"],
    weight:2, direction:"change_high_bull", essential:true,
    onlyFor: STABLES, _isAlias: true },

  // ── Flow Indicators ──
  { suffix:"whale_ratio", label:"Exchange Whale Ratio", category:"flow",
    path:"/flow-indicator/exchange-whale-ratio?${qex}",
    valueFields:["exchange_whale_ratio","ratio","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"exchange_supply_ratio", label:"Exchange Supply Ratio", category:"flow",
    path:"/flow-indicator/exchange-supply-ratio?${qex}",
    valueFields:["exchange_supply_ratio","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"exchange_shutdown", label:"Exchange Shutdown Index", category:"flow",
    path:"/flow-indicator/exchange-shutdown-index?${qex}",
    valueFields:["shutdown_index","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc"] },

  // ── Market Indicators ──
  { suffix:"mvrv", label:"MVRV", category:"indicator",
    path:"/market-indicator/mvrv?${q}",
    valueFields:["mvrv","value"],
    weight:2, direction:"low_bull", essential:true,
    onlyFor:["btc","eth"] },
  { suffix:"mvrv_zscore", label:"MVRV Z-Score", category:"indicator",
    path:"/market-indicator/mvrv-zscore?${q}",
    valueFields:["mvrv_zscore","value"],
    weight:2, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"sopr", label:"SOPR", category:"indicator",
    path:"/market-indicator/sopr-ratio?${q}",
    valueFields:["sopr","value"],
    weight:2, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"asopr", label:"aSOPR", category:"indicator",
    path:"/market-indicator/sopr-ratio-adjusted?${q}",
    valueFields:["asopr","sopr_adjusted","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"puell", label:"Puell Multiple", category:"indicator",
    path:"/market-indicator/puell-multiple?${q}",
    valueFields:["puell_multiple","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc"] },
  { suffix:"ssr", label:"Stablecoin Supply Ratio", category:"indicator",
    path:"/market-indicator/stablecoin-supply-ratio?${q}",
    valueFields:["ssr","stablecoin_supply_ratio","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"nupl", label:"NUPL", category:"indicator",
    path:"/market-indicator/nupl?${q}",
    valueFields:["nupl","value"],
    weight:2, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"realized_cap", label:"Realized Cap", category:"indicator",
    path:"/market-indicator/realized-cap?${q}",
    valueFields:["realized_cap","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"thermo_cap", label:"Thermo Cap", category:"indicator",
    path:"/market-indicator/thermo-cap?${q}",
    valueFields:["thermo_cap","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc"] },
  { suffix:"stf", label:"Stock-to-Flow", category:"indicator",
    path:"/market-indicator/stock-to-flow?${q}",
    valueFields:["stock_to_flow","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc"] },

  // ── Network Indicators ──
  { suffix:"nvt", label:"NVT", category:"indicator",
    path:"/network-indicator/nvt?${q}",
    valueFields:["nvt","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth","ltc","bch"] },
  { suffix:"nvm", label:"NVM (Metcalfe)", category:"indicator",
    path:"/network-indicator/nvm?${q}",
    valueFields:["nvm","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"nvt_golden", label:"NVT Golden Cross", category:"indicator",
    path:"/network-indicator/nvt-golden-cross?${q}",
    valueFields:["nvt_golden_cross","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },

  // ── Miners (Flows & Inter-entity) — miner=all_miner param required ──
  { suffix:"mpi", label:"MPI", category:"miner",
    path:"/flow-indicator/mpi?${q}",
    valueFields:["mpi","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc"] },
  { suffix:"miner_in", label:"Miner Inflow", category:"miner",
    path:"/miner-flows/inflow?${q}&miner=all_miner",
    valueFields:["inflow_total","inflow","value"],
    weight:0, direction:null, essential:false,
    onlyFor: PoW_COINS },
  { suffix:"miner_out", label:"Miner Outflow", category:"miner",
    path:"/miner-flows/outflow?${q}&miner=all_miner",
    valueFields:["outflow_total","outflow","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor: PoW_COINS },
  { suffix:"miner_reserve", label:"Miner Reserve", category:"miner",
    path:"/miner-flows/reserve?${q}&miner=all_miner",
    valueFields:["reserve","value"],
    weight:1, direction:"change_high_bull", essential:false,
    onlyFor: PoW_COINS },
  { suffix:"miner_to_exchange", label:"Miner→Exchange Flow", category:"miner",
    path:"/inter-entity-flows/miner-to-exchange?${q}&from_miner=all_miner&to_exchange=all_exchange",
    valueFields:["flow_total","flow","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc"] },
  { suffix:"hash", label:"Hash Rate", category:"miner",
    path:"/network-data/hashrate?${q}",
    valueFields:["hashrate","value"],
    weight:1, direction:"high_bull", essential:false,
    onlyFor: PoW_COINS },
  { suffix:"difficulty", label:"Difficulty", category:"miner",
    path:"/network-data/difficulty?${q}",
    valueFields:["difficulty","value"],
    weight:0, direction:null, essential:false,
    onlyFor: PoW_COINS },
  { suffix:"block_reward", label:"Block Reward", category:"miner",
    path:"/network-data/block-reward?${q}",
    valueFields:["block_reward","value"],
    weight:0, direction:null, essential:false,
    onlyFor: PoW_COINS },

  // ── Network Data ──
  { suffix:"tx", label:"Tx Count", category:"network",
    path:"/network-data/transactions-count?${q}",
    valueFields:["transactions_count","value"],
    weight:0, direction:null, essential:false,
    skipFor: STABLES },
  { suffix:"active", label:"Active Addresses", category:"network",
    path:"/network-data/addresses-count?${q}",
    valueFields:["addresses_count","active_addresses","value"],
    weight:1, direction:"high_bull", essential:false,
    skipFor: STABLES },
  { suffix:"supply", label:"Total Supply", category:"network",
    path:"/network-data/supply-total?${q}",
    valueFields:["supply_total","supply","value"],
    weight:0, direction:null, essential:false },
  { suffix:"fees", label:"Total Fees", category:"network",
    path:"/network-data/fees?${q}",
    valueFields:["fees_total","fees","value"],
    weight:1, direction:"high_bull", essential:false,
    skipFor: STABLES },
  { suffix:"block_bytes", label:"Block Bytes", category:"network",
    path:"/network-data/block-bytes?${q}",
    valueFields:["block_bytes","value"],
    weight:0, direction:null, essential:false,
    onlyFor: PoW_COINS },
  { suffix:"utxo", label:"UTXO Count", category:"network",
    path:"/network-data/utxo-count?${q}",
    valueFields:["utxo_count","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc","ltc","bch","doge"] },

  // ── Derivatives ──
  { suffix:"oi", label:"Open Interest", category:"derivative",
    path:"/market-data/open-interest?${qex}",
    valueFields:["open_interest","value"],
    weight:0, direction:null, essential:false,
    requirePerp:true },
  { suffix:"funding", label:"Funding Rate", category:"derivative",
    path:"/market-data/funding-rates?${qex}",
    valueFields:["funding_rates","funding_rate","value"],
    weight:1, direction:"low_bull", essential:true,
    requirePerp:true },
  { suffix:"longshort", label:"Long/Short Ratio", category:"derivative",
    path:"/market-data/long-short-ratio?${qex}",
    valueFields:["long_short_ratio","ratio","value"],
    weight:1, direction:"low_bull", essential:false,
    requirePerp:true },
  { suffix:"taker", label:"Taker Buy/Sell", category:"derivative",
    path:"/market-data/taker-buy-sell-stats?${qex}",
    valueFields:["taker_buy_sell_ratio","ratio","value"],
    weight:1, direction:"high_bull", essential:false,
    requirePerp:true },
  { suffix:"liquidations", label:"Liquidations", category:"derivative",
    path:"/market-data/liquidations?${qex}",
    valueFields:["long_liquidations_usd","liquidations","value"],
    weight:0, direction:null, essential:false,
    requirePerp:true },
  { suffix:"elr", label:"Estimated Leverage Ratio", category:"derivative",
    path:"/market-data/estimated-leverage-ratio?${qex}",
    valueFields:["estimated_leverage_ratio","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"coinbase_premium", label:"Coinbase Premium", category:"derivative",
    path:"/market-data/coinbase-premium-index?${q}",
    valueFields:["coinbase_premium_gap","coinbase_premium","value"],
    weight:1, direction:"high_bull", essential:false,
    onlyFor:["btc","eth"] },

  // ── Bank Flows (Pro/Enterprise tier — added for completeness) ──
  { suffix:"bank_in", label:"Bank Inflow", category:"flow",
    path:"/bank-flows/inflow?${qex}",
    valueFields:["inflow_total","inflow","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"bank_out", label:"Bank Outflow", category:"flow",
    path:"/bank-flows/outflow?${qex}",
    valueFields:["outflow_total","outflow","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"bank_reserve", label:"Bank Reserve", category:"flow",
    path:"/bank-flows/reserve?${qex}",
    valueFields:["reserve","value"],
    weight:1, direction:"change_high_bull", essential:false,
    onlyFor:["btc","eth"] },

  // ── Fund Flows ──
  { suffix:"fund_in", label:"Fund Inflow", category:"flow",
    path:"/fund-flows/inflow?${qex}",
    valueFields:["inflow_total","inflow","value"],
    weight:1, direction:"high_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"fund_out", label:"Fund Outflow", category:"flow",
    path:"/fund-flows/outflow?${qex}",
    valueFields:["outflow_total","outflow","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"fund_reserve", label:"Fund Reserve", category:"flow",
    path:"/fund-flows/reserve?${qex}",
    valueFields:["reserve","value"],
    weight:1, direction:"change_high_bull", essential:false,
    onlyFor:["btc","eth"] },

  // ── Inter-entity Flows (need from_/to_ params) ──
  { suffix:"exch_to_exch", label:"Exchange→Exchange", category:"flow",
    path:"/inter-entity-flows/exchange-to-exchange?${q}&from_exchange=all_exchange&to_exchange=all_exchange",
    valueFields:["flow_total","flow","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"exch_to_miner", label:"Exchange→Miner", category:"flow",
    path:"/inter-entity-flows/exchange-to-miner?${q}&from_exchange=all_exchange&to_miner=all_miner",
    valueFields:["flow_total","flow","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc"] },
  { suffix:"exch_to_bank", label:"Exchange→Bank", category:"flow",
    path:"/inter-entity-flows/exchange-to-bank?${q}&from_exchange=all_exchange&to_bank=all_bank",
    valueFields:["flow_total","flow","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"bank_to_exch", label:"Bank→Exchange", category:"flow",
    path:"/inter-entity-flows/bank-to-exchange?${q}&from_bank=all_bank&to_exchange=all_exchange",
    valueFields:["flow_total","flow","value"],
    weight:1, direction:"high_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"miner_to_bank", label:"Miner→Bank", category:"flow",
    path:"/inter-entity-flows/miner-to-bank?${q}&from_miner=all_miner&to_bank=all_bank",
    valueFields:["flow_total","flow","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc"] },

  // ── ETF (BTC spot ETF data) ──
  { suffix:"etf_holdings", label:"ETF Holdings", category:"indicator",
    path:"/etf/us-spot-btc-holdings?${q}",
    valueFields:["holdings","value"],
    weight:1, direction:"high_bull", essential:false,
    onlyFor:["btc"] },
  { suffix:"etf_flow", label:"ETF Net Flow", category:"flow",
    path:"/etf/us-spot-btc-flow?${q}",
    valueFields:["netflow","flow","value"],
    weight:2, direction:"high_bull", essential:false,
    onlyFor:["btc"] },

  // ── Realized profit/loss & capitulation ──
  { suffix:"realized_pl", label:"Realized P/L", category:"indicator",
    path:"/network-data/realized-profit-loss?${q}",
    valueFields:["realized_profit_loss","value"],
    weight:1, direction:"high_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"net_realized_pl", label:"Net Realized P/L", category:"indicator",
    path:"/network-data/net-realized-profit-loss?${q}",
    valueFields:["net_realized_profit_loss","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },

  // ── Supply distribution / HODL ──
  { suffix:"supply_top10", label:"Supply Top10 Addresses", category:"network",
    path:"/network-data/supply-top10?${q}",
    valueFields:["supply_top10","value"],
    weight:0, direction:null, essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"lth_supply", label:"Long-Term Holder Supply", category:"indicator",
    path:"/network-data/long-term-holder-supply?${q}",
    valueFields:["lth_supply","value"],
    weight:1, direction:"high_bull", essential:false,
    onlyFor:["btc"] },
  { suffix:"sth_supply", label:"Short-Term Holder Supply", category:"indicator",
    path:"/network-data/short-term-holder-supply?${q}",
    valueFields:["sth_supply","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc"] },

  // ── Additional derivatives ──
  { suffix:"oi_perp", label:"OI Perpetual", category:"derivative",
    path:"/market-data/open-interest-perpetual?${qex}",
    valueFields:["open_interest","value"],
    weight:0, direction:null, essential:false,
    requirePerp:true },
  { suffix:"basis", label:"Futures Basis", category:"derivative",
    path:"/market-data/futures-basis?${qex}",
    valueFields:["basis","value"],
    weight:1, direction:"low_bull", essential:false,
    onlyFor:["btc","eth"] },
  { suffix:"perp_volume", label:"Perpetual Volume", category:"derivative",
    path:"/market-data/perpetual-volume?${qex}",
    valueFields:["volume","value"],
    weight:0, direction:null, essential:false,
    requirePerp:true },
];

// ============================================================
// State
// ============================================================
let selectedAssets = [...ALL_ASSETS]; // auto-mode: fetch everything
let allData = { meta: { fetchedAt: null, days: 0, totalRequests: 0, errors: [], unavailable: [], assets: [] } };
let totalRequests = 0;
let doneRequests = 0;
let abortFlag = false;
let countdownTimer = null;
const activeSubTab = {};
const chartInstances = {};
let currentChartAsset = null;

// ============================================================
// Build dynamic ENDPOINT_CONFIG for selected assets
// Options:
//   skipDead: true → skip endpoints known to be dead (from CapabilityManager)
//   maxMode: true  → expand per-exchange variants for derivative/flow endpoints
// ============================================================
function buildEndpointConfig(assets, opts = {}) {
  const { skipDead = false, maxMode = false } = opts;
  const list = [];

  for (const code of assets) {
    const asset = SUPPORTED_ASSETS.find(a => a.code === code);
    if (!asset) continue;

    for (const tpl of ENDPOINT_TEMPLATES) {
      if (tpl.onlyFor && !tpl.onlyFor.includes(code)) continue;
      if (tpl.skipFor && tpl.skipFor.includes(code)) continue;
      if (tpl.requirePerp && !asset.hasPerp) continue;

      const baseKey = `${code}_${tpl.suffix}`;

      // Always include the all_exchange (or no-exchange) base variant
      const baseEndpoint = {
        key: baseKey,
        label: `${asset.icon} ${code.toUpperCase()} · ${tpl.label}`,
        path: tpl.path,
        asset: code,
        category: tpl.category,
        valueFields: tpl.valueFields,
        weight: tpl.weight,
        direction: tpl.direction,
        essential: tpl.essential,
        suffix: tpl.suffix,
        exchange: null,
      };
      if (!skipDead || !CapabilityManager.isDead(baseKey)) {
        list.push(baseEndpoint);
      }

      // Expand per-exchange variants if MAX mode enabled and template supports it
      if (maxMode && PER_EXCHANGE_SUFFIXES.has(tpl.suffix) && tpl.path.includes("${qex}")) {
        for (const exch of SUPPORTED_EXCHANGES) {
          const variantKey = `${baseKey}__${exch}`;
          // Skip if known dead (each exchange tracked separately)
          if (skipDead && CapabilityManager.isDead(variantKey)) continue;
          // Skip if base is known dead (no point trying exchanges if base failed for plan reasons)
          if (skipDead && CapabilityManager.isDead(baseKey) && !CapabilityManager.isWorking(variantKey)) continue;
          list.push({
            ...baseEndpoint,
            key: variantKey,
            label: `${asset.icon} ${code.toUpperCase()} · ${tpl.label} [${exch}]`,
            // Replace exchange param: qex has &exchange=all_exchange — we'll override per variant
            path: tpl.path,
            exchange: exch,
            weight: 0,    // per-exchange variants don't contribute to scoring (use base for scoring)
            essential: false,
          });
        }
      }
    }
  }
  return list;
}

function getCurrentConfig() {
  const maxMode = document.getElementById("maxMode")?.checked || false;
  return buildEndpointConfig(allData.meta.assets || selectedAssets, { maxMode });
}

// ============================================================
// API — fetch with retry, 429 handling, per-session cache
// ============================================================
const API = (() => {
  const cache = new Map();
  function clearCache() { cache.clear(); }

  async function call(path) {
    if (cache.has(path)) return { rows: cache.get(path), cached: true };
    const token = document.getElementById("apiKey").value.trim();
    if (!token) throw new Error("Access Token وارد نشده!");
    if (abortFlag) throw new Error("ABORTED");

    const url = getBaseUrl() + path;
    for (let attempt = 1; attempt <= 3; attempt++) {
      if (abortFlag) throw new Error("ABORTED");
      try {
        const res = await fetch(url, {
          headers: { "Authorization": "Bearer " + token, "Accept": "application/json" }
        });

        if (res.status === 429) {
          const retryAfter = parseInt(res.headers.get("Retry-After") || "") || (15 * attempt);
          UI.setStatus(`⏳ Rate limit 429 — ${retryAfter}s صبر...`);
          await sleepCountdown(retryAfter);
          continue;
        }
        if (res.status === 401) { const err = new Error("Token نامعتبر است (401)"); err.code = 401; throw err; }
        if (res.status === 403) { const err = new Error("403 Forbidden — endpoint در پلن یا برای این کوین نیست"); err.code = 403; throw err; }
        if (res.status === 404) { const err = new Error("404 Not Found — endpoint وجود ندارد"); err.code = 404; throw err; }
        if (!res.ok) {
          const body = await res.text().catch(() => res.statusText);
          throw new Error(`HTTP ${res.status}: ${body.slice(0, 120)}`);
        }

        const json = await res.json();
        const code = json?.status?.code;
        if (code !== undefined && code !== 0 && code !== 200) {
          throw new Error(`API error ${code}: ${json?.status?.message || "unknown"}`);
        }

        const rows = json?.result?.data ?? [];
        const arr = Array.isArray(rows) ? rows : [];
        cache.set(path, arr);
        allData.meta.totalRequests++;
        doneRequests++;
        UI.setProgress(Math.min(Math.round((doneRequests / totalRequests) * 100), 100));
        return { rows: arr, cached: false };
      } catch (e) {
        if (e.message === "ABORTED" || e.code === 401 || e.code === 403 || e.code === 404) throw e;
        if (attempt === 3) throw e;
        await sleep(3000);
      }
    }
    return { rows: [], cached: false };
  }
  return { call, clearCache };
})();

// ============================================================
// CapabilityManager — track what works per endpoint key
// Persistent in localStorage to skip dead endpoints on subsequent fetches
// ============================================================
const CAPABILITIES_KEY = "cqs_capabilities_v1";
const CapabilityManager = {
  get() {
    try { return JSON.parse(localStorage.getItem(CAPABILITIES_KEY) || '{"working":{},"dead":{},"recordedAt":null}'); }
    catch { return { working: {}, dead: {}, recordedAt: null }; }
  },
  set(m) { localStorage.setItem(CAPABILITIES_KEY, JSON.stringify(m)); },
  reset() {
    localStorage.removeItem(CAPABILITIES_KEY);
    UI.log("Capability map پاک شد — fetch بعدی همه endpoint ها را امتحان می‌کند", "warn");
    renderTierDisplay();
  },

  // Record outcome of a fetch
  record(key, success) {
    const m = this.get();
    if (success) { m.working[key] = Date.now(); delete m.dead[key]; }
    else { m.dead[key] = Date.now(); delete m.working[key]; }
    m.recordedAt = new Date().toISOString();
    this.set(m);
  },

  isDead(key)    { return !!this.get().dead[key]; },
  isWorking(key) { return !!this.get().working[key]; },
  isKnown(key)   { const m = this.get(); return !!m.working[key] || !!m.dead[key]; },

  // Detect plan tier from what works
  detectTier() {
    const w = this.get().working;
    const workingCount = Object.keys(w).length;
    if (workingCount === 0) return { tier: "Unknown", color: "neutral", note: "هنوز fetch نشده" };

    const hasBank = Object.keys(w).some(k => k.includes("bank_"));
    const hasFund = Object.keys(w).some(k => k.includes("fund_"));
    const hasETF  = Object.keys(w).some(k => k.includes("etf_"));
    const hasETHMvrv = w.eth_mvrv;
    const hasBTCAdvanced = w.btc_nupl || w.btc_mvrv_zscore || w.btc_puell;
    const hasBTCMvrv = w.btc_mvrv;
    const hasBTCFlows = w.btc_inflow;

    if (hasBank && hasETF) return { tier: "Enterprise", color: "bull", note: "همه چیز در دسترس" };
    if (hasBank || hasFund) return { tier: "Premier", color: "bull", note: "Bank/Fund Flows فعال" };
    if (hasBTCAdvanced && hasETHMvrv) return { tier: "Professional", color: "cbull", note: "NUPL/MVRV-Z + ETH indicators" };
    if (hasETHMvrv) return { tier: "Advanced", color: "cbull", note: "ETH market indicators فعال" };
    if (hasBTCMvrv) return { tier: "Premium", color: "neutral", note: "BTC market indicators موجود، ETH محدود" };
    if (hasBTCFlows) return { tier: "Basic", color: "cbear", note: "فقط BTC flows" };
    return { tier: "Limited", color: "bear", note: "خیلی محدود" };
  },

  stats() {
    const m = this.get();
    return {
      working: Object.keys(m.working).length,
      dead: Object.keys(m.dead).length,
      recordedAt: m.recordedAt,
      tier: this.detectTier(),
    };
  },
};

// ============================================================
// StorageManager
// ============================================================
const StorageManager = {
  list() { try { return JSON.parse(localStorage.getItem(SNAPSHOT_KEY) || "[]"); } catch { return []; } },
  save(name) {
    const snaps = this.list();
    const completeness = computeCompleteness();
    const snap = {
      id: Date.now() + "_" + Math.random().toString(36).slice(2, 8),
      name: name || `Snap ${new Date().toLocaleString("en-GB")}`,
      savedAt: new Date().toISOString(),
      days: allData.meta.days,
      assets: allData.meta.assets,
      completeness,
      data: allData,
    };
    snaps.unshift(snap);
    while (snaps.length > MAX_SNAPSHOTS) snaps.pop();
    try {
      localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snaps));
      return snap;
    } catch (e) {
      alert("ذخیره ناموفق: " + e.message + "\n(localStorage پر است — یک Snapshot حذف کنید)");
      return null;
    }
  },
  delete(id) {
    const snaps = this.list().filter(s => s.id !== id);
    localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snaps));
  },
  load(id) {
    const snap = this.list().find(s => s.id === id);
    if (!snap) return null;
    allData = snap.data;
    selectedAssets = snap.assets || [];
    return snap;
  },
};

// ============================================================
// SignalEngine
// ============================================================
const SignalEngine = {
  extractSeries(arr, valueFields) {
    if (!Array.isArray(arr) || !arr.length) return [];
    return arr.map(r => {
      for (const f of valueFields) {
        if (r[f] !== undefined && r[f] !== null) {
          const n = safeFloat(r[f]);
          if (n !== null) return { date: r.date || r.time || "", value: n };
        }
      }
      return null;
    }).filter(Boolean);
  },

  percentile(value, series) {
    if (!series.length) return null;
    const sorted = [...series].sort((a, b) => a - b);
    let below = 0;
    for (const v of sorted) if (v < value) below++;
    return Math.round((below / sorted.length) * 100);
  },

  zscore(value, series) {
    if (!series.length) return null;
    const mean = series.reduce((s, v) => s + v, 0) / series.length;
    const variance = series.reduce((s, v) => s + (v - mean) ** 2, 0) / series.length;
    const std = Math.sqrt(variance);
    return std === 0 ? 0 : (value - mean) / std;
  },

  change7d(series) {
    if (series.length < 8) return null;
    const last = series[series.length - 1];
    const prev = series[series.length - 8];
    if (prev === 0 || prev == null) return null;
    return ((last - prev) / Math.abs(prev)) * 100;
  },

  scorePercentile(value, series, direction, weight) {
    const pct = this.percentile(value, series);
    if (pct === null) return { score: 0, label: "neutral", pct: null };
    let raw = 0;
    if (direction === "low_bull") {
      if (pct <= 10) raw = 2;
      else if (pct <= 25) raw = 1;
      else if (pct >= 90) raw = -2;
      else if (pct >= 75) raw = -1;
    } else if (direction === "high_bull") {
      if (pct >= 90) raw = 2;
      else if (pct >= 75) raw = 1;
      else if (pct <= 10) raw = -2;
      else if (pct <= 25) raw = -1;
    }
    const label = raw > 0 ? "bull" : raw < 0 ? "bear" : "neutral";
    return { score: raw * weight, label, pct };
  },

  scoreChange(series, direction, weight) {
    const chg = this.change7d(series);
    if (chg === null) return { score: 0, label: "neutral", chg: null };
    let raw = 0;
    if (direction === "change_low_bull") {
      if (chg <= -3) raw = 2;
      else if (chg <= -1) raw = 1;
      else if (chg >= 3) raw = -2;
      else if (chg >= 1) raw = -1;
    } else if (direction === "change_high_bull") {
      if (chg >= 3) raw = 2;
      else if (chg >= 1) raw = 1;
      else if (chg <= -3) raw = -2;
      else if (chg <= -1) raw = -1;
    }
    const label = raw > 0 ? "bull" : raw < 0 ? "bear" : "neutral";
    return { score: raw * weight, label, chg };
  },

  scoreThreshold(value, lowThresh, highThresh, direction, weight) {
    if (value === null) return { score: 0, label: "neutral" };
    let raw = 0;
    if (direction === "low_bull") {
      if (value < lowThresh) raw = 2;
      else if (value > highThresh) raw = -2;
    } else {
      if (value > highThresh) raw = 2;
      else if (value < lowThresh) raw = -2;
    }
    const label = raw > 0 ? "bull" : raw < 0 ? "bear" : "neutral";
    return { score: raw * weight, label };
  },

  // Analyze a single asset — produces report for one coin
  analyzeAsset(asset, mode = "percentile") {
    const config = getCurrentConfig().filter(c => c.asset === asset);
    const indicators = [];
    let totalScore = 0, maxPossible = 0;
    let availableEssential = 0, totalEssential = 0;

    for (const ep of config) {
      if (ep.essential) totalEssential++;
      const series = this.extractSeries(allData[ep.key], ep.valueFields);
      if (!series.length) continue;
      if (ep.essential) availableEssential++;
      if (ep.weight === 0 || !ep.direction) continue;

      const values = series.map(s => s.value);
      const lastVal = values[values.length - 1];

      let result;
      if (ep.direction === "change_low_bull" || ep.direction === "change_high_bull") {
        result = this.scoreChange(values, ep.direction, ep.weight);
      } else if (mode === "threshold" && (ep.suffix === "mvrv" || ep.suffix === "nvt")) {
        const mvrvBuy  = parseFloat(document.getElementById("mvrvBuy").value)  || 1;
        const mvrvSell = parseFloat(document.getElementById("mvrvSell").value) || 3.5;
        const nvtLow   = parseFloat(document.getElementById("nvtLow").value)   || 40;
        const nvtHigh  = parseFloat(document.getElementById("nvtHigh").value)  || 100;
        if (ep.suffix === "mvrv") result = this.scoreThreshold(lastVal, mvrvBuy, mvrvSell, "low_bull", ep.weight);
        else result = this.scoreThreshold(lastVal, nvtLow, nvtHigh, "low_bull", ep.weight);
        result.pct = this.percentile(lastVal, values);
      } else {
        result = this.scorePercentile(lastVal, values, ep.direction, ep.weight);
      }

      totalScore += result.score;
      maxPossible += 2 * ep.weight;
      indicators.push({
        ep, lastVal, chg7: this.change7d(values),
        score: result.score, label: result.label,
        pct: result.pct ?? null, chg: result.chg ?? null,
      });
    }

    const confidencePct = totalEssential ? Math.round((availableEssential / totalEssential) * 100) : 0;
    const confidence = confidencePct >= 75 ? "High" : confidencePct >= 50 ? "Medium" : "Low";
    const normalizedScore = maxPossible > 0 ? (totalScore / maxPossible) * 10 : 0;
    let verdict, verdictClass, verdictEmoji;
    if (normalizedScore >= 5)       { verdict = "STRONG BULLISH"; verdictClass = "verdict-bull"; verdictEmoji = "🚀"; }
    else if (normalizedScore >= 2)  { verdict = "BULLISH";        verdictClass = "verdict-cbull"; verdictEmoji = "📈"; }
    else if (normalizedScore <= -5) { verdict = "STRONG BEARISH"; verdictClass = "verdict-bear"; verdictEmoji = "🔻"; }
    else if (normalizedScore <= -2) { verdict = "BEARISH";        verdictClass = "verdict-cbear"; verdictEmoji = "📉"; }
    else                            { verdict = "NEUTRAL";        verdictClass = "verdict-neutral"; verdictEmoji = "⚖️"; }

    return {
      asset, indicators, totalScore, maxPossible,
      normalizedScore: Math.round(normalizedScore * 10) / 10,
      confidence, confidencePct, verdict, verdictClass, verdictEmoji, mode,
    };
  },

  // Aggregate analysis across all assets
  analyzeAll(mode = "percentile") {
    const assets = allData.meta.assets || [];
    const perAsset = assets.map(a => this.analyzeAsset(a, mode));

    // Aggregate: average normalized score weighted by confidence
    let weightedSum = 0, weightSum = 0;
    perAsset.forEach(r => {
      if (r.maxPossible === 0) return;
      const w = r.confidencePct / 100;
      weightedSum += r.normalizedScore * w;
      weightSum += w;
    });
    const aggScore = weightSum > 0 ? Math.round((weightedSum / weightSum) * 10) / 10 : 0;
    let aggVerdict, aggClass, aggEmoji;
    if (aggScore >= 5)       { aggVerdict = "MARKET STRONG BULLISH"; aggClass = "verdict-bull"; aggEmoji = "🚀"; }
    else if (aggScore >= 2)  { aggVerdict = "MARKET BULLISH";        aggClass = "verdict-cbull"; aggEmoji = "📈"; }
    else if (aggScore <= -5) { aggVerdict = "MARKET STRONG BEARISH"; aggClass = "verdict-bear"; aggEmoji = "🔻"; }
    else if (aggScore <= -2) { aggVerdict = "MARKET BEARISH";        aggClass = "verdict-cbear"; aggEmoji = "📉"; }
    else                     { aggVerdict = "MARKET NEUTRAL";        aggClass = "verdict-neutral"; aggEmoji = "⚖️"; }

    return { perAsset, aggregate: { score: aggScore, verdict: aggVerdict, verdictClass: aggClass, emoji: aggEmoji } };
  },
};

// ============================================================
// UI namespace
// ============================================================
const UI = {
  setStatus(msg) { document.getElementById("statusText").textContent = msg; },
  setProgress(pct) {
    document.getElementById("progressFill").style.width = pct + "%";
    document.getElementById("progressCount").textContent = `${doneRequests} / ${totalRequests} درخواست`;
  },
  log(msg, type = "info") {
    const box = document.getElementById("logBox");
    const ts = new Date().toLocaleTimeString("en", { hour12: false });
    const div = document.createElement("div");
    div.className = "log-" + type;
    div.textContent = `[${ts}] ${msg}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  },
  addErrorChip(label, msg, isUnavail = false) {
    const row = document.getElementById("errorChips");
    const wrap = document.createElement("div");
    wrap.className = "tooltip-wrap";
    const cls = isUnavail ? "chip chip-unavail" : "chip chip-err";
    const tag = isUnavail ? "⊘" : "✕";
    wrap.innerHTML = `<span class="${cls}">${esc(label)} ${tag}</span><span class="tip">${esc(msg)}</span>`;
    row.appendChild(wrap);
  },
  collapseSettings() {
    document.getElementById("settings-body").classList.add("collapsed");
    document.getElementById("toggleSettingsBtn").textContent = "▸";
  },
};

// ============================================================
// Auto-fetch info display (no asset selection — fetch everything)
// ============================================================
function renderFetchInfo() {
  const maxMode = document.getElementById("maxMode")?.checked || false;
  const skipDead = document.getElementById("skipDead")?.checked !== false;
  const config = buildEndpointConfig(selectedAssets, { maxMode, skipDead });
  const fullConfig = buildEndpointConfig(selectedAssets, { maxMode });
  const skippedCount = fullConfig.length - config.length;
  const n = config.length + 1; // +1 token test
  const seconds = n * 3;
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  const timeStr = min > 0 ? `${min}m ${sec}s` : `${sec}s`;

  const byAsset = {};
  config.forEach(c => { byAsset[c.asset] = (byAsset[c.asset] || 0) + 1; });

  const box = document.getElementById("autoFetchSummary");
  if (!box) return;
  box.innerHTML = `
    <div class="auto-summary-stats">
      <div class="auto-stat"><span class="auto-stat-num">${selectedAssets.length}</span><span class="auto-stat-label">کوین</span></div>
      <div class="auto-stat"><span class="auto-stat-num">${ENDPOINT_TEMPLATES.length}</span><span class="auto-stat-label">نوع endpoint</span></div>
      <div class="auto-stat"><span class="auto-stat-num">${n}</span><span class="auto-stat-label">کل درخواست</span></div>
      <div class="auto-stat"><span class="auto-stat-num">~${timeStr}</span><span class="auto-stat-label">زمان تخمینی</span></div>
    </div>
    ${skippedCount > 0 ? `<div class="skip-info">✓ ${skippedCount} endpoint مرده (از قبل تست شده) skip می‌شوند</div>` : ""}
    ${maxMode ? `<div class="max-info">⚡ Max Mode فعال — هر endpoint flow/derivative × ${SUPPORTED_EXCHANGES.length} صرافی</div>` : ""}
    <div class="auto-breakdown">
      ${SUPPORTED_ASSETS.map(a => `
        <span class="auto-asset-chip" title="${esc(a.name)}">
          ${a.icon} ${a.code.toUpperCase()} <small>(${byAsset[a.code] || 0})</small>
        </span>
      `).join("")}
    </div>
  `;
}

// ============================================================
// Plan tier display
// ============================================================
function renderTierDisplay() {
  const stats = CapabilityManager.stats();
  const tier = stats.tier;
  const box = document.getElementById("tierDisplay");
  if (!box) return;
  if (stats.working === 0 && stats.dead === 0) {
    box.innerHTML = `<div class="tier-empty">⓪ هنوز fetch نشده — پلن تشخیص داده نشده</div>`;
    return;
  }
  const ago = stats.recordedAt ? new Date(stats.recordedAt).toLocaleString("en-GB") : "—";
  box.innerHTML = `
    <div class="tier-row">
      <div class="tier-info">
        <div class="tier-label-mini">Plan Tier تشخیص داده شد</div>
        <div class="tier-badge-big tier-${tier.color}">${esc(tier.tier)}</div>
        <div class="tier-note">${esc(tier.note)}</div>
      </div>
      <div class="tier-stats">
        <div class="tier-stat"><span class="num">${stats.working}</span><span class="lbl">✓ working</span></div>
        <div class="tier-stat"><span class="num">${stats.dead}</span><span class="lbl">✗ dead</span></div>
        <div class="tier-stat-time">آخرین تست: ${ago}</div>
        <button class="btn-mini" onclick="CapabilityManager.reset(); renderFetchInfo();">↻ ریست</button>
      </div>
    </div>
  `;
}

// ============================================================
// Helpers
// ============================================================
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function sleepCountdown(secs) {
  clearInterval(countdownTimer);
  const el = document.getElementById("countdownText");
  let remaining = secs;
  el.textContent = `⏱ ${remaining}s`;
  return new Promise(resolve => {
    countdownTimer = setInterval(() => {
      remaining--;
      if (remaining <= 0) { clearInterval(countdownTimer); el.textContent = ""; resolve(); }
      else el.textContent = `⏱ ${remaining}s`;
    }, 1000);
  });
}

async function waitBetween() {
  await sleepCountdown(Math.ceil(DELAY_MS / 1000));
  await sleep(DELAY_MS % 1000);
}

function getFromDate(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10).replace(/-/g, "");
}

function buildPath(template, asset, q, qex) {
  return ("/" + asset + template).replace("${qex}", qex).replace("${q}", q);
}

function buildEndpoints(days, opts = {}) {
  const limit = days;
  const from = getFromDate(days);
  const q = `window=day&limit=${limit}&from=${from}`;
  const maxMode = document.getElementById("maxMode")?.checked || false;
  const skipDead = document.getElementById("skipDead")?.checked !== false; // default true
  const config = buildEndpointConfig(selectedAssets, { maxMode, skipDead });

  return config.map(ep => {
    // Use per-exchange override if variant
    const exchangeName = ep.exchange || "all_exchange";
    const qex = q + "&exchange=" + exchangeName;
    return { ...ep, fullPath: buildPath(ep.path, ep.asset, q, qex) };
  });
}

function computeCompleteness() {
  const config = getCurrentConfig();
  if (!config.length) return { ok: 0, total: 0, pct: 0 };
  const ok = config.filter(ep => (allData[ep.key] || []).length > 0).length;
  return { ok, total: config.length, pct: Math.round((ok / config.length) * 100) };
}

// ============================================================
// Token validation
// ============================================================
async function validateToken() {
  UI.setStatus("🔑 بررسی Token...");
  UI.log("تست سلامت token...", "info");
  try {
    await API.call("/btc/market-data/price-ohlcv?window=day&limit=1");
    UI.log("Token معتبر است ✓", "ok");
    return true;
  } catch (e) {
    if (e.code === 401 || e.message.includes("401") || e.message.includes("نامعتبر")) {
      UI.setStatus("❌ Token اشتباه است! لطفاً از cryptoquant.com/pro/settings/api کلید بگیرید.");
      UI.log("Token نامعتبر: " + e.message, "err");
      return false;
    }
    throw e;
  }
}

// ============================================================
// Main fetch flow
// ============================================================
async function startFetch() {
  const token = document.getElementById("apiKey").value.trim();
  if (!token) { alert("❌ لطفاً Access Token را وارد کنید!"); return; }
  // Always fetch all assets in auto-mode
  selectedAssets = [...ALL_ASSETS];

  abortFlag = false;
  doneRequests = 0;
  document.getElementById("errorChips").innerHTML = "";
  document.getElementById("logBox").innerHTML = "";

  const days = parseInt(document.getElementById("daysSelect").value);
  const endpoints = buildEndpoints(days);
  totalRequests = endpoints.length + 1;

  // Reset data
  allData = {
    meta: { fetchedAt: new Date().toISOString(), days, totalRequests: 0, errors: [], unavailable: [], assets: [...selectedAssets] }
  };
  endpoints.forEach(ep => { allData[ep.key] = []; });
  API.clearCache();

  document.getElementById("fetchBtn").disabled = true;
  document.getElementById("stopBtn").classList.remove("hidden");
  document.getElementById("statusBox").classList.remove("hidden");
  document.getElementById("resultsCard").classList.add("hidden");
  UI.setProgress(0);
  UI.setStatus(`🚀 شروع... (${endpoints.length} endpoint · ~${Math.ceil(endpoints.length * 3)}s)`);

  try {
    const valid = await validateToken();
    if (!valid || abortFlag) return;
    await waitBetween();

    for (let i = 0; i < endpoints.length; i++) {
      if (abortFlag) { UI.log("توقف توسط کاربر", "warn"); break; }
      const ep = endpoints[i];
      UI.setStatus(`⟳ ${ep.label} (${i + 1}/${endpoints.length})`);
      UI.log(`Fetching: ${ep.label}`, "info");
      try {
        const { rows } = await API.call(ep.fullPath);
        allData[ep.key] = rows;
        CapabilityManager.record(ep.key, rows.length > 0);
        UI.log(`${ep.label} → ${rows.length} ردیف ✓`, "ok");
      } catch (e) {
        if (e.message === "ABORTED") break;
        if (e.code === 403 || e.code === 404 || e.message.includes("HTTP 400")) {
          UI.log(`${ep.label}: ${e.message.slice(0, 80)} (skip)`, "warn");
          allData.meta.unavailable.push({ endpoint: ep.label, msg: e.message });
          UI.addErrorChip(ep.label, e.message, true);
          CapabilityManager.record(ep.key, false);
        } else {
          UI.log(`خطا در ${ep.label}: ${e.message}`, "err");
          allData.meta.errors.push({ endpoint: ep.label, msg: e.message });
          UI.addErrorChip(ep.label, e.message, false);
          // Don't record network errors as dead — endpoint might be fine, network just failed
        }
        allData[ep.key] = [];
      }
      if (i < endpoints.length - 1 && !abortFlag) await waitBetween();
    }

    if (!abortFlag) {
      const errCount = allData.meta.errors.length;
      const unavCount = allData.meta.unavailable.length;
      const tier = CapabilityManager.detectTier();
      UI.setStatus(errCount || unavCount
        ? `✅ تمام شد — Plan: ${tier.tier} · ${errCount} خطا · ${unavCount} غیر در دسترس`
        : `✅ همه داده‌ها دریافت شدند! Plan: ${tier.tier}`);
      UI.setProgress(100);
      document.getElementById("countdownText").textContent = "";
      renderResults();
      renderTierDisplay();
      renderFetchInfo();
      UI.collapseSettings();
      document.getElementById("refreshBtn").classList.remove("hidden");
    } else {
      UI.setStatus("⛔ توسط کاربر متوقف شد.");
      renderTierDisplay();
    }
  } catch (e) {
    if (e.message !== "ABORTED") UI.setStatus("❌ خطا: " + e.message);
    else UI.setStatus("⛔ توسط کاربر متوقف شد.");
  } finally {
    document.getElementById("fetchBtn").disabled = false;
    document.getElementById("stopBtn").classList.add("hidden");
    clearInterval(countdownTimer);
  }
}

function stopFetch() {
  abortFlag = true;
  clearInterval(countdownTimer);
  UI.setStatus("⛔ در حال توقف...");
}

// ============================================================
// Refresh Latest — fetch last 7 days, merge
// ============================================================
async function refreshLatest() {
  const token = document.getElementById("apiKey").value.trim();
  if (!token) { alert("❌ لطفاً Access Token را وارد کنید!"); return; }
  if (!allData.meta.fetchedAt) { alert("ابتدا یک Fetch کامل انجام دهید."); return; }

  abortFlag = false;
  doneRequests = 0;
  const limit = 7;
  const from = getFromDate(7);
  const q = `window=day&limit=${limit}&from=${from}`;
  const qex = q + "&exchange=all_exchange";
  const config = getCurrentConfig().filter(ep => (allData[ep.key] || []).length > 0);
  const endpoints = config.map(ep => ({ ...ep, fullPath: buildPath(ep.path, ep.asset, q, qex) }));
  totalRequests = endpoints.length;
  API.clearCache();

  document.getElementById("statusBox").classList.remove("hidden");
  document.getElementById("logBox").innerHTML = "";
  document.getElementById("errorChips").innerHTML = "";
  UI.setProgress(0);
  UI.setStatus(`🔄 Refresh Latest — ${endpoints.length} endpoint × 7d`);
  document.getElementById("refreshBtn").disabled = true;

  try {
    for (let i = 0; i < endpoints.length; i++) {
      if (abortFlag) break;
      const ep = endpoints[i];
      UI.setStatus(`⟳ ${ep.label} (${i + 1}/${endpoints.length})`);
      try {
        const { rows } = await API.call(ep.fullPath);
        const existing = allData[ep.key] || [];
        const newDates = new Set(rows.map(r => r.date || r.time));
        const filtered = existing.filter(r => !newDates.has(r.date || r.time));
        allData[ep.key] = [...filtered, ...rows];
        UI.log(`${ep.label} → +${rows.length} ردیف merged ✓`, "ok");
      } catch (e) {
        if (e.message === "ABORTED") break;
        UI.log(`refresh ${ep.label}: ${e.message}`, "warn");
      }
      if (i < endpoints.length - 1 && !abortFlag) await waitBetween();
    }
    UI.setStatus("✅ Refresh کامل شد.");
    UI.setProgress(100);
    renderResults();
  } finally {
    document.getElementById("refreshBtn").disabled = false;
  }
}

// ============================================================
// Render results — dynamic tabs per asset + Signal + Charts
// ============================================================
function renderResults() {
  document.getElementById("resultsCard").classList.remove("hidden");
  const assets = allData.meta.assets || [];

  // Stats
  const errHtml = allData.meta.errors.length
    ? `<div class="stat-chip error-chip" title="${allData.meta.errors.map(e=>e.endpoint+': '+e.msg).join('\n')}">⚠️ خطا: <span>${allData.meta.errors.length}</span></div>` : "";
  const unavHtml = allData.meta.unavailable.length
    ? `<div class="stat-chip unavail-chip" title="${allData.meta.unavailable.map(e=>e.endpoint).join('\n')}">⊘ غیر در دسترس: <span>${allData.meta.unavailable.length}</span></div>` : "";
  document.getElementById("resultStats").innerHTML = `
    <div class="stat-chip">کوین‌ها: <span>${assets.length}</span></div>
    <div class="stat-chip">Requests: <span>${allData.meta.totalRequests}</span></div>
    <div class="stat-chip">بازه: <span>${allData.meta.days} روز</span></div>
    <div class="stat-chip">زمان: <span>${new Date(allData.meta.fetchedAt).toLocaleString("en-GB")}</span></div>
    ${errHtml}${unavHtml}
  `;

  // Completeness
  const comp = computeCompleteness();
  document.getElementById("completenessText").textContent = `${comp.ok} / ${comp.total} (${comp.pct}%)`;
  const fill = document.getElementById("completenessFill");
  fill.style.width = comp.pct + "%";
  fill.className = comp.pct >= 75 ? "fill-good" : comp.pct >= 50 ? "fill-med" : "fill-bad";

  // Build tabs
  const tabBar = document.getElementById("resultTabs");
  const tabsContent = document.getElementById("tabsContent");

  const tabNames = [...assets, "signal", "charts"];
  tabBar.innerHTML = tabNames.map((t, i) => {
    if (t === "signal") return `<button class="tab" onclick="showResultTab('signal')">⚡ Signal</button>`;
    if (t === "charts") return `<button class="tab" onclick="showResultTab('charts')">📈 Charts</button>`;
    const asset = SUPPORTED_ASSETS.find(a => a.code === t);
    return `<button class="tab ${i === 0 ? "active" : ""}" onclick="showResultTab('${t}')">${asset?.icon || ""} ${t.toUpperCase()}</button>`;
  }).join("");

  tabsContent.innerHTML = `
    ${assets.map((a, i) => `<div id="tab-${a}" class="tab-content ${i === 0 ? "" : "hidden"}">${renderAssetTabHTML(a)}</div>`).join("")}
    <div id="tab-signal" class="tab-content hidden"></div>
    <div id="tab-charts" class="tab-content hidden">${renderChartsTabHTML(assets)}</div>
  `;

  // Render contents
  assets.forEach(a => renderAssetTab(a));
  renderSignalTab();

  renderSnapshots();
}

function showResultTab(name) {
  const assets = allData.meta.assets || [];
  const allTabs = [...assets, "signal", "charts"];
  allTabs.forEach(t => {
    const el = document.getElementById("tab-" + t);
    if (el) el.classList.toggle("hidden", t !== name);
  });
  document.querySelectorAll("#resultTabs .tab").forEach((b, i) => {
    b.classList.toggle("active", allTabs[i] === name);
  });
  if (name === "charts") setTimeout(() => renderAssetCharts(currentChartAsset || assets[0]), 50);
}

// ============================================================
// Per-asset tab — dynamic based on which endpoints have data
// ============================================================
function renderAssetTabHTML(asset) {
  const config = getCurrentConfig().filter(c => c.asset === asset);
  const categories = ["ohlcv", "flow", "indicator", "miner", "network", "derivative"];
  const present = categories.filter(cat =>
    config.some(c => c.category === cat && (allData[c.key] || []).length > 0)
  );
  if (!present.length) return `<div class="empty-tab">داده‌ای برای ${asset.toUpperCase()} موجود نیست.</div>`;
  activeSubTab[asset] = activeSubTab[asset] || present[0];
  return `
    <div class="sub-tabs">
      ${present.map(cat => `
        <button class="sub-tab ${activeSubTab[asset] === cat ? "active" : ""}" onclick="showSubTab('${asset}','${cat}',this)">
          ${categoryLabel(cat)}
        </button>
      `).join("")}
    </div>
    ${present.map(cat => `<div id="${asset}-sub-${cat}" class="${activeSubTab[asset] === cat ? "" : "hidden"}"></div>`).join("")}
  `;
}

function categoryLabel(cat) {
  return { ohlcv: "OHLCV", flow: "Exchange Flow", indicator: "Indicators",
           miner: "Miners", network: "Network", derivative: "Derivatives" }[cat] || cat;
}

function renderAssetTab(asset) {
  const config = getCurrentConfig().filter(c => c.asset === asset);
  const cats = ["ohlcv","flow","indicator","miner","network","derivative"];
  cats.forEach(cat => {
    const box = document.getElementById(`${asset}-sub-${cat}`);
    if (!box) return;
    const eps = config.filter(c => c.category === cat);
    if (cat === "ohlcv") box.innerHTML = renderOHLCV(asset, eps);
    else if (cat === "flow") box.innerHTML = renderFlow(asset, eps);
    else box.innerHTML = renderGeneric(asset, eps, cat);
  });
}

function renderOHLCV(asset, eps) {
  const ep = eps[0];
  if (!ep) return "";
  const arr = [...(allData[ep.key] || [])].reverse();
  if (!arr.length) return `<div class="empty-tab">داده OHLCV موجود نیست.</div>`;
  return `
    <table>
      <thead><tr><th>تاریخ</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead>
      <tbody>${arr.map(r => {
        const o = safeFloat(r.open_price ?? r.open);
        const c = safeFloat(r.close_price ?? r.close);
        const up = c !== null && o !== null && c >= o;
        return `<tr>
          <td>${esc(r.date ?? r.time ?? "—")}</td>
          <td>${fmtPrice(r.open_price ?? r.open)}</td>
          <td class="change-up">${fmtPrice(r.high_price ?? r.high)}</td>
          <td class="change-down">${fmtPrice(r.low_price ?? r.low)}</td>
          <td class="${up ? "change-up" : "change-down"}">${fmtPrice(r.close_price ?? r.close)}</td>
          <td>${fmtBig(r.volume)}</td>
        </tr>`;
      }).join("")}</tbody>
    </table>
  `;
}

function renderFlow(asset, eps) {
  // Build merged table date → { in, out, res, whale }
  const inflow  = eps.find(e => e.suffix === "inflow");
  const outflow = eps.find(e => e.suffix === "outflow");
  const reserve = eps.find(e => e.suffix === "reserve" || e.suffix === "reserve_stable");
  const whale   = eps.find(e => e.suffix === "whale_ratio");

  const map = {};
  const fill = (ep, key) => {
    if (!ep) return;
    (allData[ep.key] || []).forEach(r => {
      const d = r.date ?? r.time;
      if (!map[d]) map[d] = {};
      for (const f of ep.valueFields) if (r[f] !== undefined) { map[d][key] = safeFloat(r[f]); return; }
    });
  };
  fill(inflow, "in"); fill(outflow, "out"); fill(reserve, "res"); fill(whale, "wr");

  const dates = Object.keys(map).sort().reverse();
  if (!dates.length) return `<div class="empty-tab">داده Exchange Flow موجود نیست.</div>`;

  const showWhale = !!whale;
  return `
    <table>
      <thead><tr>
        <th>تاریخ</th><th>Inflow</th><th>Outflow</th><th>Reserve</th><th>Net Flow</th>
        ${showWhale ? "<th>Whale Ratio</th>" : ""}
      </tr></thead>
      <tbody>${dates.map(d => {
        const r = map[d];
        const net = (r.out != null && r.in != null) ? r.out - r.in : null;
        return `<tr>
          <td>${esc(d)}</td>
          <td class="change-down">${fmtBig(r.in)}</td>
          <td class="change-up">${fmtBig(r.out)}</td>
          <td>${fmtBig(r.res)}</td>
          <td class="${net == null ? "" : net >= 0 ? "change-up" : "change-down"}">${net != null ? (net >= 0 ? "+" : "") + fmtBig(net) : "—"}</td>
          ${showWhale ? `<td>${r.wr != null ? r.wr.toFixed(4) : "—"}</td>` : ""}
        </tr>`;
      }).join("")}</tbody>
    </table>
  `;
}

function renderGeneric(asset, eps, cat) {
  const available = eps.filter(ep => (allData[ep.key] || []).length > 0);
  if (!available.length) return `<div class="empty-tab">داده‌ای در دسته ${categoryLabel(cat)} موجود نیست.</div>`;

  // Merge by date
  const map = {};
  available.forEach(ep => {
    (allData[ep.key] || []).forEach(r => {
      const d = r.date ?? r.time;
      if (!map[d]) map[d] = {};
      for (const f of ep.valueFields) if (r[f] !== undefined) {
        map[d][ep.suffix] = safeFloat(r[f]);
        return;
      }
    });
  });

  const dates = Object.keys(map).sort().reverse();
  return `
    <table>
      <thead><tr>
        <th>تاریخ</th>
        ${available.map(ep => `<th title="${esc(ep.label)}">${esc(shortLabel(ep))}</th>`).join("")}
      </tr></thead>
      <tbody>${dates.map(d => {
        const r = map[d];
        return `<tr>
          <td>${esc(d)}</td>
          ${available.map(ep => `<td>${formatCell(r[ep.suffix], ep)}</td>`).join("")}
        </tr>`;
      }).join("")}</tbody>
    </table>
  `;
}

function shortLabel(ep) {
  const map = { mvrv:"MVRV", sopr:"SOPR", asopr:"aSOPR", puell:"Puell", ssr:"SSR", nvt:"NVT",
    mpi:"MPI", miner_out:"Miner Out", hash:"Hash Rate", difficulty:"Difficulty",
    tx:"TX Count", active:"Active Addr",
    oi:"OI", funding:"Funding", longshort:"L/S", taker:"Taker B/S" };
  return map[ep.suffix] || ep.suffix;
}

function formatCell(v, ep) {
  if (v == null) return "—";
  if (ep.suffix === "funding") return (v * 100).toFixed(4) + "%";
  if (Math.abs(v) >= 1e6) return fmtBig(v);
  if (Math.abs(v) < 1) return v.toFixed(4);
  return v.toFixed(3);
}

function showSubTab(asset, cat, btn) {
  const cats = ["ohlcv","flow","indicator","miner","network","derivative"];
  cats.forEach(c => {
    const el = document.getElementById(`${asset}-sub-${c}`);
    if (el) el.classList.toggle("hidden", c !== cat);
  });
  btn.closest(".sub-tabs").querySelectorAll(".sub-tab").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  activeSubTab[asset] = cat;
}

// ============================================================
// Signal tab — per-asset + aggregate
// ============================================================
function renderSignalTab() {
  const mode = document.getElementById("scoringMode").value;
  const { perAsset, aggregate } = SignalEngine.analyzeAll(mode);
  const box = document.getElementById("tab-signal");
  if (!box) return;

  const aggHTML = `
    <div class="verdict-card ${aggregate.verdictClass}" style="margin-bottom:20px">
      <div class="verdict-emoji">${aggregate.emoji}</div>
      <div style="flex:1">
        <div class="verdict-title">🌐 ${esc(aggregate.verdict)}</div>
        <div class="verdict-score">Aggregate Score: ${aggregate.score > 0 ? "+" : ""}${aggregate.score} / 10 · ${perAsset.length} coins · Mode: ${mode}</div>
      </div>
    </div>
  `;

  const cardsHTML = perAsset.map(r => {
    const a = SUPPORTED_ASSETS.find(x => x.code === r.asset);
    const confBadge = `<span class="confidence-badge conf-${r.confidence.toLowerCase()}" title="${r.confidencePct}%">${r.confidence}</span>`;
    const reasons = r.indicators
      .filter(i => i.label !== "neutral")
      .slice(0, 5)
      .map(i => {
        const arrow = i.label === "bull" ? "↑" : "↓";
        const detail = i.chg != null ? `Δ7d ${i.chg.toFixed(1)}%` : i.pct != null ? `p${i.pct}` : "";
        return `<span class="chip chip-${i.label}">${esc(shortLabel(i.ep))} ${arrow} ${detail}</span>`;
      }).join("");

    return `
      <div class="asset-signal-card ${r.verdictClass}">
        <div class="asset-signal-header">
          <span class="asset-signal-icon">${a?.icon || ""}</span>
          <span class="asset-signal-name">${a?.name || r.asset.toUpperCase()}</span>
          <span class="asset-signal-code">${r.asset.toUpperCase()}</span>
          ${confBadge}
        </div>
        <div class="asset-signal-verdict">${r.verdictEmoji} ${esc(r.verdict)}</div>
        <div class="asset-signal-score">${r.normalizedScore > 0 ? "+" : ""}${r.normalizedScore} / 10 · raw ${r.totalScore}/${r.maxPossible}</div>
        <div class="chip-row">${reasons || '<span class="chip chip-neutral">no strong signal</span>'}</div>
        <details class="signal-details">
          <summary>جزئیات (${r.indicators.length} indicator)</summary>
          <table class="mini-table">
            <thead><tr><th>Indicator</th><th>Value</th><th>Δ7d</th><th>Pct</th><th>Score</th></tr></thead>
            <tbody>${r.indicators.map(i => `
              <tr>
                <td>${esc(shortLabel(i.ep))}</td>
                <td>${formatVal(i.lastVal, i.ep)}</td>
                <td class="${i.chg != null && i.chg >= 0 ? "change-up" : i.chg != null ? "change-down" : ""}">${i.chg != null ? (i.chg >= 0 ? "+" : "") + i.chg.toFixed(2) + "%" : "—"}</td>
                <td>${i.pct != null ? i.pct + "%" : "—"}</td>
                <td>${i.score >= 0 ? "+" : ""}${i.score}</td>
              </tr>`).join("")}</tbody>
          </table>
        </details>
      </div>
    `;
  }).join("");

  // Ranking table — sort by score
  const ranked = [...perAsset].sort((a, b) => b.normalizedScore - a.normalizedScore);
  const rankHTML = `
    <h3 class="section-title">🏆 رتبه‌بندی کوین‌ها</h3>
    <table class="ranking-table">
      <thead><tr><th>#</th><th>کوین</th><th>Verdict</th><th>Score</th><th>Confidence</th></tr></thead>
      <tbody>${ranked.map((r, i) => {
        const a = SUPPORTED_ASSETS.find(x => x.code === r.asset);
        return `<tr>
          <td>${i + 1}</td>
          <td>${a?.icon || ""} ${a?.name || r.asset.toUpperCase()}</td>
          <td><span class="chip chip-${r.normalizedScore >= 2 ? "bull" : r.normalizedScore <= -2 ? "bear" : "neutral"}">${esc(r.verdict)}</span></td>
          <td><strong>${r.normalizedScore > 0 ? "+" : ""}${r.normalizedScore}</strong></td>
          <td><span class="confidence-badge conf-${r.confidence.toLowerCase()}">${r.confidence} (${r.confidencePct}%)</span></td>
        </tr>`;
      }).join("")}</tbody>
    </table>
  `;

  box.innerHTML = aggHTML + rankHTML + `<h3 class="section-title">📋 جزئیات هر کوین</h3><div class="asset-signal-grid">${cardsHTML}</div>`;
}

function formatVal(v, ep) {
  if (v === null || v === undefined) return "N/A";
  if (ep.suffix === "funding") return (v * 100).toFixed(4) + "%";
  if (ep.category === "ohlcv") return "$" + v.toLocaleString();
  if (Math.abs(v) >= 1e6) return fmtBig(v);
  if (Math.abs(v) < 1) return v.toFixed(4);
  return v.toFixed(3);
}

// ============================================================
// Charts tab — asset selector + 3 charts per asset
// ============================================================
function renderChartsTabHTML(assets) {
  return `
    <div class="charts-header">
      <label>کوین: </label>
      <select id="chartAssetSelect" onchange="renderAssetCharts(this.value)">
        ${assets.map(a => {
          const ai = SUPPORTED_ASSETS.find(x => x.code === a);
          return `<option value="${a}">${ai?.icon || ""} ${ai?.name || a.toUpperCase()}</option>`;
        }).join("")}
      </select>
    </div>
    <div class="chart-grid">
      <div class="chart-box"><h3 id="chart-title-1">Price vs MVRV</h3><canvas id="chart-mvrv"></canvas></div>
      <div class="chart-box"><h3 id="chart-title-2">Price vs Reserve</h3><canvas id="chart-reserve"></canvas></div>
      <div class="chart-box"><h3 id="chart-title-3">Funding Rate</h3><canvas id="chart-funding"></canvas></div>
      <div class="chart-box"><h3 id="chart-title-4">Net Flow (Outflow - Inflow)</h3><canvas id="chart-netflow"></canvas></div>
    </div>
  `;
}

function renderAssetCharts(asset) {
  currentChartAsset = asset;
  const a = SUPPORTED_ASSETS.find(x => x.code === asset);
  if (!a) return;
  const sel = document.getElementById("chartAssetSelect");
  if (sel) sel.value = asset;

  Object.values(chartInstances).forEach(c => c?.destroy?.());

  const ohlcv  = allData[`${asset}_ohlcv`];
  const mvrv   = allData[`${asset}_mvrv`];
  const res    = allData[`${asset}_reserve`] || allData[`${asset}_reserve_stable`];
  const fund   = allData[`${asset}_funding`];
  const inflow = allData[`${asset}_inflow`];
  const outflow = allData[`${asset}_outflow`];

  document.getElementById("chart-title-1").textContent = `${a.icon} ${asset.toUpperCase()} — Price vs MVRV`;
  document.getElementById("chart-title-2").textContent = `${a.icon} ${asset.toUpperCase()} — Price vs Reserve`;
  document.getElementById("chart-title-3").textContent = `${a.icon} ${asset.toUpperCase()} — Funding Rate`;
  document.getElementById("chart-title-4").textContent = `${a.icon} ${asset.toUpperCase()} — Net Flow`;

  buildDualAxisChart("chart-mvrv", ohlcv, mvrv,
    "Price", "MVRV", ["close_price","close"], ["mvrv","value"], "#0ea5e9", "#f59e0b");
  buildDualAxisChart("chart-reserve", ohlcv, res,
    "Price", "Reserve", ["close_price","close"], ["reserve","value"], "#0ea5e9", "#22c55e");
  buildBarChart("chart-funding", fund, ["funding_rates","funding_rate","value"], "Funding %");
  buildNetFlowChart("chart-netflow", inflow, outflow);
}

function extractDateValue(arr, fields) {
  return (arr || []).map(r => {
    const d = r.date || r.time;
    for (const f of fields) if (r[f] !== undefined && r[f] !== null) {
      const n = safeFloat(r[f]);
      if (n !== null) return { x: d, y: n };
    }
    return null;
  }).filter(Boolean);
}

function buildDualAxisChart(canvasId, arrA, arrB, labelA, labelB, fieldsA, fieldsB, colorA, colorB) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const parent = ctx.parentElement;
  parent.querySelectorAll(".chart-empty").forEach(e => e.remove());
  ctx.style.display = "";
  const dataA = extractDateValue(arrA, fieldsA);
  const dataB = extractDateValue(arrB, fieldsB);
  if (!dataA.length && !dataB.length) return showEmptyChart(ctx, parent);
  chartInstances[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [
        { label: labelA, data: dataA, borderColor: colorA, backgroundColor: colorA + "20", yAxisID: "y", borderWidth: 1.6, pointRadius: 0, tension: 0.2 },
        { label: labelB, data: dataB, borderColor: colorB, backgroundColor: colorB + "20", yAxisID: "y1", borderWidth: 1.6, pointRadius: 0, tension: 0.2 },
      ]
    },
    options: chartOpts(true)
  });
}

function buildBarChart(canvasId, arr, fields, label) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const parent = ctx.parentElement;
  parent.querySelectorAll(".chart-empty").forEach(e => e.remove());
  ctx.style.display = "";
  const data = extractDateValue(arr, fields);
  if (!data.length) return showEmptyChart(ctx, parent);
  chartInstances[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      datasets: [{
        label, data: data.map(d => ({ x: d.x, y: d.y * 100 })),
        backgroundColor: data.map(d => d.y >= 0 ? "#22c55e80" : "#ef444480"),
        borderColor: data.map(d => d.y >= 0 ? "#22c55e" : "#ef4444"),
        borderWidth: 1,
      }]
    },
    options: chartOpts(false)
  });
}

function buildNetFlowChart(canvasId, inflowArr, outflowArr) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const parent = ctx.parentElement;
  parent.querySelectorAll(".chart-empty").forEach(e => e.remove());
  ctx.style.display = "";
  const inMap = {}, outMap = {};
  (inflowArr || []).forEach(r => { inMap[r.date || r.time] = safeFloat(r.inflow_total ?? r.inflow ?? r.value); });
  (outflowArr || []).forEach(r => { outMap[r.date || r.time] = safeFloat(r.outflow_total ?? r.outflow ?? r.value); });
  const dates = Array.from(new Set([...Object.keys(inMap), ...Object.keys(outMap)])).sort();
  const data = dates.map(d => {
    const i = inMap[d], o = outMap[d];
    if (i == null || o == null) return null;
    return { x: d, y: o - i };
  }).filter(Boolean);
  if (!data.length) return showEmptyChart(ctx, parent);
  chartInstances[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      datasets: [{
        label: "Net Flow (Out - In)", data,
        backgroundColor: data.map(d => d.y >= 0 ? "#22c55e80" : "#ef444480"),
        borderColor: data.map(d => d.y >= 0 ? "#22c55e" : "#ef4444"),
        borderWidth: 1,
      }]
    },
    options: chartOpts(false)
  });
}

function showEmptyChart(ctx, parent) {
  ctx.style.display = "none";
  const empty = document.createElement("div");
  empty.className = "chart-empty";
  empty.textContent = "داده موجود نیست";
  parent.appendChild(empty);
}

function chartOpts(dual) {
  const base = {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { labels: { color: "#94a3b8", font: { size: 11 } } },
      tooltip: { backgroundColor: "#0f172a", titleColor: "#e2e8f0", bodyColor: "#94a3b8", borderColor: "#334155", borderWidth: 1 },
    },
    scales: {
      x: { type: "category", ticks: { color: "#64748b", maxRotation: 0, autoSkip: true, maxTicksLimit: 8 }, grid: { color: "#1e293b" } },
      y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
    }
  };
  if (dual) base.scales.y1 = { position: "right", ticks: { color: "#94a3b8" }, grid: { drawOnChartArea: false } };
  return base;
}

// ============================================================
// Snapshots UI
// ============================================================
function saveSnapshot() {
  const name = prompt("نام Snapshot:", `Snap ${new Date().toLocaleString("en-GB")}`);
  if (name === null) return;
  const snap = StorageManager.save(name);
  if (snap) { UI.log(`Snapshot ذخیره شد: ${snap.name}`, "ok"); renderSnapshots(); }
}

function renderSnapshots() {
  const snaps = StorageManager.list();
  const box = document.getElementById("snapshotsList");
  if (!snaps.length) { box.innerHTML = `<em class="muted">هنوز Snapshot ذخیره نشده است.</em>`; return; }
  box.innerHTML = snaps.map(s => `
    <div class="snapshot-item">
      <div class="snap-meta">
        <strong>${esc(s.name)}</strong>
        <span class="muted"> · ${new Date(s.savedAt).toLocaleString("en-GB")} · ${s.days}d · ${(s.assets||[]).length} coins · ${s.completeness?.pct ?? "?"}%</span>
      </div>
      <div class="snap-actions">
        <button class="btn-mini" onclick="loadSnapshot('${s.id}')">↺ Load</button>
        <button class="btn-mini btn-danger" onclick="deleteSnapshot('${s.id}')">حذف</button>
      </div>
    </div>
  `).join("");
}

function loadSnapshot(id) {
  const snap = StorageManager.load(id);
  if (!snap) return alert("Snapshot یافت نشد.");
  UI.log(`Snapshot بارگذاری شد: ${snap.name}`, "ok");
  renderFetchInfo();
  renderResults();
}

function deleteSnapshot(id) { if (!confirm("حذف شود؟")) return; StorageManager.delete(id); renderSnapshots(); }

function toggleSnapshots() { document.getElementById("snapshotsBody").classList.toggle("collapsed"); }

function toggleSettings() {
  const body = document.getElementById("settings-body");
  body.classList.toggle("collapsed");
  document.getElementById("toggleSettingsBtn").textContent = body.classList.contains("collapsed") ? "▸" : "▾";
}

// ============================================================
// Exports
// ============================================================
function exportJSON() {
  downloadFile(JSON.stringify(allData, null, 2), "application/json", `cryptoquant_${dateStr()}.json`);
}

function exportAllCSVs() {
  // Export one combined multi-asset CSV with sections
  let out = `# CryptoQuant Multi-Asset Export\n# Generated: ${new Date().toISOString()}\n# Days: ${allData.meta.days}\n# Assets: ${(allData.meta.assets||[]).join(",")}\n\n`;
  (allData.meta.assets || []).forEach(asset => {
    const config = getCurrentConfig().filter(c => c.asset === asset);
    config.forEach(ep => {
      const arr = allData[ep.key] || [];
      if (!arr.length) return;
      out += `\n# ${ep.label}\n`;
      out += `date,value\n`;
      arr.forEach(r => {
        let v = "";
        for (const f of ep.valueFields) if (r[f] !== undefined) { v = safeFloat(r[f]) ?? ""; break; }
        out += `"${r.date ?? r.time ?? ""}","${v}"\n`;
      });
    });
  });
  downloadFile(out, "text/csv;charset=utf-8;", `cryptoquant_multi_${dateStr()}.csv`);
}

function exportAnalysis() {
  const mode = document.getElementById("scoringMode").value;
  const { perAsset, aggregate } = SignalEngine.analyzeAll(mode);
  const out = {
    generated_at: new Date().toISOString(),
    api: "CryptoQuant v1",
    days: allData.meta.days,
    assets: allData.meta.assets,
    completeness: computeCompleteness(),
    aggregate,
    per_asset: perAsset.map(r => ({
      asset: r.asset, verdict: r.verdict, normalized_score: r.normalizedScore,
      raw_score: r.totalScore, max_possible: r.maxPossible,
      confidence: r.confidence, confidence_pct: r.confidencePct,
      indicators: r.indicators.map(i => ({
        label: i.ep.label, key: i.ep.key, weight: i.ep.weight, direction: i.ep.direction,
        last_value: i.lastVal, change_7d_pct: i.chg, percentile: i.pct,
        score: i.score, status: i.label,
      })),
    })),
    errors: allData.meta.errors,
    unavailable: allData.meta.unavailable,
  };
  downloadFile(JSON.stringify(out, null, 2), "application/json", `cryptoquant_analysis_${dateStr()}.json`);
}

function exportAIPrompt() {
  const mode = document.getElementById("scoringMode").value;
  const { perAsset, aggregate } = SignalEngine.analyzeAll(mode);
  const comp = computeCompleteness();
  const dateNow = new Date().toISOString().slice(0, 10);

  let md = `# Multi-Asset On-Chain Signal Analysis Request

## Role
You are a senior on-chain crypto analyst with 10+ years of experience analyzing crypto market structure across Bitcoin, Ethereum, and altcoins. Your task is to interpret the data below and provide an actionable read on positioning, risk, and likely 1–4 week market direction across the entire portfolio. Be specific. Cite the indicators and coins that drove your conclusion.

## Data Snapshot
- **Generated:** ${dateNow}
- **Window:** ${allData.meta.days} days
- **Source:** CryptoQuant v1 API
- **Assets Analyzed:** ${(allData.meta.assets || []).map(a => a.toUpperCase()).join(", ")}
- **Completeness:** ${comp.ok}/${comp.total} endpoints (${comp.pct}%)

## Aggregate Market Verdict
**${aggregate.verdict}** ${aggregate.emoji}
Score: ${aggregate.score > 0 ? "+" : ""}${aggregate.score} / 10
Mode: ${mode}

## Per-Asset Rankings

| # | Asset | Verdict | Score | Confidence |
|---|---|---|---|---|
`;
  const ranked = [...perAsset].sort((a, b) => b.normalizedScore - a.normalizedScore);
  ranked.forEach((r, i) => {
    md += `| ${i + 1} | ${r.asset.toUpperCase()} | ${r.verdict} | ${r.normalizedScore > 0 ? "+" : ""}${r.normalizedScore} | ${r.confidence} (${r.confidencePct}%) |\n`;
  });

  md += `\n## Indicator Details per Asset\n`;
  perAsset.forEach(r => {
    if (!r.indicators.length) return;
    md += `\n### ${r.asset.toUpperCase()} — ${r.verdict}\n\n`;
    md += `| Indicator | Last Value | Δ7d | Pct | Weight | Status | Score |\n|---|---|---|---|---|---|---|\n`;
    r.indicators.forEach(i => {
      const chg = i.chg !== null ? (i.chg >= 0 ? "+" : "") + i.chg.toFixed(2) + "%" : "—";
      const pct = i.pct !== null ? i.pct + "%" : "—";
      const status = i.label === "bull" ? "🟢" : i.label === "bear" ? "🔴" : "⚪";
      md += `| ${shortLabel(i.ep)} | ${formatVal(i.lastVal, i.ep)} | ${chg} | ${pct} | ${i.ep.weight} | ${status} | ${i.score >= 0 ? "+" : ""}${i.score} |\n`;
    });
  });

  if (allData.meta.unavailable.length) {
    md += `\n## Unavailable Endpoints (not in plan or not supported for asset)\n`;
    md += allData.meta.unavailable.slice(0, 30).map(u => `- ${u.endpoint}`).join("\n");
    if (allData.meta.unavailable.length > 30) md += `\n_(+${allData.meta.unavailable.length - 30} more)_`;
  }

  md += `\n\n## What I want from you

1. **Aggregate read**: Do you agree with the computed market verdict? Justify in 2–3 sentences.
2. **Strongest setup**: Which coin has the best risk/reward right now and why? Cite specific indicators.
3. **Worst setup**: Which coin is most at risk? What would invalidate?
4. **Rotation thesis**: Are flows suggesting capital rotation between BTC, ETH, altcoins, or stablecoins?
5. **Watch list for next refresh (7d)**: Top 3 indicators to monitor.
6. **Trade plan**: For a swing trader with 2–4 week horizon, what's the highest-conviction trade given this data?

Respond in concise prose with bolded key takeaways. No fluff.
`;

  downloadFile(md, "text/markdown;charset=utf-8;", `cryptoquant_ai_prompt_${dateStr()}.md`);
}

// ============================================================
// Utility
// ============================================================
function safeFloat(v, fallback = null) {
  if (v === null || v === undefined || v === "") return fallback;
  const n = parseFloat(String(v).replace(/,/g, ""));
  return isNaN(n) ? fallback : n;
}

function esc(s) {
  if (s == null) return "—";
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function fmtPrice(n) {
  const v = safeFloat(n);
  if (v === null) return "—";
  if (Math.abs(v) >= 1) return "$" + v.toLocaleString("en", { maximumFractionDigits: 2 });
  return "$" + v.toFixed(6);
}

function fmtBig(n) {
  const v = safeFloat(n);
  if (v === null) return "—";
  if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(2) + "B";
  if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(2) + "M";
  if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(1) + "K";
  return v.toFixed(2);
}

function downloadFile(content, type, filename) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([content], { type }));
  a.download = filename;
  a.click();
}

function dateStr() { return new Date().toISOString().slice(0, 19).replace(/[T:]/g, "-"); }

// ============================================================
// Boot
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  renderFetchInfo();
  renderSnapshots();
  renderTierDisplay();
});
