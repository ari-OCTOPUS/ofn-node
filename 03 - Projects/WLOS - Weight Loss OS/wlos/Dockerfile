# Personal-use deployment image. tsx runtime is acceptable at this scale;
# swap to a tsc build stage if/when this becomes multi-user.
# .dockerignore keeps .env, node_modules and .git OUT of the build context.
FROM node:22-alpine

WORKDIR /app

# manifests + prisma first so `npm ci` (and its postinstall `prisma generate`)
# works and caches independently of source changes
COPY package.json package-lock.json* prisma.config.ts ./
COPY prisma ./prisma
COPY packages ./packages
COPY apps/api/package.json ./apps/api/package.json
COPY apps/telegram-bot/package.json ./apps/telegram-bot/package.json

RUN npm ci --omit=optional || npm install

COPY . .

# regenerate against the final source tree (idempotent)
RUN npx prisma generate

USER node
CMD ["npx", "tsx", "apps/telegram-bot/src/main.ts"]
