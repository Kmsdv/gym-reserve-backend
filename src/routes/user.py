from flask import Blueprint, request, jsonify
from sqlalchemy import text
from src.extensions import db

bp = Blueprint('user', __name__)

# -------------------------
# 查询某用户的所有评价
# -------------------------
@bp.route("/api/my_ratings", methods=["GET"])
def my_ratings():
    username = request.args.get("username")
    if not username:
        return jsonify(status=400, msg="请输入用户名")

    # 查询用户ID
    row = db.session.execute(
        text("SELECT user_id FROM users WHERE username=:username"),
        {"username": username}
    ).fetchone()
    if not row:
        return jsonify(status=404, msg="用户不存在")

    user_id = row[0]

    # 查询该用户的所有评价
    ratings = db.session.execute(
        text("""
            SELECT r.rating_id, f.facility_name, r.score, r.comment, r.created_at
            FROM ratings r
            JOIN facilities f ON r.facility_id = f.facility_id
            WHERE r.user_id=:uid
            ORDER BY r.created_at DESC
        """),
        {"uid": user_id}
    ).fetchall()

    data = []
    for r in ratings:
        data.append({
            "rating_id": r[0],
            "facility_name": r[1],
            "score": r[2],
            "comment": r[3],
            "created_at": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else None
        })

    return jsonify(status=200, msg="查询成功", data=data)
