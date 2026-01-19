def get_bicep_curl_data(points):
    """Returns joints and thresholds for bicep curls."""
    # Shoulder(11), Elbow(13), Wrist(15)
    p1 = [points[11].x, points[11].y]
    p2 = [points[13].x, points[13].y]
    p3 = [points[15].x, points[15].y]
    
    # Check visibility of elbow and wrist
    is_visible = points[13].visibility > 0.5 and points[15].visibility > 0.5
    
    return p1, p2, p3, is_visible, 40, 155, "Show your full arm!"