# ── EduQuest Studio Frontend — Next.js ───────────────────────────────────────

# ── Stage 1: Install dependencies ────────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* pnpm-lock.yaml* ./
# Prefer npm (lock file is present); falls back to pnpm if only pnpm-lock exists
RUN if [ -f pnpm-lock.yaml ]; then \
        npm install -g pnpm && pnpm install --frozen-lockfile; \
    else \
        npm ci; \
    fi

# ── Stage 2: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# The backend URL is resolved at runtime via NEXT_PUBLIC env var —
# baked in at build time so Next.js can inline it for client bundles.
ARG NEXT_PUBLIC_API_URL=http://backend:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# ── Stage 3: Production server ───────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy only the artefacts needed to serve the app
COPY --from=builder /app/public       ./public
COPY --from=builder /app/.next        ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["npm", "run", "start"]
