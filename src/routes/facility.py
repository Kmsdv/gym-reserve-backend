from flask import Blueprint, request, jsonify
from sqlalchemy import text
from src.extensions import db
from datetime import datetime

bp = Blueprint('facility', __name__)

# -------------------------
# 首页推荐设施（评分最高的前5个）
# -------------------------
@bp.route("/api/facilities/recommend", methods=["GET"])
def recommend_facilities():
    sql = text("""
        SELECT f.facility_id, f.facility_name, f.facility_type, f.description, f.location, f.capacity,
               ROUND(AVG(r.score), 2) AS avg_score
        FROM facilities f
        LEFT JOIN ratings r ON f.facility_id = r.facility_id
        GROUP BY f.facility_id, f.facility_name, f.facility_type, f.description, f.location, f.capacity
        ORDER BY avg_score IS NULL, avg_score DESC
        LIMIT 5
    """)
    data = db.session.execute(sql).fetchall()
    facilities = [dict(
        facility_id=row[0],
        facility_name=row[1],
        facility_type=row[2],
        description=row[3],
        location=row[4],
        capacity=row[5],
        avg_score=row[6] if row[6] is not None else None
    ) for row in data]
    return jsonify(status=200, msg="推荐成功", data=facilities)


# -------------------------
# 管理员设施管理
# -------------------------
@bp.route("/api/admin/facilities", methods=["GET", "POST", "PUT", "DELETE"])
def admin_facilities():
    if request.method == "GET":
        data = db.session.execute(text("SELECT * FROM facilities")).fetchall()
        facilities = [dict(
            facility_id=row[0],
            facility_name=row[1],
            facility_type=row[2],
            description=row[3],
            location=row[4],
            capacity=row[5]
        ) for row in data]
        return jsonify(status=200, data=facilities)

    if request.method == "POST":
        rq = request.json
        sql = text(
            "INSERT INTO facilities (facility_name, facility_type, description, location, capacity) "
            "VALUES (:name, :type, :desc, :loc, :cap)"
        )
        db.session.execute(sql, {
            "name": rq.get("facility_name"),
            "type": rq.get("facility_type"),
            "desc": rq.get("description"),
            "loc": rq.get("location"),
            "cap": rq.get("capacity")
        })
        db.session.commit()
        return jsonify(status=200, msg="设施添加成功")

    if request.method == "PUT":
        rq = request.json
        sql = text(
            "UPDATE facilities SET facility_name=:name, facility_type=:type, description=:desc, location=:loc, capacity=:cap "
            "WHERE facility_id=:fid"
        )
        result = db.session.execute(sql, {
            "name": rq.get("facility_name"),
            "type": rq.get("facility_type"),
            "desc": rq.get("description"),
            "loc": rq.get("location"),
            "cap": rq.get("capacity"),
            "fid": rq.get("facility_id")
        })
        db.session.commit()
        if result.rowcount == 0:
            return jsonify(status=404, msg="设施不存在")
        return jsonify(status=200, msg="设施修改成功")

    if request.method == "DELETE":
        fid = request.json.get("facility_id")
        sql = text("DELETE FROM facilities WHERE facility_id=:fid")
        result = db.session.execute(sql, {"fid": fid})
        db.session.commit()
        if result.rowcount == 0:
            return jsonify(status=404, msg="设施不存在")
        return jsonify(status=200, msg="设施删除成功")


# -------------------------
# 设施列表（支持搜索/筛选）
# -------------------------
@bp.route("/api/facilities", methods=["GET"])
def list_facilities():
    ftype = request.args.get("type")
    keyword = request.args.get("keyword")

    sql = "SELECT facility_id, facility_name, facility_type, description, location, capacity FROM facilities WHERE 1=1 "
    params = {}

    if ftype:
        sql += "AND facility_type=:t "
        params["t"] = ftype

    if keyword:
        sql += "AND (facility_name LIKE :kw OR description LIKE :kw OR location LIKE :kw) "
        params["kw"] = f"%{keyword}%"

    data = db.session.execute(text(sql), params).fetchall()
    facilities = [dict(
        facility_id=row[0],
        facility_name=row[1],
        facility_type=row[2],
        description=row[3],
        location=row[4],
        capacity=row[5]
    ) for row in data]
    return jsonify(status=200, data=facilities)


# -------------------------
# 设施详情
# -------------------------
@bp.route("/api/facilities/<int:fid>", methods=["GET"])
def facility_detail(fid):
    row = db.session.execute(
        text("SELECT facility_id, facility_name, facility_type, description, location, capacity "
             "FROM facilities WHERE facility_id=:fid"),
        {"fid": fid}
    ).fetchone()
    if not row:
        return jsonify(status=404, msg="设施不存在")

    facility = dict(
        facility_id=row[0],
        facility_name=row[1],
        facility_type=row[2],
        description=row[3],
        location=row[4],
        capacity=row[5]
    )
    return jsonify(status=200, data=facility)

# -------------------------
# 查看某个设施的评分和评论
# -------------------------
@bp.route("/api/facilities/<int:fid>/ratings", methods=["GET"])
def facility_ratings(fid):
    # 查询设施是否存在
    facility = db.session.execute(
        text("SELECT facility_name FROM facilities WHERE facility_id=:fid"),
        {"fid": fid}
    ).fetchone()

    if not facility:
        return jsonify(status=404, msg="设施不存在")

    # 查询该设施的评分和评论
    rows = db.session.execute(
        text("""
            SELECT r.rating_id, u.username, r.score, r.comment, r.created_at
            FROM ratings r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.facility_id=:fid
            ORDER BY r.created_at DESC
        """),
        {"fid": fid}
    ).fetchall()

    # 格式化输出
    ratings = []
    for r in rows:
        ratings.append({
            "rating_id": r[0],
            "username": r[1],
            "score": r[2],
            "comment": r[3],
            "created_at": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else None
        })

    # 查询平均评分
    avg_score = db.session.execute(
        text("SELECT AVG(score) FROM ratings WHERE facility_id=:fid"),
        {"fid": fid}
    ).scalar()

    return jsonify(
        status=200,
        msg="查询成功",
        data={
            "facility_name": facility[0],
            "average_score": round(avg_score, 2) if avg_score else None,
            "ratings": ratings
        }
    )

# -------------------------
# 提交设施评分和评论（支持新增或更新）
# -------------------------
@bp.route("/api/facilities/<int:fid>/rate", methods=["POST"])
def add_or_update_rating(fid):
    data = request.json
    username = data.get("username")
    score = data.get("score")
    comment = data.get("comment")

    if not username or score is None:
        return jsonify(status=400, msg="用户名和评分不能为空")

    # 检查用户是否存在
    user = db.session.execute(
        text("SELECT user_id FROM users WHERE username=:username"),
        {"username": username}
    ).fetchone()
    if not user:
        return jsonify(status=404, msg="用户不存在")

    # 检查设施是否存在
    facility = db.session.execute(
        text("SELECT facility_id FROM facilities WHERE facility_id=:fid"),
        {"fid": fid}
    ).fetchone()
    if not facility:
        return jsonify(status=404, msg="设施不存在")

    user_id = user[0]

    # 查询用户是否已有该设施的评分
    existing = db.session.execute(
        text("SELECT rating_id FROM ratings WHERE user_id=:uid AND facility_id=:fid"),
        {"uid": user_id, "fid": fid}
    ).fetchone()

    if existing:
        # 已有评分则更新
        db.session.execute(
            text("""
                UPDATE ratings
                SET score=:score, comment=:comment, created_at=:created
                WHERE rating_id=:rid
            """),
            {
                "score": score,
                "comment": comment,
                "created": datetime.now(),
                "rid": existing[0]
            }
        )
        db.session.commit()
        return jsonify(status=200, msg="评分已更新")
    else:
        # 不存在则新增
        db.session.execute(
            text("""
                INSERT INTO ratings (user_id, facility_id, score, comment, created_at)
                VALUES (:uid, :fid, :score, :comment, :created)
            """),
            {
                "uid": user_id,
                "fid": fid,
                "score": score,
                "comment": comment,
                "created": datetime.now()
            }
        )
        db.session.commit()
        return jsonify(status=200, msg="评分提交成功")
