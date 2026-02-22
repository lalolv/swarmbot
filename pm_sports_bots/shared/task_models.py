"""任务模型定义"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import StrEnum
from typing import Any, Optional
from uuid import uuid4


class TaskState(StrEnum):
    """任务状态枚举"""

    PENDING = "pending"        # 等待启动
    RUNNING = "running"        # 运行中
    SLEEPING = "sleeping"      # 休眠（数据保留，不运行）
    COMPLETED = "completed"    # 正常完成
    CANCELLED = "cancelled"    # 用户取消（物理删除前瞬态）
    FAILED = "failed"          # 异常失败


@dataclass
class TaskRobotSpec:
    """任务中的机器人声明。"""

    type: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "enabled": self.enabled,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskRobotSpec":
        robot_type = data.get("type")
        if not isinstance(robot_type, str) or not robot_type:
            raise ValueError("Robot spec must include non-empty 'type'")

        enabled = data.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"Robot spec '{robot_type}': 'enabled' must be boolean")

        config = data.get("config") or {}
        if not isinstance(config, dict):
            raise ValueError(f"Robot spec '{robot_type}': 'config' must be object")

        return cls(type=robot_type, enabled=enabled, config=config)

    @classmethod
    def from_any(cls, spec: str | dict[str, Any]) -> "TaskRobotSpec":
        if isinstance(spec, str):
            if not spec:
                raise ValueError("Robot spec string must be non-empty")
            return cls(type=spec)
        if isinstance(spec, dict):
            return cls.from_dict(spec)
        raise ValueError("Robot spec must be string or object")


@dataclass
class TaskConfig:
    """任务配置

    # 🔧 自定义点: 添加业务特定的配置字段
    """

    task_id: str = ""
    user_id: str = ""
    name: str = ""
    description: str = ""
    robots: list[TaskRobotSpec] = field(default_factory=list)
    custom_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        payload = asdict(self)
        payload["robots"] = [robot.to_dict() for robot in self.robots]
        return payload

    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskConfig":
        """从字典创建"""
        robots_raw = data.get("robots")
        if robots_raw is None:
            legacy_custom_config = data.get("custom_config") or {}
            if isinstance(legacy_custom_config, dict):
                robots_raw = legacy_custom_config.get("robots")

        if not isinstance(robots_raw, list):
            raise ValueError("Task config requires 'robots' as a list")

        robots = [TaskRobotSpec.from_any(item) for item in robots_raw]
        if not robots:
            raise ValueError("Task config requires at least one robot")

        custom_config = data.get("custom_config") or {}
        if not isinstance(custom_config, dict):
            raise ValueError("Task config 'custom_config' must be an object")

        return cls(
            task_id=str(data.get("task_id", "")),
            user_id=str(data.get("user_id", "")),
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            robots=robots,
            custom_config=custom_config,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "TaskConfig":
        """从 JSON 反序列化"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class TaskStatus:
    """任务状态"""

    task_id: str
    state: TaskState
    created_at: str   # ISO 格式时间戳
    updated_at: str   # ISO 格式时间戳
    error: Optional[str] = None
    user_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "user_id": self.user_id,
        }

    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskStatus":
        """从字典创建"""
        return cls(
            task_id=data["task_id"],
            state=TaskState(data["state"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            error=data.get("error"),
            user_id=str(data.get("user_id", "")),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "TaskStatus":
        """从 JSON 反序列化"""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def create(cls, task_id: str, user_id: str = "") -> "TaskStatus":
        """创建新任务状态"""
        now = datetime.utcnow().isoformat() + "Z"
        return cls(
            task_id=task_id,
            state=TaskState.PENDING,
            created_at=now,
            updated_at=now,
            user_id=user_id,
        )

    def update_state(self, state: TaskState, error: Optional[str] = None) -> None:
        """更新状态"""
        self.state = state
        self.updated_at = datetime.utcnow().isoformat() + "Z"
        if error:
            self.error = error


@dataclass
class TaskCommand:
    """任务控制命令。"""

    command_id: str
    task_id: str
    action: str
    payload: dict[str, Any]
    actor: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "task_id": self.task_id,
            "action": self.action,
            "payload": self.payload,
            "actor": self.actor,
            "created_at": self.created_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def create(
        cls,
        task_id: str,
        action: str,
        payload: Optional[dict[str, Any]] = None,
        actor: str = "api",
    ) -> "TaskCommand":
        return cls(
            command_id=f"cmd-{uuid4().hex}",
            task_id=task_id,
            action=action,
            payload=payload or {},
            actor=actor,
            created_at=datetime.utcnow().isoformat() + "Z",
        )


@dataclass
class CommandReceipt:
    """任务命令处理回执。"""

    command_id: str
    task_id: str
    action: str
    status: str
    timestamp: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "command_receipt",
            "command_id": self.command_id,
            "task_id": self.task_id,
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
