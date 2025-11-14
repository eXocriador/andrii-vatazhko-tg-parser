import { Router } from 'express';
import { fundraiserImportSchema, FundraiserImport } from '../schemas/fundraiser.js';
import { env } from '../env.js';
import { Fundraiser } from '../models/fundraiser.js';

const router = Router();

const coerceFundraiser = (input: FundraiserImport) => ({
  uid: input.uid,
  channelId: input.channel_id,
  channelUsername: input.channel_username ?? undefined,
  messageId: input.message_id,
  title: input.title ?? undefined,
  body: input.body,
  originalPostedAt: input.original_posted_at,
  collectedAt: input.collected_at ?? new Date(),
  amountRequested: input.amount_requested ?? undefined,
  currency: input.currency ?? undefined,
  donationLinks: input.donation_links ?? [],
  tags: input.tags ?? [],
  media: input.media ?? [],
  sourceUrl: input.source_url ?? undefined,
});

router.get('/', async (req, res) => {
  const pageParam = (req.query.page as string) ?? '1';
  const sizeParam = (req.query.pageSize as string) ?? '20';
  const parsedPage = Number.parseInt(pageParam, 10);
  const parsedSize = Number.parseInt(sizeParam, 10);
  const page = Math.max(1, Number.isNaN(parsedPage) ? 1 : parsedPage);
  const pageSize = Math.min(100, Math.max(1, Number.isNaN(parsedSize) ? 20 : parsedSize));
  const skip = (page - 1) * pageSize;

  const [data, total] = await Promise.all([
    Fundraiser.find()
      .sort({ originalPostedAt: -1 })
      .skip(skip)
      .limit(pageSize)
      .lean()
      .exec(),
    Fundraiser.countDocuments().exec(),
  ]);

  res.json({ data, pagination: { page, pageSize, total } });
});

router.get('/:uid', async (req, res) => {
  const record = await Fundraiser.findOne({ uid: req.params.uid }).lean().exec();
  if (!record) {
    return res.status(404).json({ error: 'Not found' });
  }
  return res.json(record);
});

router.post('/import', async (req, res) => {
  if (env.JSON_IMPORT_TOKEN) {
    const token = req.header('x-ingestion-key');
    if (token !== env.JSON_IMPORT_TOKEN) {
      return res.status(401).json({ error: 'Invalid ingestion token' });
    }
  }

  const payload = Array.isArray(req.body) ? req.body : [req.body];
  const parsed = payload.map((item) => fundraiserImportSchema.parse(item));

  const operations = parsed.map((item) => ({
    updateOne: {
      filter: { uid: item.uid },
      update: { $set: coerceFundraiser(item) },
      upsert: true,
    },
  }));

  if (operations.length) {
    await Fundraiser.bulkWrite(operations);
  }

  return res.status(201).json({ inserted: parsed.length });
});

export default router;
