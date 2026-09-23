# DEVELOPMENT PLAN: Sistema Inteligente de Logística Inversa

## 1. ARCHITECTURE OVERVIEW

### Components
```
├── frontend/                    # React 18 + TypeScript + Vite
│   ├── src/
│   │   ├── pages/              # 3 mandatory pages from Figma
│   │   │   ├── ReturnPortalPage.tsx
│   │   │   ├── LogisticsDeliveryPage.tsx
│   │   │   └── ControlTowerPage.tsx
│   │   ├── components/
│   │   │   └── ui/            # 7 base components
│   │   ├── hooks/             # Zustand stores
│   │   ├── services/          # API client
│   │   └── styles/            # Design tokens
│   └── Dockerfile
├── backend/                    # Python FastAPI
│   ├── src/
│   │   ├── main.py            # FastAPI app
│   │   ├── routers/           # API endpoints
│   │   │   ├── returns.py
│   │   │   ├── batch.py
│   │   │   ├── kam.py
│   │   │   ├── kpis.py
│   │   │   └── auth.py
│   │   ├── services/          # Business logic
│   │   │   ├── decision_engine.py
│   │   │   ├── batch_processor.py
│   │   │   └── qr_generator.py
│   │   └── models/            # Pydantic + SQLAlchemy
│   └── Dockerfile
├── shared/                     # Shared contracts
│   ├── types.ts               # TypeScript interfaces
│   └── models.py              # Python Pydantic models
├── docs/
│   └── architecture.md
├── docker-compose.yml
├── run.sh
├── .env.example
└── README.md
```

### Data Models (ReturnStatus, ReturnDestination, ReturnMethod, etc.)
- **ReturnRequest**: Core entity with items, customer info, decision results
- **DecisionInput/DecisionResult**: Decision engine contracts
- **BatchUploadRecord**: B2B batch processing records
- **KPIMetrics**: Control tower KPI values

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/returns | Create return request (B2C/B2B) |
| GET | /api/v1/returns/{id} | Get return details |
| GET | /api/v1/returns | List returns (filtered) |
| POST | /api/v1/returns/batch | Upload B2B batch CSV |
| GET | /api/v1/returns/batch/{batch_id} | Get batch status |
| POST | /api/v1/kam/approve/{return_id} | KAM approval |
| GET | /api/v1/kpi/dashboard | Get KPIs |
| GET | /api/v1/kpi/destinations | Get destination distribution |
| POST | /api/v1/auth/login | JWT authentication |
| GET | /api/v1/health | Health check |

### Business Rules (4-rule Decision Engine)
1. **Rule 1**: B2C 1-5 items, ≤15kg → Drop-off QR
2. **Rule 2**: B2C >5 items OR >15kg → Pickup required
3. **Rule 3**: B2B all cases → Pickup + KAM approval required
4. **Rule 4**: is_customized=true → Reciclaje Textil
5. **Rule 5**: Cost > COGS → Keep-it with refund
6. **Rule 6**: Restock → Carril Rápido (current season) or Outlet

---

## 2. ACCEPTANCE CRITERIA

1. TC001: Radicación B2C estándar (1-5 prendas) y generación de etiqueta QR Drop-off → La solicitud se procesa en tiempo real, se asigna modalidad Drop-off según Regla 1 y se genera el código QR/etiqueta descargable.
2. TC002: Carga de lote masivo B2B que bloquea Drop-off y enruta a Pickup pendiente de KAM → El sistema bloquea la opción de Drop-off, asigna modalidad Pickup y coloca la solicitud en estado 'Pendiente de Autorización KAM'.
3. TC003: Enrutamiento de artículo hipercustomizado B2C con defecto hacia Reciclaje Textil → El motor de reglas asigna automáticamente el destino final a 'Reciclaje Textil' evitando el re-stock a venta regular.
4. TC004: Aplicación de Keep-it con reembolso inmediato cuando costo logístico supera valor → El sistema asigna destino 'Keep-it', autoriza reembolso inmediato y no genera orden de recogida física ni etiqueta de envío.
5. TC005: Autorización de lote B2B por Key Account Manager y generación de orden Pickup → La devolución cambia a estado 'Aprobada' y se dispara la orden de programación de recogida Pickup con el transportista.
6. TC006: Visualización de KPIs gerenciales y distribución de destinos de devolución → El panel muestra los 5 KPIs gerenciales (Tasa de Devolución, Tiempo de Ciclo, Coste Medio, Tasa de Recuperación) y la gráfica de destinos (Carril Rápido, Outlet, Reciclaje, Incidencias B2B, Keep-it).
7. TC007: Evaluación límite B2C: 5 artículos estándar vs 6 artículos y peso exacto 15 kg vs >15 kg → Caso A asigna forzosamente Drop-off con etiqueta QR; Caso B bloquea Drop-off y conmuta a modalidad Pickup.
8. TC008: Evaluación cliente corporativo B2B bajo volumen y umbrales de lote 50 vs 51 prendas → En todos los casos B2B Drop-off queda estrictamente bloqueado, se asigna Pickup y se requiere autorización KAM antes de despachar transportista.
9. TC009: Enrutamiento de artículo is_customized=true B2B a Inspección de Incidencias B2B → El sistema enruta el producto exclusivamente a 'Inspección de Incidencias B2B' sin opción de re-stock directo ni reciclaje automático B2C.
10. TC010: Evaluación límite Keep-it: Transporte + Procesamiento mayor vs igual/menor que COGS → Caso 1 (> COGS) activa Keep-it con reembolso sin retorno físico. Caso 2 (<= COGS) rechaza Keep-it y continúa a la siguiente regla de retorno.
11. TC011: Enrutamiento Re-Stock: Temporada actual a Carril Rápido vs Fuera de temporada/rotura a Outlet → Caso 1 se enruta a 'Carril Rápido' para rápida restitución de stock vendible. Caso 2 se desvía a 'Outlet'.
12. TC001: Tiempo de respuesta del motor de 4 reglas para resoluciones B2C en tiempo real → El 95% de las solicitudes se resuelven en menos de 500 ms sin degradación del servicio.
13. TC002: Carga y procesamiento masivo de lotes B2B con más de 50 prendas o 15 kg → El archivo se procesa en menos de 3 segundos sin saturar memoria ni bloquear la interfaz web.
14. TC003: Control de acceso basado en roles (RBAC) para aprobación KAM y Torre de Control → Acceso denegado con código HTTP 403 Forbidden y evento de seguridad registrado en logs.
15. TC004: Latencia de actualización en tiempo real de los 5 KPIs en Torre de Control → Los 5 KPIs gerenciales se actualizan en pantalla en menos de 1 segundo tras la resolución.
16. TC005: Protección de datos personales (PII) en etiquetas y códigos QR Drop-off → El código QR contiene solo token/identificador opaco; datos personales no viajan en texto plano.
17. TC006: Tolerancia a fallos y consistencia de datos ante interrupción en emisión de Pickups → Transacción atómica: no se generan órdenes huérfanas y el estado queda consistente para reintento.
18. NFR001: Rendimiento del motor de reglas bajo concurrencia pico B2C/B2B simultánea → Tasa de error inferior al 0.1% y tiempo medio de respuesta global inferior a 800 ms.
19. NFR002: Disponibilidad del Portal Híbrido durante picos de devoluciones de temporada → Disponibilidad del servicio de 99.9% sin interrupciones ni reinicios del motor de decisiones.

---

## 3. EXECUTABLE ITEMS

### ITEM 1: Foundation — shared types, models, DB schema, config
**Goal:** Create ALL shared code that other items will import. Includes TypeScript interfaces, Python Pydantic models, PostgreSQL schema, and environment configuration validation.
**Files to create:**
- shared/types.ts (create) - All TypeScript interfaces: ReturnRequest, ReturnItem, DecisionInput, DecisionResult, KPIMetrics, User, AuthPayload, plus enums: ReturnChannel, ReturnDestination, ReturnStatus, ReturnMethod, AlertPriority, AlertType
- shared/models.py (create) - All Pydantic models mirroring TypeScript types with Field validations and ConfigDict settings
- backend/src/db/schema.sql (create) - Complete PostgreSQL schema: returns table with JSONB items column, indexes on (customer_id, status, channel, created_at), return_destinations enum, batch_uploads table, kpi_snapshots table, users table with RBAC roles
- backend/src/config.py (create) - Environment variable validation using pydantic-settings with DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_ALGORITHM, API_VERSION, LOG_LEVEL, with fail-fast on missing required vars
- frontend/src/styles/tokens.ts (create) - Design system tokens: colors (navy #0E1829, dark #17212E, accent emerald #10B981, warning amber #F59E0B, critical #DC2626), typography (Inter family, sizes 30/20/14/11), spacing scale (8/16/24/32/48), border radius (4/8/12/16), elevation shadows
- frontend/src/config.ts (create) - Frontend environment config: API_BASE_URL, APP_VERSION with validation
**Dependencies:** None
**Validation:** TypeScript `npx tsc --noEmit` succeeds; Python `python -c "from shared.models import ReturnRequest"` succeeds
**Role:** role-tl (technical_lead)

---

### ITEM 2: Backend — Core API and Return Request Processing
**Goal:** Implement FastAPI application with return request endpoints, JWT authentication, and health check. Includes POST /api/v1/returns, GET /api/v1/returns/{id}, GET /api/v1/returns, and the decision engine integration.
**Files to create:**
- backend/src/main.py (create) - FastAPI app with OpenAPI docs, CORS, structured logging via structlog, lifespan events for DB init and seed
- backend/src/db/database.py (create) - SQLAlchemy async engine, session factory, get_db dependency
- backend/src/db/init_db.py (create) - create_all() and seed_data() functions with 5 realistic sample returns
- backend/src/routers/returns.py (create) - CRUD endpoints for returns with decision engine call, Pydantic request/response models
- backend/src/routers/auth.py (create) - POST /api/v1/auth/login returning JWT with role claims, JWT validation dependency with role checking
- backend/src/services/decision_engine.py (create) - 4-rule decision engine: Rule1 B2C drop-off (<=5 items, <=15kg), Rule2 B2C pickup (>5 items OR >15kg), Rule3 B2B always pickup+KAM, Rule4 is_customized→Recycling, Rule5 cost>COGS→Keep-it, Rule6 season→FastLane/Outlet
- backend/src/schemas.py (create) - Additional Pydantic schemas for API responses not in shared/models.py
- backend/requirements.txt (create) - fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pydantic, pydantic-settings, python-jose, passlib, structlog, qrcode, Pillow, prometheus-client, opentelemetry-api, opentelemetry-sdk, pytest-asyncio
- backend/src/__init__.py (create) - Package marker
- backend/Dockerfile (create) (build context: ./backend) — multi-stage:3.11-slim, install deps, non-root user, EXPOSE 8000, CMD: uvicorn src.main:app --host 0.0.0.0 --port 8000
**Dependencies:** Item 1
**Validation:** `curl http://localhost:8000/api/v1/health` returns {"status":"healthy"}; `curl -X POST http://localhost:8000/api/v1/returns` with B2C payload returns decision within 500ms
**Role:** role-be (backend_developer)

---

### ITEM 3: Backend — Batch Processing and KAM Authorization
**Goal:** Implement B2B batch upload endpoint with CSV parsing, validation, and KAM approval workflow. Includes POST /api/v1/returns/batch, GET /api/v1/returns/batch/{batch_id}, and POST /api/v1/kam/approve/{return_id} with RBAC enforcement.
**Files to create:**
- backend/src/routers/batch.py (create) - POST /api/v1/returns/batch with CSV file upload using python-multipart, pandas processing, validation of SKU/quantity/reason_code, returns BatchUploadResponse with processing_time_ms
- backend/src/routers/kam.py (create) - POST /api/v1/kam/approve/{return_id} with JWT role validation (requires 'KAM' role), PATCH /api/v1/kam/reject/{return_id}, GET /api/v1/kam/pending for KAM queue
- backend/src/services/batch_processor.py (create) - Async batch processing with memory-efficient pandas chunking for >50 records, validation errors collection, batch_id generation
- backend/src/services/qr_generator.py (create) - QR code generation using qrcode library, returns Base64 PNG, uses opaque token not PII data
- backend/src/models/models.py (create) - SQLAlchemy ORM models: ReturnModel, BatchUploadModel, UserModel with role-based access
- backend/src/db/migrations/001_initial.py (create) - Alembic migration for returns, batch_uploads, users tables
**Dependencies:** Item 1, Item 2
**Validation:** Upload 100-record CSV processes in <3 seconds; KAM endpoint returns 403 for non-KAM roles; approved B2B return changes status to 'APROBADO' and generates pickup order
**Role:** role-be (backend_developer)

---

### ITEM 4: Backend — KPI Endpoints and Control Tower Data
**Goal:** Implement KPI dashboard endpoints for the Control Tower. Includes GET /api/v1/kpi/dashboard returning 5 KPIs and GET /api/v1/kpi/destinations returning destination distribution for charts.
**Files to create:**
- backend/src/routers/kpis.py (create) - GET /api/v1/kpi/dashboard returning KPIMetrics (return_rate, cycle_time_hours, avg_cost, recovery_rate, total_returns), GET /api/v1/kpi/destinations returning dict of ReturnDestination→count/percentage, GET /api/v1/kpi/alerts returning active alerts
- backend/src/services/kpi_service.py (create) - KPI calculation from DB aggregation queries with <100ms target, destination distribution aggregation, alert generation based on thresholds
- backend/src/services/alerts.py (create) - Alert engine checking: inspection saturation >80%, pending B2B approvals >10, return_rate spike >20%, cycle_time >48h, cost_threshold_breach
- backend/src/models/enums.py (create) - SQLAlchemy enum types matching shared/models.py
**Dependencies:** Item 1, Item 2
**Validation:** GET /api/v1/kpi/dashboard returns all 5 KPIs in <1 second; destination distribution includes all 5 destinations (CARRIL_RAPIDO, OUTLET, RECICLAJE, INSPECCION_B2B, KEEP_IT)
**Role:** role-be (backend_developer)

---

### ITEM 5: Frontend — Return Portal Page (B2C/B2B Hybrid)
**Goal:** Implement the Portal Híbrido de Solicitud de Devolución page following Figma frame. Includes ProfileSelector for B2C/B2B flow selection, ReturnForm for manual entry, BatchUploadZone for B2B CSV, and DecisionResolution component showing outcome.
**Files to create:**
- frontend/src/pages/ReturnPortalPage.tsx (create) - Main portal page with AppNavigationHeader, HeroHeader, ProfileSelector, ReturnIntakeWorkflow, DecisionResolution, FinancialSummary sections per Figma specs
- frontend/src/components/ui/ProfileSelector.tsx (create) - Two profile cards (B2C Consumer, B2B Corporate) with selection state
- frontend/src/components/ui/ReturnForm.tsx (create) - Multi-field form: customer_id, order_reference, items array with SKU/quantity/price/reason, contact info, conditional pickup_address
- frontend/src/components/ui/DecisionOutcomeCard.tsx (create) - Displays decision result: destination badge, return method, QR code if Drop-off, refund amount
- frontend/src/components/ui/PrimaryButtonCTA.tsx (create) - Styled button with loading state, disabled state, and success variant
- frontend/src/components/ui/StatusBadge.tsx (create) - Colored badge for status (PENDIENTE/Aprobado/Rechazado) and destination types
- frontend/src/components/ui/BatchUploadZone.tsx (create) - react-dropzone integration with drag-drop CSV upload, file validation, upload progress
- frontend/src/services/api.ts (create) - Axios client with auth interceptor, typed API methods matching backend endpoints
- frontend/src/pages/__init__.py (create) - Package marker
- frontend/src/components/ui/__init__.py (create) - Package marker
**Dependencies:** Item 1
**Validation:** Page loads at /portal with navigation working to other pages; B2C form submits and receives QR code; B2B batch upload processes CSV and shows pending status
**Role:** role-fe (frontend_developer)

---

### ITEM 6: Frontend — Logistics Delivery Module
**Goal:** Implement the Módulo Logístico de Entrega y Recogida page showing assigned method, QR code/label, pickup details, and tracking timeline. Displays DecisionOutcomeCard with method-specific content.
**Files to create:**
- frontend/src/pages/LogisticsDeliveryPage.tsx (create) - Page with AppNavigationHeader, Hero section, DecisionOutcomeCard, QR Drop-off display, Pickup special section, Mapa de puntos, Packaging guide, Timeline tracking
- frontend/src/components/ui/DropOffDisplay.tsx (create) - QR code visualization using qrcode.react, downloadable label button, drop-off point information
- frontend/src/components/ui/PickupDisplay.tsx (create) - Pickup address, scheduled time, carrier information, special instructions for B2B
- frontend/src/components/ui/TrackingTimeline.tsx (create) - Vertical timeline with status nodes (Solicitado, Pickup Programado, En Transito, Entregado), timestamps, current state highlight
- frontend/src/components/ui/PackagingGuide.tsx (create) - Collapsible guide with packaging requirements, labeling instructions
**Dependencies:** Item 1, Item 5
**Validation:** Page loads at /logistics/{return_id} showing correct method-specific content; QR code renders and is downloadable; timeline shows correct status progression
**Role:** role-fe (frontend_developer)

---

### ITEM 7: Frontend — Control Tower Dashboard
**Goal:** Implement the Torre de Control de Retornos y Supervisión page with KPI grid, destination distribution chart, alerts panel, KAM approval queue, and data density table.
**Files to create:**
- frontend/src/pages/ControlTowerPage.tsx (create) - Main control tower page with KPI grid, destination distribution, alerts, KAM validation, data table per Figma frame
- frontend/src/components/ui/KPIStatCard.tsx (create) - Metric card with label, value, trend indicator, color-coded by threshold
- frontend/src/components/ui/DestinationChart.tsx (create) - Horizontal bar chart using Recharts showing destination distribution with labels and percentages
- frontend/src/components/ui/AlertsPanel.tsx (create) - Alert list with priority indicators (CRITICAL/HIGH/MEDIUM/LOW), dismiss action, alert type icons
- frontend/src/components/ui/KAMApprovalQueue.tsx (create) - Table of pending B2B approvals with Approve/Reject buttons, customer info, batch summary
- frontend/src/components/ui/DataDensityTable.tsx (create) - High-density returns table: trace_id, customer, channel, items, destination, status, created_at, actions column
- frontend/src/hooks/useKPIs.ts (create) - Zustand store + polling hook for KPI data with 1-second refresh target
- frontend/src/hooks/useAlerts.ts (create) - Zustand store for alerts with WebSocket-ready structure
**Dependencies:** Item 1, Item 5
**Validation:** Page loads at /control-tower; all 5 KPIs display; destination chart shows 5 bars; alerts panel shows active alerts; data table is sortable and filterable
**Role:** role-fe (frontend_developer)

---

### ITEM 8: Frontend — State Management and Navigation
**Goal:** Implement global state management with Zustand, routing with React Router, and AppNavigationHeader shared across all pages. Includes auth state and return context.
**Files to create:**
- frontend/src/stores/authStore.ts (create) - Zustand store: user, token, role, login(), logout(), isAuthenticated
- frontend/src/stores/returnStore.ts (create) - Zustand store: currentReturn, returns list, filters, setCurrentReturn(), fetchReturns()
- frontend/src/components/ui/AppNavigationHeader.tsx (create) - Navigation header with brand logo, nav links (Portal, Logistics, Control Tower), alerts indicator badge, user menu
- frontend/src/App.tsx (create) - Root component with Router, AuthProvider wrapper, layout structure
- frontend/src/main.tsx (create) - Entry point with StrictMode, rendering App
- frontend/src/index.css (create) - Global styles with Tailwind directives, custom scrollbar, font-face for Inter
- frontend/tailwind.config.js (create) - Tailwind config extending with design tokens, content paths
- frontend/vite.config.ts (create) - Vite config with React plugin, proxy to backend API
- frontend/package.json (create) - All dependencies: react, react-dom, react-router-dom, zustand, axios, recharts, qrcode.react, react-dropzone, date-fns, lucide-react, tailwindcss, postcss, autoprefixer, @types/* packages, build scripts
- frontend/tsconfig.json (create) - TypeScript config with strict mode, path aliases
**Dependencies:** Item 1
**Validation:** Navigation between all 3 pages works; auth state persists across page reloads; Zustand stores are typed and functional
**Role:** role-fe (frontend_developer)

---

### ITEM 9: Infrastructure & Deployment
**Goal:** Complete Docker orchestration with all services, health checks, environment configuration, and local run script. Zero manual steps after clone.
**Files to create:**
- docker-compose.yml (create) - Services: backend (build context ./backend, port 8000, depends on postgres and redis), frontend (build context ./frontend, port 3000, depends on backend), postgres (image postgres:15, volume, port 5432), redis (image redis:7-alpine, port 6379). All services have healthcheck and depends_on with condition service_healthy. Networks: frontend-net, backend-net with proper linking.
- .env.example (create) - All environment variables documented: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/logistics, REDIS_URL=redis://localhost:6379, JWT_SECRET=your-secret-key, JWT_ALGORITHM=HS256, API_VERSION=v1, LOG_LEVEL=INFO, FRONTEND_URL=http://localhost:3000
- .gitignore (create) - Excludes: node_modules, dist, .env, __pycache__, *.pyc, .pytest_cache, .venv, venv, .DS_Store, *.log
- .dockerignore (create) - Excludes: node_modules, .git, *.log, dist, .env, __pycache__, alembic/versions
- run.sh (create) - Checks Docker is running, docker-compose build, docker-compose up -d, waits for all healthchecks, prints access URLs (Frontend: http://localhost:3000, API: http://localhost:8000/docs)
- README.md (create) - Project description, prerequisites (Docker, Docker Compose), quick start (./run.sh), folder structure, API documentation links, development commands
- docs/architecture.md (create) - System architecture diagram, component descriptions, data flow, technology choices rationale
**Dependencies:** Item 2, Item 3, Item 4, Item 5, Item 6, Item 7, Item 8
**Validation:** `./run.sh` completes successfully; all 4 services report healthy; http://localhost:3000 returns frontend; http://localhost:8000/docs returns OpenAPI docs; no orphan containers or errors in logs
**Role:** role-devops (devops_support)