from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Match, Resource, Notification, StudentProfile, Skill, Course, Message, Badge

def check_badges(profile):
    badges = Badge.objects.all()
    unlocked = profile.badges.all()
    
    for badge in badges:
        if badge in unlocked:
            continue
            
        awarded = False
        if badge.requirement_type == 'resources':
            if Resource.objects.filter(uploaded_by=profile.user).count() >= badge.requirement_threshold:
                awarded = True
        elif badge.requirement_type == 'matches':
            match_count = Match.objects.filter(student_a=profile).count() + Match.objects.filter(student_b=profile).count()
            if match_count >= badge.requirement_threshold:
                awarded = True
        elif badge.requirement_type == 'messages':
            if Message.objects.filter(sender=profile).count() >= badge.requirement_threshold:
                awarded = True
        elif badge.requirement_type == 'level':
            if profile.current_level >= badge.requirement_threshold:
                awarded = True
                
        if awarded:
            profile.badges.add(badge)
            Notification.objects.create(
                recipient=profile,
                message=f"New Achievement Unlocked: {badge.icon_emoji} {badge.name}!",
                notification_type='general'
            )

def add_xp(profile, amount):
    profile.total_xp += amount
    new_level = (profile.total_xp // 100) + 1
    
    if new_level > profile.current_level:
        profile.current_level = new_level
        Notification.objects.create(
            recipient=profile,
            message=f"🎉 Level Up! You reached Level {new_level}!",
            notification_type='general'
        )
    
    profile.save()
    check_badges(profile)

@receiver(post_save, sender=Match)
def create_match_notification(sender, instance, created, **kwargs):
    """Create notifications and award XP when a match is created/accepted."""
    if created:
        # Notify student A
        Notification.objects.create(
            recipient=instance.student_a,
            message=f"You have a new match with {instance.student_b.user.get_full_name()}!",
            notification_type='match'
        )
        # Notify student B
        Notification.objects.create(
            recipient=instance.student_b,
            message=f"You have a new match with {instance.student_a.user.get_full_name()}!",
            notification_type='match'
        )
        
        # Award XP to both
        add_xp(instance.student_a, 100)
        add_xp(instance.student_b, 100)

@receiver(post_save, sender=Resource)
def award_resource_xp(sender, instance, created, **kwargs):
    """Award XP when a student uploads a resource."""
    if created and instance.uploaded_by:
        try:
            profile = StudentProfile.objects.get(user=instance.uploaded_by)
            add_xp(profile, 50)
        except StudentProfile.DoesNotExist:
            pass

@receiver(post_save, sender=Message)
def award_message_xp(sender, instance, created, **kwargs):
    """Award XP for each collaboration message sent."""
    if created:
        add_xp(instance.sender, 10)

@receiver(m2m_changed, sender=Resource.related_skills.through)
@receiver(m2m_changed, sender=Resource.related_courses.through)
def notify_interested_students(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Notify students when a resource is tagged with skills/courses they have."""
    if action == 'post_add' and not reverse:
        
        interested_students = set()
        
        if model == Skill:
            for skill_id in pk_set:
                try:
                    skill = Skill.objects.get(pk=skill_id)
                    # Find students who have this skill
                    students = StudentProfile.objects.filter(skills=skill)
                    for s in students:
                        interested_students.add(s)
                except Skill.DoesNotExist:
                    pass
                    
        elif model == Course:
            for course_id in pk_set:
                try:
                    course = Course.objects.get(pk=course_id)
                    # Find students who have this course
                    students = StudentProfile.objects.filter(courses=course)
                    for s in students:
                        interested_students.add(s)
                except Course.DoesNotExist:
                    pass
        
        # Create notifications
        count = 0
        for student in interested_students:
            # Don't notify the uploader
            if instance.uploaded_by and student.user == instance.uploaded_by:
                continue
                
            Notification.objects.create(
                recipient=student,
                message=f"New resource available: {instance.title}",
                notification_type='resource'
            )
            count += 1
            if count > 50: 
                break
