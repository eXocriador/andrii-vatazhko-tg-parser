import type { Request, Response, NextFunction } from 'express';
import { importRequestSchema, type PostPayload } from '../api/validators/postSchema.js';
import { PostModel } from '../models/postModel.js';

const MAX_LIMIT = 100;

export async function importPosts(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const parsed = importRequestSchema.parse(req.body);
    const payloads: PostPayload[] = Array.isArray(parsed) ? parsed : [parsed];

    if (!payloads.length) {
      res.status(400).json({ error: 'No payloads supplied' });
      return;
    }

    const operations = payloads.map((payload) => ({
      updateOne: {
        filter: { tg_id: payload.tg_id },
        update: { $set: payload },
        upsert: true,
      },
    }));

    await PostModel.bulkWrite(operations, { ordered: false });
    res.status(201).json({ inserted: payloads.length });
  } catch (error) {
    next(error);
  }
}

export async function listPosts(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const pageParam = typeof req.query.page === 'string' ? req.query.page : '1';
    const limitParam = typeof req.query.limit === 'string' ? req.query.limit : '20';
    const parsedPage = Number.parseInt(pageParam, 10);
    const parsedLimit = Number.parseInt(limitParam, 10);

    const page = Number.isNaN(parsedPage) || parsedPage < 1 ? 1 : parsedPage;
    const limit = Number.isNaN(parsedLimit) || parsedLimit < 1 ? 20 : Math.min(MAX_LIMIT, parsedLimit);
    const skip = (page - 1) * limit;

    const [data, total] = await Promise.all([
      PostModel.find()
        .sort({ date: -1 })
        .skip(skip)
        .limit(limit)
        .lean()
        .exec(),
      PostModel.countDocuments().exec(),
    ]);

    res.json({
      data,
      pagination: {
        page,
        limit,
        total,
        pages: Math.max(1, Math.ceil(total / limit)),
      },
    });
  } catch (error) {
    next(error);
  }
}

export async function getPost(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const { id } = req.params;
    let query;
    if (/^\d+$/.test(id)) {
      query = PostModel.findOne({ tg_id: Number(id) });
    } else {
      query = PostModel.findById(id);
    }

    const post = await query.lean().exec();

    if (!post) {
      res.status(404).json({ error: 'Not found' });
      return;
    }

    res.json(post);
  } catch (error) {
    next(error);
  }
}
