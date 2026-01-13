# 社区健身设施预约与推荐系统 · 后端

基于 Flask + SQLAlchemy + MySQL 的后端服务，提供用户注册、设施管理、设施推荐、预约/取消预约、评分与评论、数据汇总等 API。

---

## 项目结构

- `run.py`：项目启动入口
- `src/`：源代码目录
  - `__init__.py`：应用工厂函数与初始化
  - `config.py`：数据库与 Redis 等基础配置
  - `extensions.py`：数据库实例定义
  - `routes/`：路由蓝图模块
    - `auth.py`：用户注册认证
    - `facility.py`：设施管理与推荐
    - `reservation.py`：预约管理
    - `user.py`：用户相关
    - `main.py`：数据汇总
  - `utils/`：工具模块
    - `auth.py`：JWT 编码/解码示例
- `requirements.txt`：Python 依赖
- `sql/`：数据库脚本
- `docs/`：文档资源

---

## 技术栈

- 后端框架：Flask、Flask-Cors、Flask-SQLAlchemy
- 数据库：MySQL（通过 PyMySQL 连接）
- ORM/SQL：SQLAlchemy + 原生 SQL（`sqlalchemy.text`）
- 身份认证：PyJWT（`src/utils/auth.py` 示例，默认未启用强制校验）

---

## 环境准备（Windows）

1) 安装 Python 3.12（或兼容版本），建议使用 Conda 管理环境

```bash
conda create -n web python=3.12
conda activate web
```

2) 安装依赖

```bash
pip install -r requirements.txt
```

3) 准备 MySQL 数据库（建议 Navicat 管理）

- 新建数据库（示例名：`sjk`）
- 导入初始化 SQL（例如 `sql/sjk.sql`，包含 `users`、`facilities`、`reservations`、`ratings` 等表；请根据你实际 SQL 路径导入）

4) 配置后端连接：修改 `src/config.py`

```python
class BaseConfig(object):
		DIALCT = "mysql"
		DRITVER = "pymysql"
		HOST = '127.0.0.1'
		PORT = "3306"
		USERNAME = "root"
		PASSWORD = "<你的数据库密码>"
		DBNAME = 'sjk'

		REDIS_HOST = '127.0.0.1'
		REDIS_PORT = 6379

		SQLALCHEMY_DATABASE_URI = f"{DIALCT}+{DRITVER}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?charset=utf8"
		SQLALCHEMY_TRACK_MODIFICATIONS = True
```

说明：`src/__init__.py` 内部还设置了 `app.secret_key`（用于 session），`src/utils/auth.py` 中的 `secret` 用于 JWT 示例；均为演示用途，请在生产环境替换为安全的随机值。

---

## 启动后端

```bash
python run.py
```

默认在 `http://0.0.0.0:5000` 监听，已启用 CORS（跨域）与 `SESSION_TYPE=filesystem`。

---

## API 说明

统一返回格式：`{"status": <int>, "msg": <string>, "data": <any>}`

状态约定：`200` 成功，`400` 参数错误，`404` 未找到，`409` 冲突。

### 用户相关

- 注册：`POST /api/register`
	- 请求体：
		```json
		{
			"username": "string",
			"password": "string",
			"full_name": "string",
			"phone": "string",
			"email": "string"
		}
		```
	- 返回：`status=200` 注册成功；`409` 用户名已存在；`400` 缺少必填。

### 设施推荐与列表

- 首页推荐（评分最高前 5）：`GET /api/facilities/recommend`

- 设施列表（可筛选/搜索）：`GET /api/facilities`
	- 查询参数：`type`（设施类型，可选），`keyword`（名称/描述/地点关键字，可选）

- 设施详情：`GET /api/facilities/{fid}`

### 管理员设施管理

- 列表：`GET /api/admin/facilities`
- 新增：`POST /api/admin/facilities`
	- 请求体：`{"facility_name","facility_type","description","location","capacity"}`
- 修改：`PUT /api/admin/facilities`
	- 请求体：在新增字段基础上增加 `facility_id`
- 删除：`DELETE /api/admin/facilities`
	- 请求体：`{"facility_id": number}`

### 预约相关

- 创建预约：`POST /api/reservations`
	- 请求体：
		```json
		{
			"username": "string",
			"facility_id": 1,
			"start_time": "YYYY-MM-DD HH:mm:ss",
			"end_time": "YYYY-MM-DD HH:mm:ss"
		}
		```

- 我的预约：`GET /api/my_reservations?username=xxx`
	- 返回时间字段为 `YYYY-MM-DD HH:mm:ss` 格式字符串。

- 取消预约：`POST /api/cancel_reservation`
	- 请求体：`{"reservation_id": number}`

### 评分与评论

- 查看设施评分与评论：`GET /api/facilities/{fid}/ratings`
	- 返回包含 `average_score` 与评论列表。

- 提交/更新评分与评论：`POST /api/facilities/{fid}/rate`
	- 请求体：
		```json
		{
			"username": "string",
			"score": 1,
			"comment": "string"
		}
		```
	- 若该用户对该设施已有评分则更新，否则新增。

### 数据汇总

- 概览统计：`GET /api/summary`
	- 返回：用户总数、设施总数、预约总数、预约状态分布（`pending/confirmed` → 中文映射）、按日使用趋势、评分分布等。

---

## 开发与调试建议

- 确保 MySQL 已运行且 `config.py` 连接正确。
- 时间字段建议统一使用 `YYYY-MM-DD HH:mm:ss` 字符串格式进行传参。
- 目前未启用 JWT 强制验证；若需接入，可在接口层引入 `auth.py` 的 `decode_func()` 做鉴权。
- 生产环境请：
	- 使用安全的 `SECRET_KEY`/JWT 密钥；
	- 关闭 `debug=True`；
	- 配置数据库连接池与超时等参数；
	- 按需开启/配置 Redis（`config.py` 已预留）。

---

## 常见问题

- 连接报错：检查 `HOST/PORT/USERNAME/PASSWORD/DBNAME` 与 MySQL 服务状态。
- 中文/编码问题：连接串已设置 `charset=utf8`，如需 `utf8mb4` 可自行调整。
- 表不存在：确认已正确导入初始化 SQL（`sjk.sql`）。

---

## 前端（可选说明）

如果你有对应前端项目（示例名 `qianduan`），可在前端目录执行：

```bash
npm run dev
```

前后端分离部署时，请确保前端的接口地址指向本后端的 `http://<host>:5000`。

---

一切就绪后，祝你开发顺利！🎉