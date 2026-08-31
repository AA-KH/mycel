# Mycel — Frontend

> React + Vite powered frontend for the Mycel multi-agent monitoring platform.

**Author**: Kaushal Jindal
**Project**: Mycel
**Country**: India 🇮🇳
**Timezone**: IST (Asia/Kolkata, UTC+5:30)

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| **React** | 19.1 | UI framework |
| **TypeScript** | 5.5 | Type-safe JavaScript |
| **Vite** | 5.3 | Lightning-fast build tool & HMR |
| **TailwindCSS** | 4.1 | Utility-first CSS framework |
| **React Router** | 6.25 | Client-side routing |
| **Auth0 React SDK** | 2.4 | Authentication & authorization |

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── pages/                    # Page-level components
│   │   ├── LoginPage.tsx         # Login / landing page (public)
│   │   ├── HomePage.tsx          # Homepage splash (authenticated)
│   │   └── OfficePage.tsx        # Pixel-art virtual office dashboard
│   │
│   ├── components/               # Reusable UI components
│   │
│   ├── App.tsx                   # Root app with routing
│   └── main.tsx                  # React entry point
│
├── public/                       # Static assets
│   └── index.html
│
├── index.html                    # HTML template
├── vite.config.ts                # Vite configuration
├── tailwind.config.js            # Tailwind CSS configuration
├── tsconfig.json                 # TypeScript configuration
└── package.json                  # Dependencies & scripts
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Backend API running at `http://localhost:8000`

### Install Dependencies
```bash
cd frontend
npm install
```

### Configure Environment
Create a `.env` file inside the `frontend/` directory:

```env
# Auth0 Configuration
VITE_AUTH0_DOMAIN=your-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id

# Mycel Backend API
VITE_API_URL=http://localhost:8000
```

### Run Dev Server
```bash
npm run dev
```

Open **http://localhost:5173** — welcome to **Mycel**! 🎉

---

## 🛤️ Routes

| Path | Component | Auth Required | Description |
|---|---|---|---|
| `/` | `LoginPage` | No | Login / landing page |
| `/home` | `HomePage` | Yes | Animated home screen |
| `/office` | `OfficePage` | Yes | Live pixel-art virtual office |

---

## 🔐 Authentication

The app uses **Auth0** for user authentication. Once logged in, the user receives a JWT token that is sent with every API request to the Mycel backend.

```env
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
```

Make sure to add `http://localhost:5173` to your Auth0 app's:
- **Allowed Callback URLs**
- **Allowed Logout URLs**
- **Allowed Web Origins**

---

## 📡 Connecting to the Backend

The frontend connects to the **Mycel FastAPI backend** at `VITE_API_URL`.

- **REST API**: Used for auth, API key management, and agent session data.
- **WebSockets** (`/api/realtime/ws`): Used for live agent status updates in the pixel-art office.

---

## 📦 Build & Deploy

### Production Build
```bash
npm run build
```
Output is in the `dist/` folder.

### Preview Production Build
```bash
npm run preview
```

### Deploy (Vercel — Recommended for India)
```bash
npm install -g vercel
vercel --prod
```

Set these environment variables in your Vercel project settings:
```
VITE_AUTH0_DOMAIN=...
VITE_AUTH0_CLIENT_ID=...
VITE_API_URL=https://your-backend.com
```

---

## 🐛 Troubleshooting

### Auth0 Login Not Working
- Check `VITE_AUTH0_DOMAIN` and `VITE_AUTH0_CLIENT_ID` in your `.env`
- Ensure `http://localhost:5173` is in Auth0 Allowed Callback URLs

### CORS Errors
The backend already has CORS enabled for all origins in dev. If you face issues in production, set `allow_origins` in `backend/main.py` to your frontend's domain.

### Env Variables Undefined
All frontend environment variables must be prefixed with `VITE_`. Restart the dev server after changing `.env`.

---

*Built with ❤️ in India by Kaushal Jindal*
