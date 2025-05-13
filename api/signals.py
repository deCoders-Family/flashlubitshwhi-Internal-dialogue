# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from django.core.cache import cache

# from .models import Avatar


# @receiver([post_save, post_delete], sender=Avatar)
# def invalid_product_cache(sender, instance, **kwargs):
#     cache.delete_pattern("*avatar_list_cache*")
