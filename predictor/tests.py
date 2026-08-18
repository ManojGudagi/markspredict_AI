from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from predictor.models import Prediction
from predictor.serializers import (
    calculate_performance_category,
    generate_improvement_suggestions,
    PredictionSerializer,
)


class PredictionAnalyticsTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="teststudent",
            email="teststudent@example.com",
            password="Password123!",
        )
        self.client.force_authenticate(user=self.user)

    def test_category_calculation(self):
        self.assertEqual(calculate_performance_category(92.5), "Excellent")
        self.assertEqual(calculate_performance_category(80.0), "Excellent")
        self.assertEqual(calculate_performance_category(79.9), "Good")
        self.assertEqual(calculate_performance_category(60.0), "Good")
        self.assertEqual(calculate_performance_category(59.9), "Needs Improvement")
        self.assertEqual(calculate_performance_category(42.0), "Needs Improvement")

    def test_improvement_suggestions_low_inputs(self):
        suggestions = generate_improvement_suggestions(
            study_hours=3.0,
            attendance=65.0,
            previous_marks=55.0,
            assignments=5,
            predicted_marks=52.0,
        )
        self.assertTrue(any("attendance is low" in s for s in suggestions))
        self.assertTrue(any("Study duration" in s for s in suggestions))
        self.assertTrue(any("Assignment completion" in s for s in suggestions))
        self.assertTrue(any("Prior academic mark" in s for s in suggestions))

    def test_improvement_suggestions_high_inputs(self):
        suggestions = generate_improvement_suggestions(
            study_hours=8.0,
            attendance=95.0,
            previous_marks=88.0,
            assignments=10,
            predicted_marks=91.0,
        )
        self.assertTrue(any("Outstanding study habits" in s for s in suggestions))

    def test_analytics_unauthenticated(self):
        self.client.logout()
        response = self.client.get("/api/analytics/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_analytics_empty_predictions(self):
        response = self.client.get("/api/analytics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["total_predictions"], 0)
        self.assertEqual(data["average_predicted_marks"], 0)
        self.assertEqual(data["highest_predicted_marks"], 0)
        self.assertEqual(data["lowest_predicted_marks"], 0)

    def test_analytics_with_predictions(self):
        Prediction.objects.create(
            user=self.user,
            study_hours=4.0,
            attendance=70.0,
            previous_marks=50.0,
            assignments=6,
            predicted_marks=55.0,
        )
        Prediction.objects.create(
            user=self.user,
            study_hours=6.0,
            attendance=80.0,
            previous_marks=70.0,
            assignments=8,
            predicted_marks=72.0,
        )
        Prediction.objects.create(
            user=self.user,
            study_hours=9.0,
            attendance=95.0,
            previous_marks=90.0,
            assignments=10,
            predicted_marks=90.0,
        )

        response = self.client.get("/api/analytics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["total_predictions"], 3)
        self.assertEqual(data["average_predicted_marks"], 72.33)
        self.assertEqual(data["highest_predicted_marks"], 90.0)
        self.assertEqual(data["lowest_predicted_marks"], 55.0)

        self.assertEqual(data["category_counts"]["excellent"], 1)
        self.assertEqual(data["category_counts"]["good"], 1)
        self.assertEqual(data["category_counts"]["needs_improvement"], 1)

        self.assertEqual(len(data["study_hours_vs_marks"]), 3)
        self.assertEqual(len(data["attendance_vs_marks"]), 3)
        self.assertIsNotNone(data["latest_prediction"])
        self.assertEqual(data["latest_prediction"]["performance_category"], "Excellent")

    def test_predict_marks_endpoint_recommendations(self):
        response = self.client.post(
            "/api/predict/",
            {
                "study_hours": 4.0,
                "attendance": 65.0,
                "previous_marks": 72.0,
                "assignments": 7,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("prediction", data)
        self.assertIn("performance", data)
        self.assertIn("recommendations", data)
        self.assertIsInstance(data["recommendations"], list)
        self.assertGreater(len(data["recommendations"]), 0)

    def test_predict_marks_bounded_to_100(self):
        response = self.client.post(
            "/api/predict/",
            {
                "study_hours": 24.0,
                "attendance": 100.0,
                "previous_marks": 100.0,
                "assignments": 10,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        predicted_marks = data["prediction"]["predicted_marks"]
        self.assertLessEqual(predicted_marks, 100.0)
        self.assertGreaterEqual(predicted_marks, 0.0)


    def test_model_evaluation_endpoint(self):
        response = self.client.get("/api/model-evaluation/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["model"], "Linear Regression")
        self.assertIn("metrics", data)
        self.assertIn("MAE", data["metrics"])
        self.assertIn("MSE", data["metrics"])
        self.assertIn("RMSE", data["metrics"])
        self.assertIn("R2 Score", data["metrics"])

    def test_actual_vs_predicted_endpoint(self):
        response = self.client.get("/api/actual-vs-predicted/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("actual", data)
        self.assertIn("predicted", data)
        self.assertIsInstance(data["actual"], list)
        self.assertIsInstance(data["predicted"], list)

    def test_model_comparison_endpoint(self):
        response = self.client.get("/api/model-comparison/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("best_model", data)
        self.assertIn("models", data)
        self.assertIn("Linear Regression", data["models"])
        self.assertIn("Random Forest", data["models"])





