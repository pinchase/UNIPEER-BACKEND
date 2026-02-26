import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unipeer.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import StudentProfile, Match, CollaborationRoom, Message, Notification

def cleanup():
    print("Starting data cleanup...")
    
    # Delete related models first
    print(f"Deleting {Message.objects.count()} messages...")
    Message.objects.all().delete()
    
    print(f"Deleting {CollaborationRoom.objects.count()} collaboration rooms...")
    CollaborationRoom.objects.all().delete()
    
    print(f"Deleting {Match.objects.count()} matches...")
    Match.objects.all().delete()
    
    print(f"Deleting {Notification.objects.count()} notifications...")
    Notification.objects.all().delete()
    
    print(f"Deleting {StudentProfile.objects.count()} student profiles...")
    StudentProfile.objects.all().delete()
    
    # Delete non-superuser accounts
    non_admins = User.objects.filter(is_superuser=False)
    count = non_admins.count()
    print(f"Deleting {count} non-admin user accounts...")
    non_admins.delete()
    
    print("Cleanup complete! ✨")

if __name__ == "__main__":
    cleanup()
