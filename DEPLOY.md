# Deploying PolyGraphe

Everything runs on one server with Docker Compose: InfluxDB, the processing server, the
interface, a small NGINX router and a Cloudflare Tunnel connector. No port is opened to the
internet: `cloudflared` dials out to Cloudflare, which serves `polygraphe.samy.dev` over HTTPS.

```
Cloudflare → cloudflared → proxy (nginx:80) ─ /       → frontend :3000
                                            └ /api/…  → backend  :8000   (REST + websockets)
```

## Prerequisites

- Docker with the Compose plugin (`docker compose version`).
- A Cloudflare account with the `samy.dev` zone.

## 1. Create the tunnel (Cloudflare dashboard)

1. Zero Trust → Networks → Tunnels → **Create a tunnel** → Cloudflared. Name it `polygraphe`.
2. Copy the token from the install command (the long string after `--token`).
3. Under **Public hostname**, add: subdomain `polygraphe`, domain `samy.dev`, service type
   `HTTP`, URL `proxy:80`. Cloudflare creates the DNS record itself.

## 1. Get the code and configure

```bash
git clone <repository-url> polygraphe && cd polygraphe
cp .env.example .env
```

Fill in `.env`. Every empty value is required, and `docker compose` refuses to start without
it. For secrets:

```bash
openssl rand -hex 32   # SECRET_KEY, DEVICE_TOKEN, INFLUX_TOKEN, INFLUX_ADMIN_PASSWORD
```

Paste the token into `TUNNEL_TOKEN`. Also change `OPERATOR_PASSWORD`: it is the only thing standing between watchers and the controls.

> `INFLUX_TOKEN` and `INFLUX_ADMIN_PASSWORD` are only read when InfluxDB starts for the first
> time. Changing them afterwards requires deleting the `influxdb-data` volume (and its data).

## 2. Start the stack

```bash
docker compose up -d --build
docker compose ps                        # all services should become "healthy"
curl http://127.0.0.1:8000/health        # {"status":"ok",...}
```

## 3. Check

```bash
docker compose logs cloudflared | tail   # "Registered tunnel connection" (x4)
```

Then open https://polygraphe.samy.dev (interface) and https://polygraphe.samy.dev/api/docs (API).

## 4. Connect the device

The firmware opens a websocket to

```
wss://polygraphe.samy.dev/api/ws/devices/<device-id>?token=<DEVICE_TOKEN>
```

and sends measurements as described in [backend/README.md](backend/README.md#device-protocol).
Once the real device works, set `DUMMY_ENABLED=false` and run `docker compose up -d`.

## Operating

| Task | Command |
| --- | --- |
| Update to the latest code | `git pull && docker compose up -d --build` |
| Logs | `docker compose logs -f backend` (or `frontend`, `influxdb`) |
| Restart | `docker compose restart` |
| Stop | `docker compose down` (data is kept in volumes) |

**Backups.** All the data lives in two volumes: `polygraphe_backend-data` (trials, SQLite) and
`polygraphe_influxdb-data` (measurements). For example:

```bash
docker compose stop backend influxdb
for v in backend-data influxdb-data; do
  docker run --rm -v polygraphe_$v:/data -v "$PWD":/backup alpine \
    tar czf /backup/$v-$(date +%F).tar.gz -C /data .
done
docker compose start influxdb backend
```

**Things not to change:**
- **Run a single backend container, with a single uvicorn process.** Live feeds, recordings in
  progress and connected devices are tracked in memory.
- **Rebuild after changing `DOMAIN`** (`--build`). The public API URL is baked into the
  interface at build time.
