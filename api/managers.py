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

