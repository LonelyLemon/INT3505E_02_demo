import requests
import threading
import logging
from app.core.repositories import WebhookRepository

logger = logging.getLogger(__name__)

class EventManager:
    def __init__(self):
        self.webhook_repo = WebhookRepository()

    def notify(self, event_type, payload):
        subscribers = self.webhook_repo.get_by_event(event_type)
        
        thread = threading.Thread(target=self._send_webhooks, args=(subscribers, payload))
        thread.start()

    def _send_webhooks(self, subscribers, payload):
        for sub in subscribers:
            try:
                logger.info(f"Triggering webhook to {sub.url}")
                requests.post(sub.url, json=payload, timeout=5)
            except Exception as e:
                logger.error(f"Failed to send webhook to {sub.url}: {e}")