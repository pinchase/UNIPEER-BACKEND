from rest_framework import serializers
from .serializers import StudentProfileSerializer
from .models import MatchInvite, StudentProfile, Match



class MatchInviteSerializer(serializers.ModelSerializer):
    sender = StudentProfileSerializer(read_only=True)
    recipient_id = serializers.IntegerField(write_only=True)
    recipient = StudentProfileSerializer(read_only=True)

    class Meta:
        model = MatchInvite
        fields = [
            'id', 'sender', 'recipient', 'recipient_id', 'message',
            'status', 'created_at', 'responded_at', 'related_match',
        ]
        read_only_fields = ['id', 'sender', 'recipient', 'status', 'created_at', 'responded_at']

    def validate_recipient_id(self, value):
        request = self.context.get('request')
        profile = getattr(getattr(request, 'user', None), 'profile', None)

        if profile and profile.id == value:
            raise serializers.ValidationError('Cannot invite yourself')

        if not StudentProfile.objects.filter(id=value).exists():
            raise serializers.ValidationError('Recipient not found')

        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError('Authentication required')
        profile = getattr(request.user, 'profile', None)
        if not profile:
            raise serializers.ValidationError('User profile not found')
        recipient_id = validated_data.pop('recipient_id')

        recipient = StudentProfile.objects.get(id=recipient_id)
        student_a, student_b = sorted([profile.id, recipient.id])
        if Match.objects.filter(student_a_id=student_a, student_b_id=student_b, status='accepted').exists():
            raise serializers.ValidationError('You are already matched with this student')
        if MatchInvite.objects.filter(
            sender=profile,
            recipient=recipient,
            status=MatchInvite.STATUS_PENDING,
        ).exists():
            raise serializers.ValidationError('You already sent a pending invite to this student')

        invite = MatchInvite.objects.create(sender=profile, recipient=recipient, **validated_data)
        return invite
