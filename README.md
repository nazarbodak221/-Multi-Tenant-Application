# Multi-Tenant Application

Multi-tenant application with database-per-tenant architecture. Built with FastAPI, Tortoise ORM, and PostgreSQL.

## Architecture

### Database-per-Tenant Pattern

Each organization (tenant) has its own isolated PostgreSQL database:

- **Core Database**: Stores platform-level data (users, organizations)
- **Tenant Databases**: Each organization gets its own database (`tenant_{org_id}`)

### Key Components

- **Core Database Models**: `User`, `Organization` (platform-level)
- **Tenant Database Models**: `TenantUser` (tenant-specific)
- **Database Manager**: Manages connections to core and tenant databases
- **Tenant Context**: Thread-safe tenant ID storage via ContextVar
- **Event System**: Event-driven architecture for decoupled operations
- **JWT Authentication**: Separate tokens for core and tenant scope

### Request Flow

**Core User Request:**
```
Client → Middleware → Dependency (get user) → Endpoint → Service → Repository → Core DB
```

**Tenant User Request:**
```
Client → Middleware (X-Tenant-Id) → Dependency (get tenant user) → Endpoint → Service → Tenant DB
```

### Technology Stack

- FastAPI
- Tortoise ORM
- PostgreSQL
- Aerich (migrations)
- JWT (python-jose)
- bcrypt (passlib)

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

## Local Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd -Multi-Tenant-Application
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create `.env` file:

```env
copy .env .env.example
```

### 4. Initialize Database

Create PostgreSQL database:

```bash
createdb multitenant
```

### 5. Run Migrations

```bash
# Initialize Aerich
aerich init -t app.core.database.TORTOISE_ORM

# Create initial migration
aerich init-db

# Apply migrations
aerich upgrade
```

### 6. Start Application

```bash
uvicorn app.main:app --reload
```

Application will be available at `http://localhost:8000`

## Docker Setup

### 1. Build and Run

```bash
docker-compose up -d
```

### 2. Run Migrations

```bash
docker-compose exec app aerich init -t app.core.database.TORTOISE_ORM
docker-compose exec app aerich init-db
docker-compose exec app aerich upgrade
```

### 3. Access Application

```
http://localhost:8000
```

### Stop Containers

```bash
docker-compose down
```

### Running Tests in Docker

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=app --cov-report=term-missing

# Run specific test file
docker-compose exec app pytest tests/unit/test_security.py

# Run with HTML coverage report
docker-compose exec app pytest --cov=app --cov-report=html

# Run only unit tests
docker-compose exec app pytest tests/unit/

# Run only integration tests
docker-compose exec app pytest tests/integration/

# Run tests with verbose output
docker-compose exec app pytest -v

# Run tests and fail if coverage < 80%
docker-compose exec app pytest --cov=app --cov-fail-under=80
```

**Note**: Tests require PostgreSQL running. In Docker, the database is already available. For local testing, ensure PostgreSQL is running on `localhost:5432`.

#### Docker Compose для тестів

Можна використати окремий compose файл для тестів:

```bash
# Запустити тести з окремою БД
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Після тестів - очистити
docker-compose -f docker-compose.test.yml down -v
```

## Scripts

### Migration Scripts

**Create Initial Migration:**
```bash
python scripts/create_initial_migration.py
```

**Initialize Aerich:**
```bash
python scripts/init_aerich.py
```

**Apply Migrations to Tenant:**
```bash
python scripts/apply_tenant_migrations.py <tenant_id>
```

**Apply Migrations to All Tenants:**
```bash
python scripts/migrate_tenant.py
```

**Apply to Specific Tenant:**
```bash
python scripts/migrate_tenant.py <tenant_id>
```

## Migrations

### Core Database Migrations

**Create Migration:**
```bash
aerich migrate --name "migration_name"
```

**Apply Migration:**
```bash
aerich upgrade
```

**Rollback Migration:**
```bash
aerich downgrade
```

**Show Migration Status:**
```bash
aerich history
```

### Tenant Database Migrations

Migrations are automatically applied when creating a new organization. For existing tenants:

```bash
python scripts/migrate_tenant.py
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register user (core or tenant)
- `POST /api/v1/auth/login` - Login user

### Organizations (Core Only)

- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/organizations/me` - Get my organizations
- `GET /api/v1/organizations/{id}` - Get organization

### Users (Tenant Only)

- `GET /api/v1/users/me` - Get my profile
- `PUT /api/v1/users/me` - Update my profile

### Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Development

### Running Tests

#### Local

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_security.py
```

#### Docker

**Via docker exec (Recommended - найпростіший спосіб):**

```bash
# Run all tests
docker exec multi-tenant-app pytest

# Run with coverage
docker exec multi-tenant-app pytest --cov=app --cov-report=term-missing

# Run specific test file
docker exec multi-tenant-app pytest tests/unit/test_security.py

# Run with HTML coverage report
docker exec multi-tenant-app pytest --cov=app --cov-report=html
# Coverage report will be in htmlcov/ directory (accessible via volume)

# Run only unit tests
docker exec multi-tenant-app pytest tests/unit/

# Run only integration tests
docker exec multi-tenant-app pytest tests/integration/

# Run tests with verbose output
docker exec multi-tenant-app pytest -v

# Run tests and fail if coverage < 80%
docker exec multi-tenant-app pytest --cov=app --cov-fail-under=80
```

**Via docker-compose exec (альтернативний спосіб):**

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=app --cov-report=term-missing

# Run specific test file
docker-compose exec app pytest tests/unit/test_security.py
```

### Linting

```bash
# Ruff
ruff check app/
ruff check app/ --fix
```

### Type Checking

```bash
# MyPy
mypy app/
```

## Project Structure

```
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core functionality
│   ├── events/         # Event system
│   ├── middleware/     # Middleware
│   ├── models/         # Database models
│   ├── repositories/   # Data access layer
│   ├── schemas/        # Pydantic schemas
│   └── services/       # Business logic
├── docs/               # Documentation
├── migrations/         # Database migrations
├── scripts/            # Utility scripts
├── tests/              # Tests
└── requirements.txt    # Dependencies
```

## Manual Testing

### Quick Start

1. Register core user: `POST /api/v1/auth/register`
2. Login core user: `POST /api/v1/auth/login`
3. Create organization: `POST /api/v1/organizations` (with core token)
4. Register tenant user: `POST /api/v1/auth/register` (with X-Tenant-Id header)
5. Login tenant user: `POST /api/v1/auth/login` (with X-Tenant-Id header)
6. Get tenant profile: `GET /api/v1/users/me` (with tenant token + X-Tenant-Id)

**Swagger UI**: `http://localhost:8000/docs` для інтерактивного тестування

### Creating Organization

When an organization is created:
1. Organization record created in core DB
2. Tenant database created
3. Migrations applied to tenant DB
4. `organization.created` event emitted
5. Owner synced to tenant DB as owner user

## License

MIT

