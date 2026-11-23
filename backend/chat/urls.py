from django.urls import path

from .views import DocumentChatView

urlpatterns = [
    path("<uuid:document_id>/chat/", DocumentChatView.as_view(), name="document-chat"),
]
