# MyCloud Backend

**MyCloud** is a self-hosted personal cloud storage backend designed to run on a Windows laptop and manage files stored on an external HDD (e.g. 500 GB development HDD or 2 TB production HDD).

It provides a clean, secure REST API with server-side sessions, Argon2id password hashing, path traversal protection, chunked streaming file transfers, and metadata management via SQLite.

---

## 1. Requirements

- **Python**: 3.12+ (or 3.13+)
- **Operating System**: Windows 10/11 (or Linux/macOS for development)
- **Storage**: Local disk folder or dedicated external HDD

---

## 2. Installation

1. Open a terminal in the `backend/` directory:

   ```powershell
   cd backend
   ```

2. Create and activate a Python virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install pinned dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 3. Configuration

Copy the example environment configuration:

```powershell
copy .env.example .env
```

Edit `.env` to configure your storage drive and application settings:

```env
# Application Configuration
APP_NAME=MyCloud
APP_ENV=development

# Server Network
HOST=127.0.0.1
PORT=8000

# SQLite Database Location
DATABASE_URL=sqlite:///./data/mycloud.db

# Storage Path (Point to your external HDD mount or local folder)
STORAGE_PATH=E:\MyCloudStorage

# Security & Sessions
SESSION_EXPIRE_MINUTES=10080
MAX_UPLOAD_SIZE_MB=5120
SECRET_KEY=replace-with-a-random-secret-key

# Cookie Configuration
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
COOKIE_NAME=mycloud_session

# Initial Admin User Credentials
ADMIN_INITIAL_USERNAME=admin
ADMIN_INITIAL_EMAIL=admin@example.com
ADMIN_INITIAL_PASSWORD=YourSecurePassword123!
```

> **HDD Migration Note**: When replacing your 500 GB development HDD with a 2 TB production HDD, copy the data folder across and simply update `STORAGE_PATH=F:\MyCloudStorage` (or the new drive letter) in `.env`.

---

## 4. Database Initialization

Initialize database tables, storage directory structure, and the initial administrator account:

```powershell
python -m app.db.init_db
```

This creates:

- SQLite database file at the configured `DATABASE_URL` path
- Storage directories: `<STORAGE_PATH>/users/` and `<STORAGE_PATH>/tmp/`
- Seed administrator user from `.env`

---

## 5. Running the Backend

Start the development server with hot-reloading:

```powershell
python run.py
```

The application will start on `http://127.0.0.1:8000`.

---

## 6. Interactive API Documentation

Once the server is running, open the interactive Swagger OpenAPI docs in your browser:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 7. Storage Architecture & Path Security

- **Central Storage Boundary**: All direct disk operations are strictly isolated inside `StorageService`. Routers and other services never interact with the filesystem directly.
- **Path Traversal Protection**: All paths are resolved and verified against `STORAGE_PATH` using `pathlib.Path.resolve()` and `is_relative_to`.
- **Windows Sanitization**: Filenames are validated against invalid Windows characters (`<>:"/\|?*`), ASCII control characters, null bytes, and Windows reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).
- **Decoupled Physical Storage**: Uploaded files receive UUID-based storage filenames (`<uuid>.<ext>`) within `<STORAGE_PATH>/users/<user_id>/files/`, preventing filename collisions and arbitrary path injection.
- **Chunked Streaming**: Uploads stream to a temporary file (`<STORAGE_PATH>/tmp/<uuid>.tmp`) while simultaneously computing a SHA-256 checksum and enforcing maximum size constraints before atomically moving to their final destination. Downloads are streamed chunk-by-chunk.

---

## 8. Running Automated Tests

Run the complete pytest test suite:

```powershell
pytest -v
```

The test suite covers:

- **Authentication**: Login, logout, session expiration, token hashing, revocation, password change.
- **Storage**: Directory creation, streaming write/read, SHA-256 checksum calculation, disk usage.
- **Folders**: Virtual folder hierarchy, nesting, duplicate checks, cascade/soft deletion, ownership isolation.
- **Files**: Chunked upload, streaming download, rename, soft deletion, storage inconsistency resilience.
- **Security**: Windows path traversal payloads (`../../`, `..\..\`, `C:\`, UNC `\\`), reserved device names, null bytes, cross-user isolation.

---

## 9. Tailscale Remote Access

The backend is designed as a standard HTTP service that runs cleanly behind **Tailscale**:

1. Install and authenticate Tailscale on the Windows host machine.
2. Configure `HOST=0.0.0.0` so the API binds to all interfaces.
3. Use the Tailscale IP only as the client-facing address, for example `http://100.99.177.87:8000`.
4. Keep `COOKIE_SECURE=false` for development over plain HTTP; set it to `true` only when serving over HTTPS in a future production setup.
5. Clients accessing the Tailscale node can interact directly with all `/api/v1/` endpoints.

### Tailscale Access

Windows Tailscale IP:

```text
100.99.177.87
```

Backend:

```text
http://100.99.177.87:8000
```

Swagger:

```text
http://100.99.177.87:8000/docs
```

This is private Tailscale access only and the client device must be connected to the same tailnet.
