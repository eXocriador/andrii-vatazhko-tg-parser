import { config } from 'dotenv';
import { z } from 'zod';

config();

const envSchema = z.object({
  NODE_ENV: z.string().default('development'),
  PORT: z.coerce.number().default(4000),
  MONGODB_URI: z.string().url(),
  JSON_IMPORT_TOKEN: z.string().optional(),
});

export const env = envSchema.parse(process.env);
