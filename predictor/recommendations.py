def generate_recommendations(
    study_hours,
    attendance,
    previous_marks,
    predicted_marks
):
    recommendations = []

    # =====================================================
    # ATTENDANCE RECOMMENDATION
    # =====================================================
    if attendance < 75:
        recommendations.append(
            "Your attendance is below 75%. "
            "Improving attendance may help your performance."
        )
    elif attendance >= 90:
        recommendations.append(
            "Your attendance is excellent. Keep it up!"
        )
    else:
        recommendations.append(
            "Your attendance is good. Maintain your attendance."
        )

    # =====================================================
    # STUDY HOURS RECOMMENDATION
    # =====================================================
    if study_hours < 5:
        recommendations.append(
            "Consider increasing your study hours "
            "for better preparation."
        )
    else:
        recommendations.append(
            "Your study hours are good. "
            "Maintain your current study consistency."
        )

    # =====================================================
    # PREVIOUS VS PREDICTED MARKS
    # =====================================================
    difference = (
        predicted_marks -
        previous_marks
    )

    if difference >= 5:
        recommendations.append(
            "Your predicted performance is higher "
            "than your previous marks. Great progress!"
        )
    elif difference < -10:
        recommendations.append(
            "Your predicted marks are significantly "
            "lower than your previous marks. "
            "Focus on consistent preparation."
        )
    elif difference < 0:
        recommendations.append(
            "Your predicted marks are slightly lower "
            "than your previous marks. "
            "Try to improve your preparation."
        )
    else:
        recommendations.append(
            "Your predicted performance is consistent "
            "with your previous marks."
        )

    # =====================================================
    # OVERALL PERFORMANCE
    # =====================================================
    if predicted_marks >= 80:
        performance = "Excellent"
    elif predicted_marks >= 60:
        performance = "Good"
    else:
        performance = "Needs Improvement"

    return {
        "performance": performance,
        "recommendations": recommendations
    }
