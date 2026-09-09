const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store"
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: jsonHeaders });
}

function shanghaiDay() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date());
}

async function hashVisitor(visitorId) {
  const bytes = new TextEncoder().encode(visitorId);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function readStats(db, day) {
  const [visitors, views, today] = await db.batch([
    db.prepare("SELECT COUNT(*) AS value FROM visitors"),
    db.prepare("SELECT value FROM counters WHERE key = 'views'"),
    db.prepare("SELECT value FROM daily_views WHERE day = ?").bind(day)
  ]);
  return {
    visitors: Number(visitors.results[0]?.value || 0),
    views: Number(views.results[0]?.value || 0),
    today: Number(today.results[0]?.value || 0)
  };
}

export async function onRequestGet(context) {
  if (!context.env.VISITS_DB) {
    return json({ error: "statistics unavailable" }, 503);
  }
  try {
    return json(await readStats(context.env.VISITS_DB, shanghaiDay()));
  } catch {
    return json({ error: "statistics unavailable" }, 503);
  }
}

export async function onRequestPost(context) {
  const db = context.env.VISITS_DB;
  if (!db) {
    return json({ error: "statistics unavailable" }, 503);
  }

  const origin = context.request.headers.get("origin");
  if (origin && origin !== new URL(context.request.url).origin) {
    return json({ error: "origin rejected" }, 403);
  }

  let body;
  try {
    body = await context.request.json();
  } catch {
    return json({ error: "invalid request" }, 400);
  }

  const visitorId = typeof body.visitorId === "string" ? body.visitorId.trim() : "";
  const path = typeof body.path === "string" ? body.path.slice(0, 160) : "/";
  if (!/^[A-Za-z0-9-]{12,80}$/.test(visitorId) || !path.startsWith("/")) {
    return json({ error: "invalid request" }, 400);
  }

  const now = new Date().toISOString();
  const day = shanghaiDay();
  const visitorHash = await hashVisitor(visitorId);

  try {
    await db.batch([
      db.prepare(
        "INSERT OR IGNORE INTO visitors (id, first_seen, last_seen) VALUES (?, ?, ?)"
      ).bind(visitorHash, now, now),
      db.prepare("UPDATE visitors SET last_seen = ? WHERE id = ?").bind(now, visitorHash),
      db.prepare(
        "INSERT INTO counters (key, value) VALUES ('views', 1) " +
        "ON CONFLICT(key) DO UPDATE SET value = value + 1"
      ),
      db.prepare(
        "INSERT INTO daily_views (day, value) VALUES (?, 1) " +
        "ON CONFLICT(day) DO UPDATE SET value = value + 1"
      ).bind(day)
    ]);
    return json(await readStats(db, day));
  } catch {
    return json({ error: "statistics unavailable" }, 503);
  }
}
