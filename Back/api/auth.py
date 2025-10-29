from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """회원가입

    Request Body:
        - id (str, required): 사용자 아이디 (로그인용)
        - username (str, required): 사용자 닉네임 (표시용)
        - password (str, required): 비밀번호
        - email (str, optional): 이메일

    Returns:
        201: 회원가입 성공
        400: 필수 필드 누락
        409: 아이디 또는 이메일 중복
    """
    data = request.get_json()

    # 필수 필드 확인
    required_fields = ["id", "username", "password"]
    if not all(field in data for field in required_fields):
        return (
            jsonify(
                {"error": "Missing required fields", "required_fields": required_fields}
            ),
            400,
        )

    # 아이디 중복 확인
    if User.query.filter_by(id=data["id"]).first():
        return jsonify({"error": "ID already exists"}), 409

    # 이메일 중복 확인 (이메일이 제공된 경우)
    if data.get("email"):
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 409

    # 사용자 생성
    user = User(
        id=data["id"], username=data["username"], email=data.get("email")  # 선택 사항
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return (
        jsonify({"message": "User registered successfully", "user": user.to_dict()}),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """로그인

    Request Body:
        - id (str, required): 사용자 아이디
        - password (str, required): 비밀번호

    Returns:
        200: 로그인 성공 (access_token, refresh_token 반환)
        400: 필수 필드 누락
        401: 아이디 또는 비밀번호 오류
        403: 계정 비활성화
    """
    data = request.get_json()

    # 필수 필드 확인
    if not data.get("id") or not data.get("password"):
        return jsonify({"error": "ID and password required"}), 400

    # 사용자 확인 (id 필드로 조회)
    user = User.query.filter_by(id=data["id"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid ID or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    # 토큰 생성 (identity는 user.id - 문자열 형태의 사용자 아이디)
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return (
        jsonify(
            {
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.to_dict(),
            }
        ),
        200,
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """토큰 갱신"""
    # current_user_id = get_jwt_identity()
    current_user_id = "1"
    access_token = create_access_token(identity=current_user_id)

    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """현재 사용자 정보"""
    # current_user_id = get_jwt_identity()
    current_user_id = "1"
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """로그아웃 (클라이언트에서 토큰 삭제)"""
    return jsonify({"message": "Logout successful"}), 200
