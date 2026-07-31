"""Shopping-list Discord notification task.

Event-driven: fired by inventory changes (capture processed, count overridden).
Posts to the configured Discord webhook ONLY when items are below par.
No scheduler, no cron — pantry reacts to its own state.
"""
import json
import os
import urllib.request

from app.log_config import setup_logging
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.shopping import recompute_shopping_list, get_unresolved_items

logger = setup_logging("pantry-notify")

WEBHOOK_URL = os.getenv("PANTRY_DISCORD_WEBHOOK", "").strip()


def _post_webhook(payload: dict) -> bool:
    """Post a JSON payload to the Discord webhook. Returns True on 2xx."""
    if not WEBHOOK_URL:
        logger.warning("PANTRY_DISCORD_WEBHOOK not set — skipping notification")
        return False
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) pantry-notify/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            logger.info("Webhook posted", extra={"status": r.status})
            return 200 <= r.status < 300
    except Exception as e:
        logger.error("Webhook post failed", extra={"error": str(e)})
        return False


@celery_app.task(bind=True, base=celery_app.Task, max_retries=3)
def notify_shopping_list(self) -> dict:
    """Recompute the shopping list; notify Discord if anything is below par."""
    db = SessionLocal()
    try:
        updated = recompute_shopping_list(db)
        items = get_unresolved_items(db)

        if not items:
            logger.info("Shopping list empty — nothing below par, no notification")
            return {"status": "ok", "below_par": 0, "notified": False}

        lines = [
            f"• **{i['item_name']}** ×{i['needed']}  `{i.get('location') or 'unassigned'}`"
            for i in items
        ]
        payload = {
            "content": (
                f"🛒 **Pantry shopping list** — {len(items)} item(s) below par\n\n"
                + "\n".join(lines)
            )
        }
        notified = _post_webhook(payload)
        logger.info("Shopping list notify complete", extra={
            "below_par": len(items),
            "recomputed": updated,
            "notified": notified,
        })
        return {"status": "ok", "below_par": len(items), "notified": notified}
    except Exception as exc:
        logger.exception("notify_shopping_list failed", extra={"error": str(exc)})
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries, 60))
    finally:
        db.close()
