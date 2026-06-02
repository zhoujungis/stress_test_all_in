import hashlib
import uuid
import requests


class CloudClient:
    """Glazero云平台客户端"""

    BASE_URL = "https://admin-cn.aosulife.com"
    PID = "glazero"

    def __init__(self):
        self.username = ""
        self.password = ""
        self.region = "CN"
        self._session = requests.Session()
        self._gz_sid = None
        self._gz_username = None
        self._logged_in = False

        self._session.headers.update({
            "accept": "application/json, text/plain, */*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://admin.glazero.com",
            "referer": "https://admin.glazero.com/",
            "user-agent": "Mozilla/5.0"
        })

    def configure(self, username: str, password: str, region: str = "CN"):
        self.username = username
        self.password = password
        self.region = region.upper()

    def login(self) -> bool:
        if not self.username or not self.password:
            return False

        url = f"{self.BASE_URL}/admin/adminUser/login"
        params = {"uuid": str(uuid.uuid4()), "pid": self.PID}
        # MD5 required by cloud API — not a local security choice
        md5_pwd = hashlib.md5(self.password.encode()).hexdigest()
        data = {"username": self.username, "password": md5_pwd, "uuid": str(uuid.uuid4())}

        try:
            resp = self._session.post(url, params=params, data=data)
            result = resp.json()

            ok = result.get("code") in (200, 0) or result.get("success") in (True, "true")
            if not ok:
                return False

            data_obj = result.get("data", {})
            if isinstance(data_obj, dict):
                self._gz_sid = data_obj.get("gz_sid") or data_obj.get("sid") or data_obj.get("token")
                self._gz_username = data_obj.get("gz_username") or self.username

            if not self._gz_sid:
                self._gz_sid = self._session.cookies.get("gz_sid", self.username)
            self._gz_username = self._gz_username or self.username
            self._logged_in = True
            return True
        except Exception:
            return False

    def is_logged_in(self) -> bool:
        return self._logged_in

    def _request(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        params = {"uuid": str(uuid.uuid4()), "pid": self.PID}
        body = {
            "gz_sid": self._gz_sid or self.username,
            "gz_username": self._gz_username or self.username,
            "uuid": str(uuid.uuid4()),
        }
        if data:
            body.update(data)

        try:
            if method == "POST":
                resp = self._session.post(url, params=params, data=body, timeout=30)
            else:
                resp = self._session.get(url, params=params, timeout=30)
            result = resp.json()
            return {"success": result.get("code") in (200, 0), "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def trigger_ota(self, device_sn: str, firmware_version: str = "") -> dict:
        """触发OTA升级"""
        data = {"clientId": device_sn}
        if firmware_version:
            data["version"] = firmware_version
        return self._request("POST", "/admin/firmware/ota/upgrade", data)

    def check_ota_status(self, device_sn: str) -> dict:
        """查询设备OTA状态"""
        return self._request("POST", "/admin/firmware/ota/status", {"clientId": device_sn})

    def get_device_logs(self, device_sn: str, date_str: str, page: int = 1) -> dict:
        """获取设备日志列表"""
        from datetime import datetime
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            formatted = dt.strftime("%Y-%m-%dT16:00:00.000Z")
        except ValueError:
            formatted = date_str
        return self._request("POST", "/admin/clientlog/getList", {
            "clientId": device_sn, "date": formatted,
            "page": str(page), "count": "10",
        })

    def post(self, path: str, data: dict = None, timeout: float = 30.0) -> dict:
        """通用POST（兼容旧接口）"""
        url = f"{self.BASE_URL}{path}"
        try:
            resp = self._session.post(url, json=data or {}, timeout=timeout)
            return {"success": resp.ok, "status_code": resp.status_code,
                    "data": resp.json() if resp.text else None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def is_configured(self) -> bool:
        return bool(self.username)

    def close(self):
        self._session.close()
        self._logged_in = False
