from django.conf import settings
from django.db import models

from documents.models import Document


class ChatMessage(models.Model):
    """One message in the chat history of a single document (per user)."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["document", "user", "created_at"])]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"
