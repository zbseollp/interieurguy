# InterieurGuy.nl — Astro Frontend

Modern, responsive Astro.js frontend for [interieurguy.nl](https://interieurguy.nl/), preserving the original brand identity while improving UI polish, responsiveness, and accessibility.

## Quick start

```bash
npm install
npm run dev
```

Open [http://localhost:4321/](http://localhost:4321/)

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build static site to `dist/` |
| `npm run preview` | Preview production build |
| `npm run verify:links` | Build and verify all internal links |

## Project structure

```
interieurguy.nl/
├── public/images/          # Locally stored WordPress images
├── src/
│   ├── components/         # Reusable UI components
│   ├── data/               # Navigation, homepage, blog, slugs
│   ├── layouts/            # Base and page layouts
│   ├── pages/              # Routes (homepage, contact, blog, catch-all)
│   └── styles/             # Global CSS design system
└── scripts/verify-links.py
```

## Design tokens

- **Primary:** `#313131`
- **Accent:** `#DFB56C`
- **Text:** `#757575`
- **Font:** Open Sans
- **Container:** 1160px max-width

## Pages

64 static pages including homepage, category pages, product reviews, blog posts, contact, and sitemap. All images are stored locally in `public/images/` — no external hotlinking.
