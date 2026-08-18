from django.contrib import admin
from predictor.models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "study_hours",
        "attendance",
        "previous_marks",
        "assignments",
        "predicted_marks",
        "created_at",
    )