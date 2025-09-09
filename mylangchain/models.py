from django.db import models

class ChatHistory(models.Model):
    session_id = models.CharField(max_length=255)
    role = models.CharField(max_length=50)  # "user" atau "ai"
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.session_id} - {self.role}: {self.message[:50]}"
    

