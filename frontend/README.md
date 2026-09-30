# PolyGraphe — interface

Create trials, record them in real time, look them up afterwards. Next.js (App Router),
Tailwind CSS v4, Biome, uPlot for real-time charts. Visual language after IBM's Carbon design system.

## Running

The [processing server](../backend) must be running (port 8000 by default).

```bash
cp .env.example .env.local   # only if the server is not on http://localhost:8000
pnpm install
pnpm dev                     # http://localhost:3000
```

| Script | |
| --- | --- |
| `pnpm lint` / `pnpm format` | Biome. |
| `pnpm typecheck` | Route types + TypeScript. |
| `pnpm api:types` | Regenerates `src/lib/api/schema.d.ts` from the running server's OpenAPI schema. Run it after changing the backend's API. |

## Structure

```
src/
├── app/                      Routes only: fetch data, compose features.
│   ├── page.tsx              Trial list + search (empty state when there are none)
│   ├── trials/new/           Creation form
│   ├── trials/[id]/          Trial: controls + processed/raw charts
│   └── trials/[id]/edit/     Edit details (also once saved)
├── features/
│   ├── home/                 Hero
│   ├── trials/               Server actions, form (create + edit), table, controls, status tag
│   └── measurements/         Real-time data: store, live feed, charts, kind display registry
├── components/               Design-system primitives (button, field, tag), header, language picker
├── i18n/                     Languages: config, request setup, messages/{en,fr}.json
└── lib/
    ├── api/                  Typed client (generated types), server-side queries
    └── config.ts             Server URL
```

- **Data flow.** Pages are Server Components that call the backend directly (`lib/api/queries.ts`).
  Mutations are Server Actions (`features/trials/actions.ts`) that refresh the page afterwards.
  The browser only talks to the backend for the live websocket.
- **Real time.** `MeasurementStore` holds the series column-wise, in plain TypeScript. It is filled
  with the history rendered by the server, then by `useLiveFeed`. Each (re)connection asks for
  everything since the newest point held, so reconnecting never leaves holes. Charts draw
  straight from the store into uPlot, at most once per animation frame, without React re-renders.
- **New data type.** Nothing to do: every kind the backend stores is plotted. To give it a label,
  a unit, or pick which fields to plot, add it to `features/measurements/kinds.ts`.
- **Watchers and operators.** Anyone can watch. Recordings in progress appear live on the
  home page, and pages re-render by themselves when a trial changes anywhere
  (`RefreshOnTrialChange`, fed by the server's `/trials/events`). Controls (create, edit,
  start, stop, save) only show in operator mode, unlocked with the padlock in the header. The
  server's session token is kept in an httpOnly cookie (`lib/api/operator.ts`).
- **Search** runs as you type and only replaces `?q=` in the URL: no scrolling, no history spam.
- **Languages.** [next-intl](https://next-intl.dev), without locale prefixes in URLs: the
  language comes from the `NEXT_LOCALE` cookie set by the header's picker, or else from the
  browser's preferences. Every text lives in `src/i18n/messages/`, and keys are type-checked
  against `en.json`, so a key missing or misspelt breaks `pnpm typecheck`. To add a language,
  add it to `locales` in `src/i18n/config.ts` and create its message file.
- **Styling.** Design tokens (Carbon colours, IBM Plex) live in `app/globals.css`. Components
  only use those tokens.
