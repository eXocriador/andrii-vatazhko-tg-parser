import { config } from 'dotenv';
import { z } from 'zod';

config();

const envSchema = z.object({
  NODE_ENV: z.string().default('development'),
  PORT: z.coerce.number().default(3000),
  MONGODB_URI: z.string().url(),
  INGEST_TOKEN: z.string().optional(),
});

export const env = envSchema.parse(process.env);
