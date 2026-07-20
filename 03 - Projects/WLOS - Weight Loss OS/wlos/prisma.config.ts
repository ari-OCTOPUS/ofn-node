import { defineConfig } from 'prisma/config';

export default defineConfig({
  schema: 'prisma/schema.prisma',
  migrations: {
    path: 'prisma/migrations',
  },
  datasource: {
    // Migrate/CLI connection. Runtime clients use the pg driver adapter.
    url: process.env.DATABASE_URL ?? 'postgresql://wlos:wlos@localhost:5432/wlos?schema=public',
  },
});
