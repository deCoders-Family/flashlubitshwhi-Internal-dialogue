from django.contrib.auth.models import BaseUserManager
from django.db.models import Manager

from .choices import StatusChoices, SenderTypeChoices


class StatusManager(Manager):
    def IS_ACTIVE(self):
        return self.filter(status=StatusChoices.ACTIVE)

    def IS_INACTIVE(self):
        return self.filter(status=StatusChoices.INACTIVE)

    def IS_REMOVED(self):
        return self.filter(status=StatusChoices.REMOVED)


class SenderTypeManager(Manager):
    def IS_USER(self):
        return self.filter(sender_type=SenderTypeChoices.USER)

    def IS_AI(self):
        return self.filter(sender_type=SenderTypeChoices.AI)


class UserManager(BaseUserManager, StatusManager):
    def create_user(self, email, password=None, password2=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", email, password, extra_fields)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def IS_ACTIVE(self):
        return super().IS_ACTIVE()

    def IS_INACTIVE(self):
        return super().IS_INACTIVE()

    def IS_REMOVED(self):
        return super().IS_REMOVED()


class GeneratedAudioManager(StatusManager):
    def IS_ACTIVE(self):
        return super().IS_ACTIVE()

    def IS_INACTIVE(self):
        return super().IS_INACTIVE()

    def IS_REMOVED(self):
        return super().IS_REMOVED()


class ChatHistoryManager(StatusManager):
    def IS_ACTIVE(self):
        return super().IS_ACTIVE()

    def IS_INACTIVE(self):
        return super().IS_INACTIVE()

    def IS_REMOVED(self):
        return super().IS_REMOVED()


class AvatarManager(StatusManager):
    def IS_ACTIVE(self):
        return super().IS_ACTIVE()

    def IS_INACTIVE(self):
        return super().IS_INACTIVE()

    def IS_REMOVED(self):
        return super().IS_REMOVED()


class MoodManager(StatusManager):
    def IS_ACTIVE(self):
        return super().IS_ACTIVE()

    def IS_INACTIVE(self):
        return super().IS_INACTIVE()

    def IS_REMOVED(self):
        return super().IS_REMOVED()
