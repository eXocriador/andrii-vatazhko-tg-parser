import { z } from 'zod';

const isoDate = z.preprocess((value) => (typeof value === 'string' ? new Date(value) : value), z.date());
const optionalIsoDate = z
  .preprocess((value) => (value ? new Date(value as string) : undefined), z.date().optional());

export const mediaMetaSchema = z.object({
  kind: z.string(),
  file_name: z.string().nullable().optional(),
  mime_type: z.string().nullable().optional(),
  size: z.number().int().nonnegative().nullable().optional(),
  caption: z.string().nullable().optional(),
});

export const fundraiserImportSchema = z.object({
  uid: z.string(),
  channel_id: z.number(),
  channel_username: z.string().nullable().optional(),
  message_id: z.number().int(),
  title: z.string().nullable().optional(),
  body: z.string(),
  original_posted_at: isoDate,
  collected_at: optionalIsoDate.default(() => new Date()),
  amount_requested: z.number().int().nullable().optional(),
  currency: z.string().nullable().optional(),
  donation_links: z.array(z.string()).default([]),
  tags: z.array(z.string()).default([]),
  media: z.array(mediaMetaSchema).default([]),
  source_url: z.string().url().nullable().optional(),
});

export type FundraiserImport = z.infer<typeof fundraiserImportSchema>;
