#!/usr/bin/env python3
"""
Real-time market-data client for FYERS WebSocket v3
Works stand-alone inside the fyers-data-fetcher repo.
Brian Pinto – MIT licence
"""

import json, time, threading, signal, sys
import websocket          # pip install websocket-client

# ---------- config ----------------------------------------------------------
CRED_FILE        = "api_cred.json"          # same file used by historical fetcher
TOKEN_FILE       = "access_token.txt"       # created after 1st login
SUBSCRIPTIONS    = ["NSE:NIFTY50-INDEX", "NSE:BANKNIFTY-INDEX"]  # add your own
DATA_MODE        = "symbolUpdate"           # "symbolUpdate"=full OHLCV, "l2Update"=LTP only
# ---------------------------------------------------------------------------

def _load_creds():
    with open(CRED_FILE) as f:
        c = json.load(f)
    return c["ClientID"], c["SecretID"], c["RedirectURI"]

def _load_token():
    try:
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"[ERROR] {TOKEN_FILE} not found. Run historical fetcher once to generate it.")
        sys.exit(1)

def _on_open(ws):
    print("🟢 WebSocket connected – subscribing …")
    subscribe = {
        "T": "SUB_L2",
        "S": SUBSCRIPTIONS,
        "MK": DATA_MODE
    }
    ws.send(json.dumps(subscribe))

def _on_message(ws, msg):
    data = json.loads(msg)
    # FYERS sends one dict per tick; print something readable
    if "l" in data:          # full OHLCV
        print(f"{data['tk']}  "
              f"LTP {data['ltp']:>8.2f}  "
              f"O {data['o']:>8.2f}  "
              f"H {data['h']:>8.2f}  "
              f"L {data['l']:>8.2f}  "
              f"C {data['c']:>8.2f}  "
              f"Vol {data['v']:>10}")
    else:                    # LTP only
        print(f"{data['tk']}  LTP {data['ltp']:>8.2f}")

def _on_error(ws, err):
    print("🔴 WS error:", err)

def _on_close(ws, close_status_code, close_msg):
    print("🔌 WebSocket closed")

def _sigint(*_):
    print("\n🛑 Ctrl-C – closing …")
    ws.close()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, _sigint)

    client_id, _, _ = _load_creds()
    access_token    = _load_token()

    ws_url = ("wss://api.fyers.in/socket/v3/data?"
              f"access_token={client_id}:{access_token}")

    ws = websocket.WebSocketApp(ws_url,
                                on_open=_on_open,
                                on_message=_on_message,
                                on_error=_on_error,
                                on_close=_on_close)

    # run forever in a thread so we can catch Ctrl-C cleanly
    wst = threading.Thread(target=ws.run_forever, daemon=True)
    wst.start()

    while wst.is_alive():
        time.sleep(1)