#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse, datetime

# ---- Config (set via repo secrets, see step 3) ----
BOT_TOKEN  = os.environ["TG_BOT_TOKEN"]
CHAT_ID    = os.environ["TG_CHAT_ID"]
MCP_URL    = "https://tvremix.xyz/mcp"   # MCP endpoint

TOP10 = ["NASDAQ:AAPL","NASDAQ:MSFT","NASDAQ:NVDA","NASDAQ:AMZN",
         "NASDAQ:GOOGL","NASDAQ:META","NASDAQ:TSLA","NASDAQ:AVGO",
         "NASDAQ:NFLX","NASDAQ:COST"]

def mcp_call(method, params):
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps({"method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def main():
    # 1. Pull top-10 NDX news to decide NEW NEWS / NO NEWS
    news_lines = []
    for sym in TOP10:
        try:
            for h in mcp_call("get_news", {"symbol": sym, "limit": 3})[:3]:
                ts = h.get("time", 0)
                if ts and (datetime.datetime.utcnow().timestamp() - ts) < 900:
                    news_lines.append(h.get("headline",""))
        except Exception:
            pass

    head = "NEW NEWS" if news_lines else "NO NEWS"

    # 2. MNQ bias + intraday call
    q = mcp_call("get_quote", {"symbol": "CME_MINI:MNQ1!"})
    t = mcp_call("get_technicals", {"symbol": "CME_MINI:MNQ1!",
                                    "timeframes": ["1D","60"]})
    price = q.get("price", 0)
    daily = t.get("1D", {}).get("recommendation", "Neutral")
    bias = "BULLISH" if "Buy" in str(daily) else ("BEARISH" if "Sell" in str(daily) else "NEUTRAL")

    # 3. Build message
    msg = f"{head} — last 15 min\n"
    msg += f"MNQ1! call: {bias} bias, slow long"  # refine intraday per your rules
    msg += f" — futures {price}"

    # 4. Send to Telegram
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg}).encode()
    urllib.request.urlopen(urllib.request.Request(url, data=data))

if __name__ == "__main__":
    main()
