from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(
    sender, instance: User, created: bool, **kwargs
) -> None:
    if created:
        # Create UserProfile with default security settings
        UserProfile.objects.create(
            user=instance,
            show_email=False,  # Default to not showing email publicly
            show_profile=True,  # Default to showing profile
            data_processing_consent=False,  # Default to no data processing consent
            marketing_consent=False,  # Default to no marketing consent
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance: User, **kwargs) -> None:
    # Save the user profile with security considerations
    if hasattr(instance, 'profile'):
        instance.profile.save()
