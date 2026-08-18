from django.db import models
from django.contrib.auth.models import User


class Prediction(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="predictions"
    )

    study_hours = models.FloatField()
    attendance = models.FloatField()
    previous_marks = models.FloatField()
    assignments = models.IntegerField()
    predicted_marks = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.predicted_marks}"