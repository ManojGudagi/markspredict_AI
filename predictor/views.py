import os
import joblib

from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from predictor.models import Prediction
from predictor.serializers import (
    PredictionSerializer,
    RegisterSerializer
)
from predictor.recommendations import generate_recommendations


from drf_yasg.utils import swagger_auto_schema


# =========================================================
# LOAD ML MODEL
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

model = joblib.load(
    os.path.join(
        BASE_DIR,
        "ml",
        "model.pkl"
    )
)


# =========================================================
# PREDICT MARKS
# =========================================================

class PredictMarksView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=PredictionSerializer,
        responses={
            201: PredictionSerializer,
            400: "Invalid data",
            401: "Authentication credentials were not provided.",
        },
    )
    def post(self, request):

        serializer = PredictionSerializer(
            data=request.data
        )

        # Validate input
        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


        data = serializer.validated_data


        # =================================================
        # ML PREDICTION
        # =================================================

        prediction = model.predict(
            [
                [
                    data["study_hours"],
                    data["attendance"],
                    data["previous_marks"],
                    data["assignments"],
                ]
            ]
        )


        raw_predicted = float(prediction[0])
        clipped_predicted = max(0.0, min(100.0, raw_predicted))

        predicted_marks = round(
            clipped_predicted,
            2
        )



        recommendation_data = generate_recommendations(
            study_hours=data["study_hours"],
            attendance=data["attendance"],
            previous_marks=data["previous_marks"],
            predicted_marks=predicted_marks
        )


        # =================================================
        # SAVE PREDICTION
        # =================================================

        prediction_obj = Prediction.objects.create(

            user=request.user,

            study_hours=data["study_hours"],

            attendance=data["attendance"],

            previous_marks=data["previous_marks"],

            assignments=data["assignments"],

            predicted_marks=predicted_marks,

        )


        # =================================================
        # RESPONSE
        # =================================================

        response_serializer = PredictionSerializer(
            prediction_obj
        )


        return Response(
            {
                "prediction":
                    response_serializer.data,

                "performance":
                    recommendation_data["performance"],

                "recommendations":
                    recommendation_data["recommendations"]
            },
            status=status.HTTP_201_CREATED
        )



# =========================================================
# PREDICTION HISTORY
# =========================================================

class PredictionHistoryView(APIView):

    permission_classes = [IsAuthenticated]


    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: PredictionSerializer(many=True),
            401: "Authentication credentials were not provided.",
        },
    )
    def get(self, request):

        # =================================================
        # GET CURRENT USER PREDICTIONS
        # =================================================

        predictions = Prediction.objects.filter(
            user=request.user
        ).order_by(
            "-created_at"
        )


        # =================================================
        # FILTER BY MINIMUM PREDICTED MARKS
        # =================================================

        min_marks = request.query_params.get(
            "min_marks"
        )


        if min_marks:

            try:

                predictions = predictions.filter(
                    predicted_marks__gte=float(
                        min_marks
                    )
                )

            except ValueError:

                return Response(
                    {
                        "error":
                        "min_marks must be a valid number."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


        # =================================================
        # FILTER BY MINIMUM ATTENDANCE
        # =================================================

        min_attendance = request.query_params.get(
            "min_attendance"
        )


        if min_attendance:

            try:

                predictions = predictions.filter(
                    attendance__gte=float(
                        min_attendance
                    )
                )

            except ValueError:

                return Response(
                    {
                        "error":
                        "min_attendance must be a valid number."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


        # =================================================
        # FILTER BY MINIMUM STUDY HOURS
        # =================================================

        min_study_hours = request.query_params.get(
            "min_study_hours"
        )


        if min_study_hours:

            try:

                predictions = predictions.filter(
                    study_hours__gte=float(
                        min_study_hours
                    )
                )

            except ValueError:

                return Response(
                    {
                        "error":
                        "min_study_hours must be a valid number."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


        # =================================================
        # PAGINATION
        # =================================================

        paginator = PageNumberPagination()

        paginator.page_size = 5


        result_page = paginator.paginate_queryset(
            predictions,
            request
        )


        # =================================================
        # SERIALIZE
        # =================================================

        serializer = PredictionSerializer(
            result_page,
            many=True
        )


        # =================================================
        # PAGINATED RESPONSE
        # =================================================

        return paginator.get_paginated_response(
            serializer.data
        )


# =========================================================
# USER REGISTRATION
# =========================================================

class RegisterView(APIView):

    permission_classes = []

    @swagger_auto_schema(auto_schema=None)
    def post(self, request):



        serializer = RegisterSerializer(
            data=request.data
        )


        # =================================================
        # VALIDATE REGISTRATION
        # =================================================

        if serializer.is_valid():

            user = serializer.save()


            # =================================================
            # GENERATE JWT TOKENS
            # =================================================

            refresh = RefreshToken.for_user(
                user
            )


            return Response(
                {

                    "message":
                        "User registered successfully.",

                    "username":
                        user.username,

                    "email":
                        user.email,

                    "tokens":
                        {

                            "refresh":
                                str(refresh),

                            "access":
                                str(
                                    refresh.access_token
                                )

                        }

                },
                status=status.HTTP_201_CREATED
            )


        # =================================================
        # REGISTRATION ERROR
        # =================================================

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# PREDICTION ANALYTICS
# =========================================================

class PredictionAnalyticsView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={
            200: "Analytics metrics, performance categories, charts, and recommendations.",
            401: "Authentication credentials were not provided.",
        },
    )
    def get(self, request):

        predictions = Prediction.objects.filter(
            user=request.user
        ).order_by("created_at")

        total_predictions = predictions.count()

        if total_predictions == 0:
            return Response(
                {
                    "total_predictions": 0,
                    "average_predicted_marks": 0,
                    "highest_predicted_marks": 0,
                    "lowest_predicted_marks": 0,
                    "latest_prediction": None,
                    "category_counts": {
                        "excellent": 0,
                        "good": 0,
                        "needs_improvement": 0,
                    },
                    "category_percentages": {
                        "excellent": 0,
                        "good": 0,
                        "needs_improvement": 0,
                    },
                    "study_hours_vs_marks": [],
                    "attendance_vs_marks": [],
                },
                status=status.HTTP_200_OK,
            )

        marks_list = [p.predicted_marks for p in predictions]
        average_marks = round(sum(marks_list) / total_predictions, 2)
        highest_marks = round(max(marks_list), 2)
        lowest_marks = round(min(marks_list), 2)

        excellent_count = 0
        good_count = 0
        needs_improvement_count = 0

        study_hours_vs_marks = []
        attendance_vs_marks = []

        for p in predictions:
            if p.predicted_marks >= 80:
                excellent_count += 1
            elif p.predicted_marks >= 60:
                good_count += 1
            else:
                needs_improvement_count += 1

            study_hours_vs_marks.append(
                {
                    "study_hours": p.study_hours,
                    "predicted_marks": p.predicted_marks,
                    "created_at": p.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

            attendance_vs_marks.append(
                {
                    "attendance": p.attendance,
                    "predicted_marks": p.predicted_marks,
                    "created_at": p.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        latest_prediction_obj = predictions.last()
        latest_prediction_data = (
            PredictionSerializer(latest_prediction_obj).data
            if latest_prediction_obj
            else None
        )

        return Response(
            {
                "total_predictions": total_predictions,
                "average_predicted_marks": average_marks,
                "highest_predicted_marks": highest_marks,
                "lowest_predicted_marks": lowest_marks,
                "latest_prediction": latest_prediction_data,
                "category_counts": {
                    "excellent": excellent_count,
                    "good": good_count,
                    "needs_improvement": needs_improvement_count,
                },
                "category_percentages": {
                    "excellent": round(
                        (excellent_count / total_predictions) * 100, 1
                    ),
                    "good": round(
                        (good_count / total_predictions) * 100, 1
                    ),
                    "needs_improvement": round(
                        (needs_improvement_count / total_predictions) * 100, 1
                    ),
                },
                "study_hours_vs_marks": study_hours_vs_marks,
                "attendance_vs_marks": attendance_vs_marks,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# MODEL EVALUATION API
# =========================================================

class ModelEvaluationView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}]
    )
    def get(self, request):

        metrics_path = os.path.join(
            BASE_DIR,
            "ml",
            "metrics.pkl"
        )

        if not os.path.exists(
            metrics_path
        ):
            return Response(
                {
                    "error":
                    "Model evaluation metrics not found. "
                    "Run ml/train.py first."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        metrics = joblib.load(
            metrics_path
        )

        return Response(
            {
                "model": "Linear Regression",

                "metrics": {

                    "MAE":
                        metrics["mae"],

                    "MSE":
                        metrics["mse"],

                    "RMSE":
                        metrics["rmse"],

                    "R2 Score":
                        metrics["r2_score"]

                }
            },
            status=status.HTTP_200_OK
        )


# =========================================================
# ACTUAL VS PREDICTED API
# =========================================================

class ActualPredictedView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}]
    )
    def get(self, request):

        evaluation_data_path = os.path.join(
            BASE_DIR,
            "ml",
            "evaluation_data.pkl"
        )

        if not os.path.exists(
            evaluation_data_path
        ):
            return Response(
                {
                    "error":
                    "Evaluation data not found. "
                    "Run ml/train.py first."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        evaluation_data = joblib.load(
            evaluation_data_path
        )

        return Response(
            {
                "actual": evaluation_data["actual"],
                "predicted": evaluation_data["predicted"],
            },
            status=status.HTTP_200_OK
        )


# =========================================================
# MODEL COMPARISON API
# =========================================================

class ModelComparisonView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}]
    )
    def get(self, request):

        comparison_path = os.path.join(
            BASE_DIR,
            "ml",
            "model_comparison.pkl"
        )

        if not os.path.exists(
            comparison_path
        ):
            return Response(
                {
                    "error":
                    "Model comparison data not found. "
                    "Run ml/train.py first."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        comparison_data = joblib.load(
            comparison_path
        )

        return Response(
            {
                "best_model":
                    comparison_data[
                        "best_model"
                    ],

                "models":
                    comparison_data[
                        "models"
                    ]
            },
            status=status.HTTP_200_OK
        )


