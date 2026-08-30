import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from './generated/client.js';

/**
 * Prisma 7 engine-less client with the pg driver adapter.
 * One instance per process; pass around explicitly (no globals).
 */
export function makePrisma(databaseUrl: string): PrismaClient {
  const adapter = new PrismaPg({ connectionString: databaseUrl });
  return new PrismaClient({ adapter });
}

export type { PrismaClient };
export * as Db from './generated/client.js';
