"""登录凭证回归测试：只使用内存数据库，不连接或修改业务数据库。"""
import asyncio
import hashlib
import json
import os
import unittest
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import Base, get_db
from routers import auth, announcement


class LoginCredentialTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([
            models.User(id="u", username="员工", password="123456", role="EMPLOYEE", job_grade="P1"),
            models.User(id="a", username="管理员", password="123456", role="ADMIN", job_grade="P1"),
        ])
        self.db.commit()
        self.app = FastAPI()
        self.app.include_router(auth.router)
        self.app.include_router(announcement.router)
        self.app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def request(self, method, path, body=None, token=None):
        # 直接调用 ASGI 应用，验证真实路由与依赖注入，不额外安装测试客户端。
        async def run():
            messages = []
            async def receive():
                return {"type": "http.request", "body": json.dumps(body or {}).encode(), "more_body": False}
            async def send(message):
                messages.append(message)
            headers = [(b"content-type", b"application/json")]
            if token:
                headers.append((b"authorization", f"Bearer {token}".encode()))
            await self.app({"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
                            "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
                            "query_string": b"", "headers": headers, "root_path": "",
                            "client": ("127.0.0.1", 1), "server": ("test", 80)}, receive, send)
            status = next(m["status"] for m in messages if m["type"] == "http.response.start")
            data = json.loads(b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body"))
            return status, data
        return asyncio.run(run())

    def login(self, uid="u", path="user-login"):
        status, data = self.request("POST", f"/api/v1/auth/{path}", {"user_id": uid, "password": "123456"})
        self.assertEqual(status, 200)
        return data["access_token"]

    def test_login_me_and_hash_storage(self):
        token = self.login()
        session = self.db.query(models.LoginSession).one()
        self.assertEqual(session.token_hash, hashlib.sha256(token.encode()).hexdigest())
        self.assertNotEqual(token, session.token_hash)
        status, data = self.request("GET", "/api/v1/auth/me", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(data["data"]["id"], "u")
        self.assertNotIn("password", data["data"])

    def test_missing_fake_and_expired_credentials(self):
        for token in (None, "u", "fake-token"):
            self.assertEqual(self.request("GET", "/api/v1/auth/me", token=token)[0], 401)
        token = self.login()
        self.db.query(models.LoginSession).one().expires_at = datetime.utcnow() - timedelta(seconds=1)
        self.db.commit()
        self.assertEqual(self.request("GET", "/api/v1/auth/me", token=token)[0], 401)

    def test_logout_revokes_only_current_session(self):
        first, second = self.login(), self.login()
        self.assertEqual(self.request("POST", "/api/v1/auth/logout", token=first)[0], 200)
        self.assertEqual(self.request("GET", "/api/v1/auth/me", token=first)[0], 401)
        self.assertEqual(self.request("GET", "/api/v1/auth/me", token=second)[0], 200)

    def test_admin_and_existing_login_rules(self):
        token = self.login("a", "admin-login")
        self.assertEqual(self.request("GET", "/api/v1/auth/me", token=token)[1]["data"]["role"], "ADMIN")
        self.assertEqual(self.request("POST", "/api/v1/auth/admin-login", {"user_id": "u", "password": "123456"})[0], 403)
        self.assertEqual(self.request("POST", "/api/v1/auth/user-login", {"user_id": "u", "password": "wrong"})[0], 400)

    def test_current_user_reads_latest_database_information(self):
        token = self.login()
        user = self.db.query(models.User).filter_by(id="u").one()
        user.department = "研发科"
        self.db.commit()
        self.assertEqual(self.request("GET", "/api/v1/auth/me", token=token)[1]["data"]["department"], "研发科")
        user.is_deleted = True
        self.db.commit()
        self.assertEqual(self.request("GET", "/api/v1/auth/me", token=token)[0], 401)

    def test_announcement_dependency_rejects_missing_token(self):
        self.assertEqual(self.request("POST", "/api/v1/announcements", {"title": "标题", "content": "正文"})[0], 401)


if __name__ == "__main__":
    unittest.main()
