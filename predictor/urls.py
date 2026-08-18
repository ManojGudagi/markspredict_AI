from django.urls import path
from predictor.views import (
    PredictMarksView,
    PredictionHistoryView,
    PredictionAnalyticsView,
    RegisterView,
    ModelEvaluationView,
    ActualPredictedView,
    ModelComparisonView,
)


urlpatterns = [
    path("predict/", PredictMarksView.as_view(), name="predict"),

    path("predictions/", PredictionHistoryView.as_view(), name="prediction-history"),

    path("analytics/", PredictionAnalyticsView.as_view(), name="prediction-analytics"),

    path("register/", RegisterView.as_view(), name="register"),

    path("model-evaluation/", ModelEvaluationView.as_view(), name="model-evaluation"),

    path("actual-vs-predicted/", ActualPredictedView.as_view(), name="actual-vs-predicted"),

    path("model-comparison/", ModelComparisonView.as_view(), name="model-comparison"),
]


