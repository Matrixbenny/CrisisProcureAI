# Docker Deployment

## Prerequisites
- Docker Desktop installed and running
- Docker Compose v2 (included with Docker Desktop)

## Start all services
From the project root:

```powershell
docker compose up --build
```

This starts:
- Web portal: http://127.0.0.1:8088
- Compliance-Risk API: http://127.0.0.1:8010
- Prioritization API: http://127.0.0.1:8020

## Stop all services
```powershell
docker compose down
```

## Rebuild after code changes
```powershell
docker compose up --build
```

## Persistent data
SQLite audit history is stored in the named volume:
- `crisisprocure_data`

This means history survives container restarts.

## Troubleshooting
- Port in use: stop conflicting local services on 8088, 8010, or 8020.
- If UI shows APIs offline, confirm containers are healthy in Docker Desktop and that API ports are mapped.
