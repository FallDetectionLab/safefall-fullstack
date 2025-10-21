"""
Dashboard API - 대시보드용 통합 엔드포인트
로컬 버전의 기능들을 통합
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

from models import db, Incident, StreamSession

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/stats", methods=["GET"])
# @jwt_required()
def get_dashboard_stats():
    """
    대시보드 통계 조회

    Returns:
        - totalVideos: 전체 영상 수
        - checkedVideos: 확인된 영상 수
        - uncheckedVideos: 미확인 영상 수
        - todayVideos: 오늘 발생한 영상 수
        - checkRate: 확인률 (%)
        - system_status: 시스템 상태
    """
    try:
        # current_user_id = get_jwt_identity()
        current_user_id = "1"
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # 통계 집계
        stats_query = (
            db.session.query(
                func.count(Incident.id).label("total"),
                func.sum(db.case((Incident.is_checked == True, 1), else_=0)).label(
                    "checked"
                ),
                func.sum(
                    db.case((Incident.detected_at >= today_start, 1), else_=0)
                ).label("today"),
            )
            .filter(Incident.user_id == current_user_id)
            .first()
        )

        total = stats_query.total or 0
        checked = stats_query.checked or 0
        today = stats_query.today or 0
        unchecked = total - checked
        check_rate = (checked / total * 100) if total > 0 else 0

        # 시스템 상태 확인
        active_session = StreamSession.query.filter_by(is_active=True).first()
        system_status = "active" if active_session else "inactive"

        return (
            jsonify(
                {
                    "success": True,
                    "totalVideos": total,
                    "checkedVideos": checked,
                    "uncheckedVideos": unchecked,
                    "todayVideos": today,
                    "checkRate": round(check_rate, 1),
                    "system_status": system_status,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "totalVideos": 0,
                    "checkedVideos": 0,
                    "uncheckedVideos": 0,
                    "todayVideos": 0,
                    "checkRate": 0.0,
                    "system_status": "error",
                }
            ),
            500,
        )


@dashboard_bp.route("/recent-videos", methods=["GET"])
# @jwt_required()
def get_recent_videos():
    """
    최근 영상 목록 조회

    Query Parameters:
        - limit: 조회할 영상 수 (기본: 6)
    """
    try:
        # current_user_id = get_jwt_identity()
        current_user_id = "1"
        limit = request.args.get("limit", 6, type=int)

        # 최근 영상 조회
        incidents = (
            Incident.query.filter_by(user_id=current_user_id)
            .order_by(Incident.detected_at.desc())
            .limit(limit)
            .all()
        )

        videos = []
        for incident in incidents:
            video_data = incident.to_dict()
            # 프론트엔드 호환성을 위한 추가 필드
            video_data.update(
                {
                    "url": f"/api/incidents/{incident.id}/video",
                    "thumbnail_url": (
                        f"/api/incidents/{incident.id}/thumbnail"
                        if incident.thumbnail_path
                        else None
                    ),
                }
            )
            videos.append(video_data)

        return jsonify({"success": True, "data": videos, "count": len(videos)}), 200

    except Exception as e:
        print(f"❌ Recent videos error: {e}")
        return jsonify({"success": False, "error": str(e), "data": [], "count": 0}), 500


@dashboard_bp.route("/incidents/summary", methods=["GET"])
# @jwt_required()
def get_incidents_summary():
    """
    사고 요약 정보

    Query Parameters:
        - days: 조회 기간 (일 단위, 기본: 7)
    """
    try:
        # current_user_id = get_jwt_identity()
        current_user_id = "1"
        days = request.args.get("days", 7, type=int)

        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # 기간별 사고 통계
        incidents = Incident.query.filter(
            Incident.user_id == current_user_id, Incident.detected_at >= start_date
        ).all()

        # 타입별 집계
        by_type = {}
        by_date = {}

        for incident in incidents:
            # 타입별
            incident_type = incident.incident_type
            by_type[incident_type] = by_type.get(incident_type, 0) + 1

            # 날짜별
            date_key = incident.detected_at.strftime("%Y-%m-%d")
            by_date[date_key] = by_date.get(date_key, 0) + 1

        return (
            jsonify(
                {
                    "success": True,
                    "period_days": days,
                    "total_incidents": len(incidents),
                    "by_type": by_type,
                    "by_date": by_date,
                    "incidents": [
                        incident.to_dict() for incident in incidents[:10]
                    ],  # 최근 10개
                }
            ),
            200,
        )

    except Exception as e:
        print(f"❌ Incidents summary error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/stream/status", methods=["GET"])
def get_stream_status():
    """
    스트리밍 상태 확인 (인증 불필요)
    """
    try:
        # 활성 세션 확인
        active_session = StreamSession.query.filter_by(is_active=True).first()

        if active_session:
            return (
                jsonify(
                    {
                        "success": True,
                        "stream_active": True,
                        "status": "active",
                        "session": active_session.to_dict(),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "success": True,
                        "stream_active": False,
                        "status": "inactive",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                200,
            )

    except Exception as e:
        print(f"❌ Stream status error: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "stream_active": False,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )
