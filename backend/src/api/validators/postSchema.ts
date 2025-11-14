import { z } from 'zod';

export const postPayloadSchema = z.object({
  tg_id: z.number().int().nonnegative(),
  type: z.enum(['fundraising', 'report']),
  text: z.string().min(1),
  images: z.array(z.string()).default([]),
  links: z.array(z.string()).default([]),
  date: z.preprocess((val) => {
    if (val instanceof Date) return val;
    if (typeof val === 'string' || typeof val === 'number') {
      const parsed = new Date(val);
      return Number.isNaN(parsed.getTime()) ? undefined : parsed;
    }
    return undefined;
  }, z.date()),
});

export const importRequestSchema = z.union([postPayloadSchema, z.array(postPayloadSchema)]);

export type PostPayload = z.infer<typeof postPayloadSchema>;
