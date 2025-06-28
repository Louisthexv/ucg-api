from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import urllib3
import os

urllib3.disable_warnings()

app = FastAPI()

# Get env variables for URL and API KEY
UGW_API_URL = os.getenv("UGW_API_URL")
API_KEY = os.getenv("API_KEY")

if not UGW_API_URL or not API_KEY:
    raise RuntimeError("Missing required environment variables: UGW_API_URL and/or API_KEY")

@app.get("/api/ugw-health")
def get_router_health():
    headers = {
        "X-API-KEY": API_KEY,
        "Accept": "application/json"
    }

    try:
        response = requests.get(UGW_API_URL, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()

        health_data = data.get("data", [{}])

        # Find WAN, LAN, VPN subsystems for stats
        wan = next((s for s in health_data if s.get("subsystem") == "wan"), {})
        lan = next((s for s in health_data if s.get("subsystem") == "lan"), {})
        vpn = next((s for s in health_data if s.get("subsystem") == "vpn"), {})
        www = next((s for s in health_data if s.get("subsystem") == "www"), {})

        latency = www.get("latency", None)

        result = {
            "wan_ip": wan.get("wan_ip", "-"),
            "latency": latency if latency is not None else "-",
            "speed_down": www.get("xput_down", "-"),
            "speed_up": www.get("xput_up", "-"),
            "uptime": wan.get("gw_system-stats", {}).get("uptime", "-"),
            "clients_connected": lan.get("num_user", "-"),
            "clients_disconnected": lan.get("num_disconnected", "-"),
            "vpn_clients_connected": vpn.get("remote_user_num_active", "-"),
        }

        return JSONResponse(content={"data": [result]})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
