# Arquitectura del Sistema Inteligente de Logistica Inversa

## 1. Vision General

Sistema de gestion automatizada de devoluciones B2C y B2B con motor de decisiones basado en reglas de negocio predefinidas.

## 2. Stack Tecnologico

### Frontend
- React 18 + TypeScript
- Vite 5 (build tool)
- Zustand (state management)
- Tailwind CSS 3
- Recharts (visualizacion de KPIs)

### Backend
- Python 3.11 + FastAPI
- Pydantic 2 (validacion de datos)
- Uvicorn (ASGI server)
- PostgreSQL 15 (base de datos)
- Redis 7 (cache, rate limiting)

### Infraestructura
- Docker + Docker Compose
- nginx (proxy reverso)

## 3. Arquitectura de Servicios

```
                    +------------------+
                    |    nginx         |
                    |  (Puerto 3000)   |
                    +--------+--------+
                             |
                             v
                    +------------------+
                    |   Frontend       |
                    |   React App      |
                    +------------------+
                             |
                             | HTTP /api/*
                             v
                    +------------------+
                    |   Backend        |
                    |   FastAPI        |
                    |  (Puerto 21001)  |
                    +--------+--------+
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
      +------------+ +------------+ +------------+
      | PostgreSQL | |   Redis    | |   Worker   |
      | (Puerto    | | (Puerto    | |  (Future)  |
      |  25432)    | |  26379)    | +------------+
      +------------+ +------------+
```

## 4. Servicios Docker

| Servicio | Imagen | Puerto | Proposito |
|----------|--------|--------|-----------|
| postgres | postgres:15-alpine | 25432 | Base de datos principal |
| redis | redis:7-alpine | 26379 | Cache y rate limiting |
| backend | Dockerfile local | 21001 | API REST + Motor de decisiones |
| frontend | Dockerfile local | 3000 | Aplicacion web (nginx) |

## 5. Modelo de Datos

### ReturnRequest
- trace_id: UUID unico
- return_id: Identificador legible
- channel: B2C | B2B
- customer_id: Identificador del cliente
- items: Lista de articulos
- status: Estado del retorno
- destination: Destino asignado
- return_method: DROP_OFF | PICKUP | KEEP_IT

### Destinos de Devolucion
- CARRIL_RAPIDO: Restitucion rapida a stock
- OUTLET: Venta en outlet
- RECICLAJE: Reciclaje textil
- KEEP_IT: No requiere retorno fisico
- INSPECCION_B2B: Inspeccion para clientes B2B

## 6. Motor de Decisiones

El motor de reglas evalua cada solicitud segun:

1. **Regla de Canal**: B2C permite Drop-off, B2B requiere Pickup
2. **Regla de Volumen**: >5 articulos o >15kg bloquea Drop-off
3. **Regla de Articulo**: Articulos hipercustomizados van a Inspeccion B2B
4. **Regla de Costo**: Si costo logistico > valor, se activa KEEP_IT

## 7. Endpoints Principales

### Autenticacion
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout

### Devoluciones
- POST /api/returns - Crear devolucion
- GET /api/returns - Listar devoluciones
- GET /api/returns/{return_id} - Detalle de devolucion
- PATCH /api/returns/{return_id}/status - Actualizar estado

### Lotes B2B
- POST /api/batch/upload - Subir archivo CSV
- GET /api/batch/{batch_id}/status - Estado del lote

### KAM
- GET /api/kam/pending - Solicitudes pendientes
- POST /api/kam/{return_id}/approve - Aprobar devolucion
- POST /api/kam/{return_id}/reject - Rechazar devolucion

### Torre de Control
- GET /api/tower/kpis - KPIs gerenciales
- GET /api/tower/distribution - Distribucion de destinos
- GET /api/tower/alerts - Alertas activas

## 8. Flujo de Datos

```
Solicitud B2C
    |
    v
[Validacion] --> 400 Bad Request
    |
    v
[Motor de Decisiones]
    |
    +-- Drop-off --> Generar QR --> 200 OK
    |
    +-- Pickup --> Pendiente --> 200 OK
    |
    +-- Keep-it --> Reembolso --> 200 OK

Solicitud B2B
    |
    v
[Validacion] --> 400 Bad Request
    |
    v
[Motor de Decisiones]
    |
    v
[Requiere KAM?] --> Si --> 202 Pending Approval
    |
    v
[KAM Aprueba] --> Generar Pickup --> 200 OK
```

## 9. Seguridad

- JWT con expiracion de 1 hora
- Rate limiting por IP (Redis)
- CORS configurabe
- Validacion de entrada con Pydantic

## 10. Escalabilidad

- Conexiones BD: pool de 10
- Maximo uploads: 10MB
- Tiempo de respuesta objetivo: <500ms p95

## 11. Rutas del Frontend

| Ruta | Componente | Descripcion |
|------|------------|-------------|
| / | PortalHibrido | Portal de solicitudes B2C/B2B |
| /tower | ControlTowerPage | Torre de control KPIs |
| /logistics | LogisticsDeliveryPage | Logistica de entrega |
| /delivery | LogisticaEntrega | Gestion de entregas |
