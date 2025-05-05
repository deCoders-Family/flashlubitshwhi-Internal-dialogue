from django.db.models import TextChoices


class StatusChoices(TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    REMOVED = "REMOVED", "Removed"
    
    
class SenderTypeChoices(TextChoices):
    USER = "USER", "User"
    AI = "AI", "AI"

