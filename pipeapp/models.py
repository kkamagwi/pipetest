from django.db import models
from django.shortcuts import reverse


class TodoItems(models.Model):
    text = models.TextField()
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_delete_url(self):
        return reverse('delete', kwargs={'id': self.id})

    def __str__(self):
        return self.text