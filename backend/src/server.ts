import express from 'express';
import cors from 'cors';
import morgan from 'morgan';

import { env } from './env.js';
import fundraiserRouter from './routes/fundraisers.js';
import { connectMongo, disconnectMongo } from './lib/mongo.js';

const app = express();

app.use(cors());
app.use(express.json({ limit: '1mb' }));
app.use(morgan(env.NODE_ENV === 'production' ? 'combined' : 'dev'));

app.get('/healthz', (_req, res) => res.json({ status: 'ok' }));
app.use('/fundraisers', fundraiserRouter);

async function bootstrap() {
  await connectMongo();
  const server = app.listen(env.PORT, () => {
    console.log(`API listening on http://localhost:${env.PORT}`);
  });

  const shutdown = async () => {
    await disconnectMongo();
    server.close(() => process.exit(0));
  };

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}

bootstrap().catch((error) => {
  console.error('Failed to bootstrap server', error);
  process.exit(1);
});
