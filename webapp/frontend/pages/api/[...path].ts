/** Proxy all /api/* to backend. Runs server-side, avoids CORS. */
import type { NextApiRequest, NextApiResponse } from 'next';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const GENERATE_TIMEOUT_MS = 86400000;  // 24 hours (no solver time limit)

async function readBody(req: NextApiRequest): Promise<Buffer | null> {
  return new Promise((resolve) => {
    const chunks: Buffer[] = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(chunks.length ? Buffer.concat(chunks) : null));
    req.on('error', () => resolve(null));
  });
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const path = (req.query.path as string[]) || [];
  const pathStr = path.filter(Boolean).join('/');
  const qs = req.url?.includes('?') ? req.url.split('?')[1] : '';
  let url = `${BACKEND}/api/${pathStr}`;
  if (qs) url += `?${qs}`;
  else if (path.length <= 1) url += '/';  // avoid 307 redirect for POST /api/completions

  try {
    const headers: Record<string, string> = {};
    const skip = ['host', 'connection', 'content-length'];
    for (const [k, v] of Object.entries(req.headers)) {
      if (v && !skip.includes(k.toLowerCase())) {
        headers[k] = Array.isArray(v) ? v[0] : v;
      }
    }
    delete headers['host'];

    const init: RequestInit = { method: req.method, headers };
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      const body = await readBody(req);
      if (body && body.length > 0) init.body = body as any;
    }

    // Schedule generate can take several minutes; use longer timeout
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    const isGenerate = path[0] === 'schedule' && path[1] === 'generate' && req.method === 'POST';
    if (isGenerate) {
      const controller = new AbortController();
      timeoutId = setTimeout(() => controller.abort(), GENERATE_TIMEOUT_MS);
      (init as RequestInit & { signal?: AbortSignal }).signal = controller.signal;
    }
    const backendRes = await fetch(url, init);
    if (timeoutId) clearTimeout(timeoutId);

    // Stream the response back to client (supports binary/Excel)
    const arrayBuffer = await backendRes.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    res.status(backendRes.status);
    backendRes.headers.forEach((v, k) => {
      // Forward all headers except content-encoding/transfer-encoding
      if (!['content-encoding', 'transfer-encoding'].includes(k.toLowerCase())) {
        res.setHeader(k, v);
      }
    });
    res.send(buffer);
  } catch (e: any) {
    res.status(502).json({ detail: e.message || 'Backend unreachable' });
  }
}

export const config = {
  api: { bodyParser: false, responseLimit: '10mb' },
};
