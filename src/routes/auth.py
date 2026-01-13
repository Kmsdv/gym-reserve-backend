from flask import Blueprint, request, jsonify
from sqlalchemy import text
from src.extensions import db

bp = Blueprint('auth', __name__)

# -------------------------
# 用户注册
# -------------------------
@bp.route("/api/register", methods=["POST"])
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
