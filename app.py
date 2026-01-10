from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from config import BaseConfig
from datetime import datetime

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 加载配置
app.config.from_object(BaseConfig)

# session配置
app.secret_key = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'

db = SQLAlchemy(app)


# -------------------------
# 用户注册
# -------------------------

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    full_name = data.get("full_name")
    phone = data.get("phone")
    email = data.get("email")

    if not username or not password:
        return jsonify(status=400, msg="用户名和密码不能为空")

    # 检查是否已有用户
    row = db.session.execute(
        text("SELECT user_id FROM users WHERE username=:username"),
        {"username": username}
    ).fetchone()
    if row:
        return jsonify(status=409, msg="用户名已存在")

    # 插入用户
    db.session.execute(
        text("INSERT INTO users (username, password_hash, full_name, phone, email) VALUES (:username, :password, :full_name, :phone, :email)"),
        {"username": username, "password": password, "full_name": full_name, "phone": phone, "email": email}
    )
    db.session.commit()
    return jsonify(status=200, msg="注册成功")

# -------------------------
# 首页推荐设施（评分最高的前5个）
# -------------------------
@app.route("/api/facilities/recommend", methods=["GET"])
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
@app.route("/api/admin/facilities", methods=["GET", "POST", "PUT", "DELETE"])
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
@app.route("/api/facilities", methods=["GET"])
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
@app.route("/api/facilities/<int:fid>", methods=["GET"])
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
# 预约（使用用户名称）
# -------------------------
@app.route("/api/reservations", methods=["POST"])
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

from datetime import datetime

# -------------------------
# 查询我的预约
# -------------------------
@app.route("/api/my_reservations", methods=["GET"])
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
@app.route("/api/cancel_reservation", methods=["POST"])
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

# -------------------------
# 查询某用户的所有评价
# -------------------------
@app.route("/api/my_ratings", methods=["GET"])
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

# -------------------------
# 数据汇总接口
# -------------------------
@app.route("/api/summary", methods=["GET"])
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

# -------------------------
# 查看某个设施的评分和评论
# -------------------------
@app.route("/api/facilities/<int:fid>/ratings", methods=["GET"])
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
@app.route("/api/facilities/<int:fid>/rate", methods=["POST"])
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



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
