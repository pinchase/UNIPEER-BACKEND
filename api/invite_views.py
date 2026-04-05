from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models

from .models import MatchInvite
from .invite_serializers import MatchInviteSerializer


class InviteViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = MatchInvite.objects.all().select_related('sender__user', 'recipient__user', 'related_match')
    serializer_class = MatchInviteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        view = self.request.query_params.get('view')
        profile = getattr(self.request.user, 'profile', None)
        if not profile:
            return qs.none()
        if view == 'sent':
            return qs.filter(sender=profile)
        if view == 'received':
            return qs.filter(recipient=profile)
        return qs.filter(models.Q(sender=profile) | models.Q(recipient=profile))

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        invite = self.get_object()
        profile = getattr(request.user, 'profile', None)
        if invite.recipient != profile:
            return Response({'error': 'Only the recipient can accept this invite.'}, status=403)
        invite.accept(actor=profile)
        return Response(self.get_serializer(invite).data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        invite = self.get_object()
        profile = getattr(request.user, 'profile', None)
        if invite.recipient != profile:
            return Response({'error': 'Only the recipient can decline this invite.'}, status=403)
        invite.decline(actor=profile)
        return Response(self.get_serializer(invite).data)
