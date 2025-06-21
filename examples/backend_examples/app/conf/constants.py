"""
这个模块将常量固定
框架项目的顶层目录
一定要注意，所有功能最好不好耦合，各个模块单独运行，有利于系统的良好运行
只有该模块，对相关环境的路径进行明确，与其他模块进行必要的联系
"""

import os
from pathlib import Path

# 根目录
root_path = Path(__file__).parent.parent.parent.absolute()
# 后端目录
backend_path = root_path / "backend"
# 前端目录
frontend_path = root_path / "frontend"
# 日志目录
log_path = root_path / "logs"
# 例子目录
examples_path = root_path / "examples"


TORTOISE_ORM: dict = {
    "connections": {
        # SQLite configuration
        "sqlite": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": f"{root_path}/db.sqlite3"
            },  # Path to SQLite database file
        },
        # MySQL/MariaDB configuration
        # Install with: tortoise-orm[asyncmy]
        # "mysql": {
        #     "engine": "tortoise.backends.mysql",
        #     "credentials": {
        #         "host": "localhost",  # Database host address
        #         "port": 3306,  # Database port
        #         "user": "yourusername",  # Database username
        #         "password": "yourpassword",  # Database password
        #         "database": "yourdatabase",  # Database name
        #     },
        # },
        # PostgreSQL configuration
        # Install with: tortoise-orm[asyncpg]
        # "postgres": {
        #     "engine": "tortoise.backends.asyncpg",
        #     "credentials": {
        #         "host": "localhost",  # Database host address
        #         "port": 5432,  # Database port
        #         "user": "yourusername",  # Database username
        #         "password": "yourpassword",  # Database password
        #         "database": "yourdatabase",  # Database name
        #     },
        # },
        # MSSQL/Oracle configuration
        # Install with: tortoise-orm[asyncodbc]
        # "oracle": {
        #     "engine": "tortoise.backends.asyncodbc",
        #     "credentials": {
        #         "host": "localhost",  # Database host address
        #         "port": 1433,  # Database port
        #         "user": "yourusername",  # Database username
        #         "password": "yourpassword",  # Database password
        #         "database": "yourdatabase",  # Database name
        #     },
        # },
        # SQLServer configuration
        # Install with: tortoise-orm[asyncodbc]
        # "sqlserver": {
        #     "engine": "tortoise.backends.asyncodbc",
        #     "credentials": {
        #         "host": "localhost",  # Database host address
        #         "port": 1433,  # Database port
        #         "user": "yourusername",  # Database username
        #         "password": "yourpassword",  # Database password
        #         "database": "yourdatabase",  # Database name
        #     },
        # },
    },
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "sqlite",
        },
    },
    "use_tz": False,  # Whether to use timezone-aware datetimes
    "timezone": "Asia/Shanghai",  # Timezone setting
}
DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

if __name__ == "__main__":
    print(root_path)
    print(backend_path)
    print(frontend_path)
    print(log_path)
