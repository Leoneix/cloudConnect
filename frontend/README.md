# MyCloud Frontend

The modern web frontend for **MyCloud**, a self-hosted personal cloud storage application.

Built with **React**, **TypeScript**, **Vite**, **React Router**, **TanStack Query**, and **Axios**.

---

## 1. Requirements

- **Node.js**: 20.x or 24.x LTS
- **npm**: 10.x or 11.x
- **Backend**: FastAPI backend running on `http://127.0.0.1:8000` (or configured via `.env`)

---

## 2. Installation

1. Navigate to the `frontend/` directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

---

## 3. Configuration

Create or edit the `.env` file in this directory:

```env
# Backend API Base URL
VITE_API_BASE_URL=http://100.99.177.87:8000
```

> **Tailscale / Remote Note**: The frontend must talk to the backend over the Tailscale IP while the app is being accessed from the phone. This keeps API requests on the private tailnet instead of the phone's local loopback.

### Tailscale Access

Frontend URL:

```text
http://100.99.177.87:5173
```

Backend URL:

```text
http://100.99.177.87:8000
```

These URLs are intended for private Tailscale access only and require the client to be on the same tailnet.

---

## 4. Development Server

Start the Vite development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The application will be available at: [http://127.0.0.1:5173](http://127.0.0.1:5173).

---

## 5. Production Build

Type-check and bundle the application for production:

```bash
npm run build
```

Preview the production build locally:

```bash
npm run preview
```

---

## 6. Running Tests

Run the Vitest test suite:

```bash
npm run test
```

---

## 7. Features & UX

- **Modern Cloud Drive UI**: Minimalist, fast, and responsive layout across Windows desktops, tablets, iPhones, and Android devices.
- **Authentication**: Seamless session checking and login with HTTP-only cookies; protected routes with automatic redirection.
- **File & Folder Management**: Dynamic folder hierarchy, URL-based navigation (`?folder=<id>`), creation, renaming, and soft deletion.
- **Multipart Uploads with Progress**: File selection queue with real-time percentage and byte tracking.
- **Streaming Downloads**: Direct streaming downloads via the backend without loading large files into browser memory.
- **Real-time Storage Indicator**: Dynamic disk capacity bar showing used, free, and total disk space from the underlying HDD.
