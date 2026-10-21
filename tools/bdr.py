"""Tiny client for the Dice Rush Extended test harness (127.0.0.1:47811).
usage:
  python bdr.py ping
  python bdr.py eval "m().money"
  python bdr.py raw '{"cmd":"screenshot","path":"C:/temp/shot.png"}'
"""
import json, socket, sys

def request(payload, port=47811, timeout=120):
    s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
    data = b""
    while not data.endswith(b"\n"):
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
    s.close()
    return json.loads(data.decode("utf-8"))

if __name__ == "__main__":
    port = 47811
    args = sys.argv[1:]
    if args and args[0].startswith("--port="):
        port = int(args[0][7:]); args = args[1:]
    cmd = args[0]
    if cmd == "raw":
        payload = json.loads(args[1])
    elif cmd == "eval":
        payload = {"cmd": "eval", "expr": args[1]}
    else:
        payload = {"cmd": cmd}
        for extra in args[1:]:
            k, v = extra.split("=", 1)
            try:
                v = json.loads(v)
            except Exception:
                pass
            payload[k] = v
    out = request(payload, port)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
