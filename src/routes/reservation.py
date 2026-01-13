from flask import Blueprint, request, jsonify
from sqlalchemy import text
from src.extensions import db
from datetime import datetime

bp = Blueprint('reservation', __name__)

# -------------------------
# 预约（使用用户名称）
# -------------------------
@bp.route("/api/reservations", methods=["POST"])
def reserve():
    data = request.json
    username = data.get("username")  # 改成 username
    facility_id = data.get("facility_id")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not username or not facility_id or not start_time or not end_time:
        return jsonify(status=400, msg="参数不完整")

    # 查 user_id
    row = db.session.execute(
        text("SELECT user_id FROM users WHERE username=:username"),
        {"username": username}
    ).fetchone()
    if not row:
        return jsonify(status=404, msg="用户不存在")

    user_id = row[0]

    db.session.execute(
        text("INSERT INTO reservations (user_id, facility_id, start_time, end_time) VALUES (:uid, :fid, :start, :end)"),
        {"uid": user_id, "fid": facility_id, "start": start_time, "end": end_time}
    )
    db.session.commit()
    return jsonify(status=200, msg="预约成功")

# -------------------------
# 查询我的预约
# -------------------------
@bp.route("/api/my_reservations", methods=["GET"])
def my_reservations():
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

    # 查询预约记录
    reservations = db.session.execute(
        text("""
            SELECT r.reservation_id, f.facility_name, f.facility_type, r.start_time, r.end_time
            FROM reservations r
            JOIN facilities f ON r.facility_id = f.facility_id
            WHERE r.user_id=:uid
            ORDER BY r.start_time DESC
        """),
        {"uid": user_id}
    ).fetchall()

    # 转换为字典列表并格式化时间
    data = []
    for r in reservations:
        data.append({
            "reservation_id": r[0],
            "facility_name": r[1],
            "facility_type": r[2],
            "start_time": r[3].strftime("%Y-%m-%d %H:%M:%S") if r[3] else None,
            "end_time": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else None
        })

    return jsonify(status=200, msg="查询成功", data=data)

# -------------------------
# 取消预约
# -------------------------
@bp.route("/api/cancel_reservation", methods=["POST"])
def cancel_reservation():
    data = request.json
    reservation_id = data.get("reservation_id")

    if not reservation_id:
        return jsonify(status=400, msg="参数不完整")

    # 检查预约是否存在
    row = db.session.execute(
        text("SELECT reservation_id FROM reservations WHERE reservation_id=:rid"),
        {"rid": reservation_id}
    ).fetchone()

    if not row:
        return jsonify(status=404, msg="预约不存在")

    # 删除预约
    db.session.execute(
        text("DELETE FROM reservations WHERE reservation_id=:rid"),
        {"rid": reservation_id}
    )
    db.session.commit()

    return jsonify(status=200, msg="取消成功")
