from django.core.management.base import BaseCommand
from api.models import Badge

class Command(BaseCommand):
    help = 'Seed initial badges for UniPeer'

    def handle(self, *args, **options):
        badges = [
            {
                'name': 'Resource Guru',
                'description': 'Upload 5 academic resources.',
                'icon_emoji': '📚',
                'requirement_type': 'resources',
                'requirement_threshold': 5
            },
            {
                'name': 'Social Butterfly',
                'description': 'Create 3 successful study matches.',
                'icon_emoji': '🤝',
                'requirement_type': 'matches',
                'requirement_threshold': 3
            },
            {
                'name': 'Deep Thinker',
                'description': 'Reach Level 5.',
                'icon_emoji': '🧠',
                'requirement_type': 'level',
                'requirement_threshold': 5
            },
            {
                'name': 'Chatty Scholar',
                'description': 'Send 20 collaboration messages.',
                'icon_emoji': '💬',
                'requirement_type': 'messages',
                'requirement_threshold': 20
            }
        ]

        for b_data in badges:
            badge, created = Badge.objects.get_or_create(
                name=b_data['name'],
                defaults=b_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created badge: {badge.name}'))
            else:
                self.stdout.write(f'Badge already exists: {badge.name}')
