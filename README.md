# PolyGraphe

Engineering physics project: an oximeter (heart rate, SpO₂) extended with breathing, sweat and
GSR sensors, used as an experimental "lie detector".

| Part | |
| --- | --- |
| `firmware/` (to come) | The device. Streams measurements over WiFi to the backend. |
| [`backend/`](backend) | FastAPI processing server: ingestion, storage (InfluxDB + SQLite), processing, trials. |
| [`frontend/`](frontend) | Next.js interface: trials, real-time charts, lookup. |

## Quick start

```bash
# Terminal 1: processing server, with a simulated device and no database needed
cd backend && POLYGRAPHE_STORAGE_BACKEND=memory uv run uvicorn app.main:app

# Terminal 2: interface
cd frontend && pnpm install && pnpm dev
```

Then open http://localhost:3000. To keep data between restarts, run InfluxDB with
`docker compose up -d` in `backend/` and drop the `POLYGRAPHE_STORAGE_BACKEND=memory`.

## Deployment

See [DEPLOY.md](DEPLOY.md): Docker Compose behind a Cloudflare Tunnel, on a single server.
