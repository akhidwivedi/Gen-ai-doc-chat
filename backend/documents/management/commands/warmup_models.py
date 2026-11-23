from django.conf import settings
from django.core.management.base import BaseCommand

from ai_services.embeddings import get_model


class Command(BaseCommand):
    help = "Download/load the sentence-transformers embedding model so the first upload is fast."

    def handle(self, *args, **options):
        self.stdout.write(f"Loading {settings.EMBEDDING_MODEL} ...")
        get_model(settings.EMBEDDING_MODEL)
        self.stdout.write(self.style.SUCCESS("Embedding model ready."))
