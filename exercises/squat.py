def get_squat_data(points):
    """Returns joints and thresholds for squats."""
    # Hip(23), Knee(25), Ankle(27)
    p1 = [points[23].x, points[23].y]
    p2 = [points[25].x, points[25].y]
    p3 = [points[27].x, points[27].y]
    
    # Check visibility of knee and ankle
    is_visible = points[25].visibility > 0.5 and points[27].visibility > 0.5
    
    return p1, p2, p3, is_visible, 90, 165, "Show your full legs!"