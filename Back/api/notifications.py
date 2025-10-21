from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone

from models import db, Incident

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/latest', methods=['GET'])
def get_latest_notifications():
    """
    Get latest unchecked incident notifications from the last 24 hours.

    NOTE: This endpoint is intentionally unauthenticated to allow the frontend
    to poll for notifications without requiring JWT authentication.
    Consider implementing API key authentication if security is a concern.

    Query Parameters:
        hours (int): Number of hours to look back (default: 24, max: 168)

    Returns:
        JSON response with notification count and list of notifications:
        {
            "count": 2,
            "notifications": [
                {
                    "id": 1,
                    "title": "Fall Detected",
                    "message": "Incident at 2025-01-07 14:30",
                    "severity": "high",
                    "type": "fall",
                    "filename": "video.mp4",
                    "createdAt": "2025-01-07T14:30:00"
                }
            ]
        }

    PERFORMANCE: Uses indexed query on user_id, is_checked, and detected_at
    to efficiently fetch recent unchecked incidents.
    """
    try:
        # SECURITY: Input validation - hours parameter with reasonable limits
        hours = request.args.get('hours', 24, type=int)
        if hours < 1 or hours > 168:  # Max 1 week
            return jsonify({
                'error': 'Invalid hours parameter',
                'message': 'hours must be between 1 and 168'
            }), 400

        # Calculate time threshold using timezone-aware datetime
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

        # PERFORMANCE: Query uses composite index (idx_user_checked) for optimal performance
        # Query unchecked incidents from the last specified hours
        incidents = Incident.query.filter(
            Incident.is_checked == False,
            Incident.detected_at >= time_threshold
        ).order_by(Incident.detected_at.desc()).all()

        # Transform incidents to notification format
        notifications = []
        for incident in incidents:
            notification = {
                'id': incident.id,
                'title': _get_notification_title(incident.incident_type),
                'message': _get_notification_message(incident),
                'severity': _get_severity_level(incident.incident_type),
                'type': incident.incident_type,
                'filename': incident.video_path,
                'createdAt': incident.detected_at.isoformat()
            }
            notifications.append(notification)

        return jsonify({
            'count': len(notifications),
            'notifications': notifications
        }), 200

    except ValueError as e:
        # Handle invalid parameter types
        return jsonify({
            'error': 'Invalid parameter',
            'message': str(e)
        }), 400
    except Exception as e:
        # Log error and return generic error message
        print(f"Error fetching notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to fetch notifications',
            'message': str(e)
        }), 500


def _get_notification_title(incident_type):
    """
    Generate notification title based on incident type.

    Args:
        incident_type (str): Type of incident

    Returns:
        str: Human-readable notification title
    """
    titles = {
        'fall': 'Fall Detected',
        'collapse': 'Collapse Detected',
        'abnormal_behavior': 'Abnormal Behavior Detected',
        'emergency': 'Emergency Detected',
        'unknown': 'Incident Detected'
    }
    return titles.get(incident_type, 'Incident Detected')


def _get_notification_message(incident):
    """
    Generate notification message with incident details.

    Args:
        incident (Incident): Incident model instance

    Returns:
        str: Formatted notification message
    """
    # Format datetime in a user-friendly way
    detected_time = incident.detected_at.strftime('%Y-%m-%d %H:%M')
    message = f"Incident at {detected_time}"

    # Add confidence level if available
    if incident.confidence:
        confidence_percent = int(incident.confidence * 100)
        message += f" (Confidence: {confidence_percent}%)"

    return message


def _get_severity_level(incident_type):
    """
    Determine severity level based on incident type.

    Args:
        incident_type (str): Type of incident

    Returns:
        str: Severity level (high, medium, low)

    BEST PRACTICE: Severity levels help prioritize notifications:
    - high: Requires immediate attention (fall, emergency)
    - medium: Should be reviewed soon (collapse, abnormal_behavior)
    - low: Can be reviewed later (unknown)
    """
    severity_map = {
        'fall': 'high',
        'emergency': 'high',
        'collapse': 'medium',
        'abnormal_behavior': 'medium',
        'unknown': 'low'
    }
    return severity_map.get(incident_type, 'medium')
