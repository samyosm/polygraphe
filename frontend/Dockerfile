FROM node:22-alpine AS base
RUN corepack enable
WORKDIR /app

FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Public URL of the processing server, e.g. https://polygraphe.samy.dev/api.
# Baked into the browser code: changing it means rebuilding the image.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_OUTPUT=standalone \
    NEXT_TELEMETRY_DISABLED=1
RUN test -n "$NEXT_PUBLIC_API_URL" || (echo "NEXT_PUBLIC_API_URL build arg is required" && exit 1)
RUN pnpm build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000
RUN addgroup -S polygraphe && adduser -S polygraphe -G polygraphe
COPY --from=build /app/public ./public
COPY --from=build --chown=polygraphe:polygraphe /app/.next/standalone ./
COPY --from=build --chown=polygraphe:polygraphe /app/.next/static ./.next/static
USER polygraphe

EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s \
    CMD wget -q -O /dev/null http://127.0.0.1:3000/logos/un.svg || exit 1
CMD ["node", "server.js"]
