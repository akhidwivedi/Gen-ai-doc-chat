from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_services import AIServiceError
from ai_services.rag import answer_question
from documents.models import Document
from documents.services import get_rag_config

from .models import ChatMessage
from .serializers import AskSerializer, ChatMessageSerializer


class DocumentChatView(APIView):
    """
    GET    /api/documents/{id}/chat/   -> chat history for this document
    POST   /api/documents/{id}/chat/   -> ask a question {"question": "..."}
    DELETE /api/documents/{id}/chat/   -> clear chat history

    The document is always looked up with owner=request.user, so another
    user's document id returns 404 (no information leak).
    """

    throttle_scope = "ask"

    def _document(self, request, document_id) -> Document:
        return get_object_or_404(Document, pk=document_id, owner=request.user)

    def get(self, request, document_id):
        doc = self._document(request, document_id)
        msgs = ChatMessage.objects.filter(document=doc, user=request.user)
        return Response(ChatMessageSerializer(msgs, many=True).data)

    def post(self, request, document_id):
        doc = self._document(request, document_id)
        if doc.status != Document.Status.READY:
            return Response(
                {"detail": f"Document is not ready (status: {doc.status})."},
                status=status.HTTP_409_CONFLICT,
            )
        ser = AskSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        question = ser.validated_data["question"]

        # Recent turns of THIS document's conversation give the LLM follow-up context.
        recent = list(
            ChatMessage.objects.filter(document=doc, user=request.user).order_by("-created_at", "-id")[
                : settings.RAG_HISTORY_TURNS * 2
            ]
        )[::-1]
        history = [{"role": m.role, "content": m.content} for m in recent]

        try:
            result = answer_question(
                get_rag_config(),
                user_id=request.user.id,
                document_id=doc.id,
                question=question,
                history=history,
            )
        except AIServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        user_msg = ChatMessage.objects.create(
            document=doc, user=request.user, role=ChatMessage.Role.USER, content=question
        )
        bot_msg = ChatMessage.objects.create(
            document=doc,
            user=request.user,
            role=ChatMessage.Role.ASSISTANT,
            content=result["answer"],
            sources=result["sources"],
        )
        return Response(
            {
                "user_message": ChatMessageSerializer(user_msg).data,
                "assistant_message": ChatMessageSerializer(bot_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, document_id):
        doc = self._document(request, document_id)
        ChatMessage.objects.filter(document=doc, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
