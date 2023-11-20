import random
import datetime
from django.db.models import signals
from django.dispatch import receiver
from django.db import models


def generate_token():
    token = ''
    for _ in range(16):
        if random.randint(0, 3):
            if random.randint(0, 1):
                token += random.choice('abcdefghigklmnopqrstuvwxyz')
            else:
                token += random.choice('abcdefghigklmnopqrstuvwxyz').upper()
        else:
            token += str(random.randint(0, 9))
    now = datetime.datetime.now()
    token += str(now).replace('-', '').replace(' ', '').replace('.', '').replace(':', '')
    return token


class Token(models.Model):
    token = models.TextField(null=True)
    duration = models.IntegerField(null=False)
    created_at = models.DateTimeField(null=True)


@receiver(signals.post_save, sender=Token)
def create_company(sender, instance, created, **kwargs):
    if created:
        token = instance
        token.token = generate_token()
        token.created_at = datetime.datetime.now()
        token.save()
