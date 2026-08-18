from rest_framework import serializers
from predictor.models import Prediction
from django.contrib.auth.models import User


def calculate_performance_category(predicted_marks):
    if predicted_marks >= 80:
        return "Excellent"
    elif predicted_marks >= 60:
        return "Good"
    else:
        return "Needs Improvement"


def generate_improvement_suggestions(study_hours, attendance, previous_marks, assignments, predicted_marks):
    suggestions = []
    category = calculate_performance_category(predicted_marks)

    if attendance < 75:
        suggestions.append(
            f"Class attendance is low ({attendance}%). Aim for at least 75% to 85% attendance to improve score."
        )
    if study_hours < 5:
        suggestions.append(
            f"Study duration ({study_hours} hrs) is below recommended levels. Target 5-8 study hours per week."
        )
    if assignments < 7:
        suggestions.append(
            f"Assignment completion ({assignments} submitted) is on the lower side. Complete all coursework assignments."
        )
    if previous_marks < 60:
        suggestions.append(
            f"Prior academic mark ({previous_marks}) indicates foundation gaps. Dedicate extra time to core topic revision."
        )

    if not suggestions:
        if category == "Excellent":
            suggestions.append(
                "Outstanding study habits! Continue maintaining your high attendance and regular study routine."
            )
        elif category == "Good":
            suggestions.append(
                "Solid overall routine. Slightly increasing study time or assignment focus will push marks into Excellent (≥80)."
            )
        else:
            suggestions.append(
                "Focus on increasing study hours and attendance to boost overall predicted marks."
            )

    return suggestions


class PredictionSerializer(serializers.ModelSerializer):
    performance_category = serializers.SerializerMethodField()
    improvement_suggestions = serializers.SerializerMethodField()

    class Meta:
        model = Prediction
        fields = [
            "id",
            "study_hours",
            "attendance",
            "previous_marks",
            "assignments",
            "predicted_marks",
            "performance_category",
            "improvement_suggestions",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "predicted_marks",
            "performance_category",
            "improvement_suggestions",
            "created_at",
        ]

    def get_performance_category(self, obj):
        if obj.predicted_marks is None:
            return None
        marks = float(obj.predicted_marks)
        if marks >= 80:
            return "Excellent"
        elif marks >= 60:
            return "Good"
        return "Needs Improvement"


    def get_improvement_suggestions(self, obj):
        if obj.predicted_marks is None:
            return []
        return generate_improvement_suggestions(
            obj.study_hours,
            obj.attendance,
            obj.previous_marks,
            obj.assignments,
            obj.predicted_marks,
        )

    def validate_study_hours(self, value):
        if value < 0 or value > 24:
            raise serializers.ValidationError(
                "Study hours must be between 0 and 24."
            )
        return value

    def validate_attendance(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Attendance must be between 0 and 100."
            )
        return value

    def validate_previous_marks(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Previous marks must be between 0 and 100."
            )
        return value

    def validate_assignments(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Assignments cannot be negative."
            )
        return value




class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password"
        ]

    def validate_username(self, value):

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Username already exists."
            )

        return value

    def validate_email(self, value):

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists."
            )

        return value

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )

        return user