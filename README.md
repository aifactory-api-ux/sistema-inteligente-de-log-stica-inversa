# Sistema Inteligente de Logistica Inversa

Modulo Inteligente de Logistica Inversa para la gestion automatizada de devoluciones B2C y B2B.

## Arquitectura

- **Backend**: Python 3.11 + FastAPI + PostgreSQL + Redis
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Infraestructura**: Docker Compose con servicios orquestados

## Inicio Rapido

```bash
# Clonar y ejecutar (configuracion automatica)
./run.sh up

# Ver estado de servicios
./run.sh status

# Ver logs
./run.sh logs

# Detener servicios
./run.sh down
```

## Servicios

| Servicio | Puerto | Descripcion |
|----------|--------|-------------|
| Frontend | 3000 | Portal web de solicitudes de devolucion |
| Backend | 21001 | API REST con motor de decisiones |
| PostgreSQL | 25432 | Base de datos principal |
| Redis | 26379 | Cache y rate limiting |
| API Docs | 21001/docs | Documentacion OpenAPI |

## Rutas Principales

- `http://localhost:3000` - Portal Hibrido B2C/B2B
- `http://localhost:3000/tower` - Torre de Control (KPIs)
- `http://localhost:3000/logistics` - Modulo de Logistica de Entrega
- `http://localhost:21001/docs` - Documentacion API

## Variables de Entorno

Copiar `.env.example` a `.env` y ajustar segun necesidad:

```bash
cp .env.example .env
```

## Requisitos

- Docker 20.10+
- Docker Compose 2.0+

## Estructura del Proyecto

```
.
├── backend/          # API FastAPI
├── frontend/         # Aplicacion React
├── shared/          # Modelos y tipos compartidos
├── docs/            # Documentacion
├── docker-compose.yml
├── run.sh           # Script de inicio
└── .env.example    # Variables de entorno
```
