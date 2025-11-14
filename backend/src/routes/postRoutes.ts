import { Router, type Request, type Response, type NextFunction } from 'express';
import { importPosts, listPosts, getPost } from '../controllers/postController.js';
import { env } from '../utils/env.js';

const router = Router();

function verifyToken(req: Request, res: Response, next: NextFunction): void {
  if (!env.INGEST_TOKEN) {
    next();
    return;
  }

  const token = req.header('x-ingestion-key');
  if (token !== env.INGEST_TOKEN) {
    res.status(401).json({ error: 'Invalid ingestion token' });
    return;
  }
  next();
}

router.get('/', listPosts);
router.get('/:id', getPost);
router.post('/import', verifyToken, importPosts);

export const postRoutes = router;
