# DocChat Frontend (React + Vite + Tailwind)

React 19, Vite, JavaScript, Axios, Tailwind CSS v4, React Router.

## Quick start (macOS)

Requires Node 20+ (`brew install node`) and the backend running on port 8000.

```bash
cd frontend
cp .env.example .env     # VITE_API_URL=http://localhost:8000/api
npm install
npm run dev
```

Open http://localhost:5173. Register an account, upload a PDF/DOCX/TXT, click **Chat**.

## Scripts
| Command | Purpose |
|---|---|
| `npm run dev` | Dev server with hot reload (port 5173) |
| `npm run build` | Production build into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Lint |

## Structure
```
src/
  api/          client.js (axios + JWT attach + auto refresh), auth.js, documents.js, chat.js
  context/      AuthContext.jsx (login/register/logout, session restore)
  components/   Navbar, ProtectedRoute, AuthForm, UploadBox, DocumentCard, ChatWindow, MessageBubble, Spinner
  pages/        LoginPage, RegisterPage, DashboardPage (upload + list), ChatPage (per-document chat)
```

## Notes
- Tokens are kept in `localStorage`. On a 401 the axios interceptor refreshes the access token once and replays the request; if refresh fails you are logged out.
- Chat history is loaded from the backend per document, so it persists across reloads and devices.
- If the browser shows a CORS error, make sure the frontend origin is listed in the backend's `CORS_ALLOWED_ORIGINS` (default covers `localhost:5173` and `127.0.0.1:5173`).
- Changed `.env`? Restart `npm run dev` (Vite reads env at startup).
