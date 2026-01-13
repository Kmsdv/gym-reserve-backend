from flask import Blueprint, jsonify
from sqlalchemy import text
from src.extensions import db

bp = Blueprint('main', __name__)

# -------------------------
# 数据汇总接口
# -------------------------
@bp.route("/api/summary", methods=["GET"])
def summary():
    # 用户总数
    users = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()

    # 设施总数
    facilities = db.session.execute(text("SELECT COUNT(*) FROM facilities")).scalar()

    # 预约总数
    reservations = db.session.execute(text("SELECT COUNT(*) FROM reservations")).scalar()

    # 预约状态分布（转中文）
    status_rows = db.session.execute(
        text("SELECT status, COUNT(*) FROM reservations GROUP BY status")
    ).fetchall()
    status_map = {"pending": "待确认", "confirmed": "已确认"}
    status_data = [
        {"name": status_map.get(r[0], r[0]), "value": r[1]} for r in status_rows
    ]

    # 使用趋势（按日统计）
    trend_rows = db.session.execute(
        text("""
            SELECT DATE(start_time) AS day, COUNT(*) 
            FROM reservations 
            GROUP BY DATE(start_time) 
            ORDER BY day
        """)
    ).fetchall()
    trend_data = [
        {"date": r[0].strftime("%Y-%m-%d"), "count": r[1]} for r in trend_rows
    ]

    # 评分分布
    score_rows = db.session.execute(
        text("SELECT score, COUNT(*) FROM ratings GROUP BY score ORDER BY score")
    ).fetchall()
    score_dist = [{"score": row[0], "count": row[1]} for row in score_rows]


    return jsonify(
        status=200,
        msg="查询成功",
        data={
            "users": users,
            "facilities": facilities,
            "reservations": reservations,
            "status_data": status_data,
            "trend_data": trend_data,
            "score_dist": score_dist,
        },
    )
