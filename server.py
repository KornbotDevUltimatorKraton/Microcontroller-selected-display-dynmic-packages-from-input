import uvicorn
import httpx
import base64
import json
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI(title="RoboReactor Dynamic Pinout Visualizer")

# Enable full CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_PAYLOAD = {
    "email": "kornbot380@hotmail.com",
    "project_name": "Hexbot_design",
    "mcus": "STM32F401RET6"
}
DEFAULT_B64 = base64.b64encode(json.dumps(DEFAULT_PAYLOAD).encode("utf-8")).decode("utf-8")

# ── TOGGLE CONFIGURATION ──────────────────────────────────────────────────────────
# Set to False (default) to run in PRODUCTION fetching live database from http://192.168.50.247:9058/get_component_gpios
# Set to True if you want to test all multi-protocol colors (SPI, CAN, PWM, UART, ADC, I2C) using mock data.
USE_MOCK_TEST_DATA = False

# Visual Verification Mock Data featuring SPI, CAN, PWM, UART, ADC, and I2C simultaneously
MOCK_ALL_PROTOCOLS_DATA = {
    "kornbot380@hotmail.com": {
        "Hexbot_design": {
            "STM32F401RET6": {
                "TCA9548A_I2C_Mux.glb": {
                    "I2C": {
                        "SCL": "PA8",
                        "SDA": "PC9"
                    }
                },
                "SPI_Flash_Memory.glb": {
                    "SPI": {
                        "SCK": "PA5",
                        "MISO": "PA6",
                        "MOSI": "PA7",
                        "CS": "PB6"
                    }
                },
                "CAN_Transceiver_SN65HVD230.glb": {
                    "CAN": {
                        "CAN_TX": "PB9",
                        "CAN_RX": "PB8"
                    }
                },
                "PCA9685_Servo_Driver.glb": {
                    "PWM": {
                        "PWM_CH1": "PA1",
                        "PWM_CH2": "PA2",
                        "PWM_CH3": "PB0"
                    }
                },
                "GPS_UART_Module.glb": {
                    "UART": {
                        "TX": "PA9",
                        "RX": "PA10"
                    }
                },
                "Analog_Radar_Sensor.glb": {
                    "ADC": {
                        "ANALOG_IN": "PA0"
                    }
                }
            }
        }
    }
}

@app.get("/")
async def read_root():
    # Redirect root to default interact_pins endpoint
    return RedirectResponse(url=f"/interact_pins/{DEFAULT_B64}")

@app.get("/interact_pins/{encoded_data}")
async def interact_pins(encoded_data: str):
    """
    Serve the interactive pinout page pre-loaded with config encoded as base64 JSON.
    URL format: /interact_pins/<base64(json.dumps({"email":...,"project_name":...,"mcus":...}))>
    """
    try:
        decoded_bytes = base64.b64decode(encoded_data + "==")
        config = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid base64 JSON payload: {e}"}
        )

    email = config.get("email", "")
    project_name = config.get("project_name", "")
    mcu_name = config.get("mcus") or config.get("mcu") or config.get("mcusdata", "")

    html_path = Path("templates/index.html")
    html = html_path.read_text(encoding="utf-8")

    # Inject values into hidden inputs
    html = html.replace('id="api-email" value=""', f'id="api-email" value="{email}"')
    html = html.replace('id="api-project" value=""', f'id="api-project" value="{project_name}"')
    html = html.replace('id="api-mcu" value=""', f'id="api-mcu" value="{mcu_name}"')

    inject = f"""
    <script id="preload-config" type="application/json">
    {json.dumps(config)}
    </script>"""
    html = html.replace("</head>", inject + "\n</head>", 1)

    return HTMLResponse(content=html)

# CORS Proxy for MCU Database Structure
@app.post("/api/mcus_dbpath")
async def proxy_mcus_dbpath(request: Request):
    payload = await request.json()
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post("http://192.168.50.247:5978/mcus_dbpath", json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)

# CORS Proxy for Live GPIO Polling (PRODUCTION ENDPOINT)
@app.post("/api/get_component_gpios")
async def proxy_get_component_gpios(request: Request):
    payload = await request.json()

    # ── MOCK TEST OVERRIDE (Set USE_MOCK_TEST_DATA = True to test multi-protocol colors) ──
    if USE_MOCK_TEST_DATA:
        return JSONResponse(content=MOCK_ALL_PROTOCOLS_DATA)

    # ── PRODUCTION BACKEND ENDPOINT ──
    # Forwards requests directly to the live RoboReactor database at 192.168.50.247:9058
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post("http://192.168.50.247:9058/get_component_gpios", json=payload)
        return JSONResponse(content=response.json(), status_code=response.status_code)

if __name__ == "__main__":
    print("Starting RoboReactor Pinout Visualizer server...")
    print(f"Access default interactive pinout at: http://127.0.0.1:8000/interact_pins/{DEFAULT_B64}")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
