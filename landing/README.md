# Agora Landing Page

A futuristic landing page for the Agora workflow orchestration framework. Built with React, Vite, and TailwindCSS.

## Features

- **Glassmorphism UI** with neon accent colors (blue, violet, cyan)
- **Animated Hero** with interactive node-flow SVG diagram
- **Feature Showcase** — 6 feature cards highlighting Agora's capabilities
- **Interactive Demo** — Tabbed code viewer with syntax highlighting and animated terminal
- **Quick Start Guide** — 4-step setup with copy-to-clipboard code blocks
- **Beta Signup** — Email collection form with validation
- **Scroll Animations** — Entrance animations using Intersection Observer
- **Fully Responsive** — Mobile, tablet, and desktop optimized
- **Secure** — Whitelist-based file serving, admin-protected email access

## Quick Start

```bash
# Install dependencies
npm install

# Run dev servers (Vite + Express)
npm run dev
```

The landing page will be available at **http://localhost:5174**

## Development

### Run Servers Separately

**Frontend (Vite on port 5174):**
```bash
npm run dev:frontend
```

**Backend (Express on port 3001):**
```bash
npm run server
```

### Build for Production

```bash
npm run build
```

Outputs optimized static files to `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
landing/
├── src/
│   ├── components/
│   │   ├── Navbar.tsx          # Fixed glassmorphism nav
│   │   ├── Hero.tsx            # Hero with animated SVG
│   │   ├── Features.tsx        # 6 feature cards
│   │   ├── Demo.tsx            # Interactive code demo
│   │   ├── QuickStart.tsx      # Step-by-step guide
│   │   ├── BetaSignup.tsx      # Email signup form
│   │   └── Footer.tsx          # Footer with links
│   ├── hooks/
│   │   └── useScrollReveal.ts  # Intersection Observer hook
│   ├── utils/
│   │   └── api.ts              # Email API client
│   ├── App.tsx                 # Main layout
│   ├── main.tsx                # React entry point
│   └── index.css               # Tailwind + custom styles
├── public/
│   └── agora-logo.svg          # Agora logo
├── .data/
│   └── emails.json             # Beta signups (secured)
├── server.js                   # Express server for email collection
├── vite.config.ts              # Vite config with security middleware
├── package.json
└── README.md
```

## Email Collection

Beta signups are collected via the Express server on port 3001.

### View Collected Emails (Admin Only)

```bash
curl -H "X-Admin-Key: agora-admin-secret" http://localhost:3001/api/emails
```

### Set Custom Admin Key

```bash
# Development
ADMIN_KEY=your-secret-here npm run server

# Production
ADMIN_KEY=your-secret-here node server.js
```

## Security

- **Whitelist-based file serving** — Only `/`, `/index.html`, `/src/*`, `/node_modules/*`, `/@*`, `/api/*`, and `/agora-logo.svg` are accessible
- **All config files blocked** — `server.js`, `package.json`, `tsconfig*.json`, etc. return 403
- **Email data secured** — Stored in `.data/emails.json` (not web-accessible)
- **Admin authentication** — `GET /api/emails` requires `X-Admin-Key` header

## API Endpoints

### `POST /api/signup`

Submit a beta signup email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "You're on the list! We'll be in touch soon."
}
```

**Error Responses:**
- `400` — Invalid or missing email
- `409` — Email already on waitlist

### `GET /api/emails` (Admin Only)

Retrieve all collected emails.

**Request:**
```bash
curl -H "X-Admin-Key: agora-admin-secret" http://localhost:3001/api/emails
```

**Response:**
```json
{
  "count": 42,
  "emails": [
    {
      "email": "user@example.com",
      "timestamp": "2026-02-17T03:30:00.000Z"
    }
  ]
}
```

**Error Response:**
- `401` — Unauthorized (missing or invalid admin key)

## Tech Stack

- **React 19** — UI framework
- **Vite 7** — Build tool and dev server
- **TailwindCSS 4** — Styling with custom futuristic theme
- **TypeScript** — Type safety
- **Prism.js** — Syntax highlighting for code blocks
- **Express** — Backend server for email collection

## Design System

### Colors

- **Background:** `#0A0A0F` (dark-900)
- **Neon Blue:** `#00D4FF`
- **Neon Violet:** `#7B61FF`
- **Neon Cyan:** `#00FFE0`
- **Neon Pink:** `#FF61D8`

### Typography

- **Body:** Inter (Google Fonts)
- **Code:** JetBrains Mono (Google Fonts)

### Effects

- Glassmorphism cards with backdrop blur
- Glow effects on hover
- Animated gradient text
- Pulse animations on SVG nodes
- Scroll-triggered entrance animations
- Typing cursor effect in terminal

## License

MIT License — Part of the Agora project
