#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse, datetime

MCP_URL  = "https://tvremix.xyz/api/mcp/v1"
API_KEY  = os.environ["TVREMIX_API_KEY"]
BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
CHAT_ID   = os.environ["TG_CHAT_ID"]

TOP10 = ["NASDAQ:AAPL","NASDAQ:MSFT","NASDAQ:NVDA","NASDAQ:AMZN",
         "NASDAQ:GOOGL","NASDAQ:META","NASDAQ:TSLA","NASDAQ:AVGO",
         "NASDAQ:NFLX","NASDAQ:COST"]
MNQ = "CME_MINI:MNQ1!"

_sess = {"id": None}
def rpc(method, params=None):
    body = {"jsonrpc":"2.0","id":1,"method":method}
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(
        MCP_URL, data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def call_tool(name, args):
    res = rpc("tools/call", {"name": name, "arguments": args})
    # MCP returns {content:[{type:"text",text:"<json>"}]}
    for c in res.get("content", []):
        if c.get("type") == "text":
            try: return json.loads(c["text"])
            except Exception: return c["text"]
    return res

def main():
    # 1. NEW NEWS / NO NEWS across top-10 NDX in last 15 min
    fresh = False
    for sym in TOP10:
        try:
            for h in call_tool("get_news", {"symbol": sym, "limit": 3})[:3]:
                ts = h.get("time", 0)
                if ts and (datetime.datetime.utcnow().timestamp() - ts) < 900:
                    fresh = True
        except Exception:
            pass
    head = "NEW NEWS" if fresh else "NO NEWS"

    # 2. MNQ daily bias + intraday call
    try:
        q = call_tool("get_quote", {"symbol": MNQ})
        price = q.get("price", 0)
        chg   = q.get("change_pct", q.get("change", 0))
    except Exception:
        price, chg = 0, 0

    try:
        t = call_tool("get_technicals", {"symbol": MNQ, "timeframes": ["1D","60"]})
        daily = str(t.get("1D", {}).get("recommendation", "Neutral"))
    except Exception:
        daily = "Neutral"

    bias = "BULLISH" if "Buy" in daily else ("BEARISH" if "Sell" in daily else "NEUTRAL")

    # 3. Message
    msg = f"{head} — last 15 min\n"
    msg += f"**MNQ1! call:** {bias} bias"
    if price: msg += f" — futures {price} ({chg:+.2f}%)"
    msg += "\nIntraday: slow long"  # refine per your rules

    # 4. Send
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg,
                                   "parse_mode": "Markdown"}).encode()
    urllib.request.urlopen(urllib.request.Request(url, data=data))

if __name__ == "__main__":
    main()
