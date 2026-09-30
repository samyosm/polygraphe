# Deploying PolyGraphe

Everything runs on one server with Docker Compose: InfluxDB, the processing server and the
interface. The host's NGINX handles HTTPS and routes `polygraphe.samy.dev`:

```
https://polygraphe.samy.dev/        → frontend  127.0.0.1:3000
https://polygraphe.samy.dev/api/…   → backend   127.0.0.1:8000   (REST + websockets)
```

## Prerequisites

- Docker with the Compose plugin (`docker compose version`), NGINX, certbot.
- A DNS `A` (and `AAAA` if you have IPv6) record for `polygraphe.samy.dev` pointing to the
  server, and ports 80 and 443 reachable from the internet.

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

Also change `OPERATOR_PASSWORD`: it is the only thing standing between watchers and the controls.

> `INFLUX_TOKEN` and `INFLUX_ADMIN_PASSWORD` are only read when InfluxDB starts for the first
> time. Changing them afterwards requires deleting the `influxdb-data` volume (and its data).

## 2. Start the stack

```bash
docker compose up -d --build
docker compose ps                        # all three should become "healthy"
curl http://127.0.0.1:8000/health        # {"status":"ok",...}
```

## 3. NGINX and HTTPS

Get a certificate first: the site file refers to it, so NGINX will not load the site without it.

```bash
sudo certbot certonly --nginx -d polygraphe.samy.dev
```

Then enable the site:

```bash
sudo cp deploy/nginx/polygraphe.samy.dev.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/polygraphe.samy.dev.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

If `nginx -t` complains that `$connection_upgrade` is a duplicate, another site already defines
that `map`: delete it from `polygraphe.samy.dev.conf`. If you changed `FRONTEND_PORT` or
`BACKEND_PORT`, change the two `proxy_pass` lines to match. Certbot renews the certificate by
itself.

Check: https://polygraphe.samy.dev (interface) and https://polygraphe.samy.dev/api/docs (API).

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
