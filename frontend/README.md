# CivicSignal website

React 19 + Vite + TypeScript. Student page (submit and track complaints) and supervisor
dashboard (review queue, all complaints, repeated problems).

```bash
npm install
npm run dev      # http://localhost:5173 (API calls to /api are proxied to http://127.0.0.1:8000)
npm run lint
npm test         # Vitest + Testing Library
npm run build    # production build in dist/ (served by FastAPI in production)
```

- `src/api.ts` - API calls; the session is an httpOnly cookie (`credentials: 'include'`), no tokens in storage
- `src/auth/` - login state
- `src/pages/` - landing/login page and the student and supervisor workspaces
- `src/components/` - progress tracker, complaint cards, repeated problems, dialogs
- `src/index.css` - design tokens and styles

See the [main README](../README.md) for the whole project.
