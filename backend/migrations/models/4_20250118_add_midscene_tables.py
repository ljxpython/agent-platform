from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- 创建 Midscene 会话表
        CREATE TABLE IF NOT EXISTS "midscene_sessions" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "session_id" VARCHAR(100) NOT NULL UNIQUE,
            "user_id" INT,
            "user_requirement" TEXT NOT NULL,
            "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
            "uploaded_files" JSON NOT NULL DEFAULT '[]',
            "file_count" INT NOT NULL DEFAULT 0,
            "ui_analysis_result" TEXT,
            "interaction_analysis_result" TEXT,
            "midscene_generation_result" TEXT,
            "script_generation_result" TEXT,
            "yaml_script" TEXT,
            "playwright_script" TEXT,
            "script_info" JSON,
            "processing_time" REAL,
            "agent_count" INT NOT NULL DEFAULT 4,
            "total_tokens" INT,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "completed_at" TIMESTAMP
        );

        -- 创建 Midscene 智能体日志表
        CREATE TABLE IF NOT EXISTS "midscene_agent_logs" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "session_id" VARCHAR(100) NOT NULL,
            "agent_name" VARCHAR(50) NOT NULL,
            "agent_type" VARCHAR(30) NOT NULL,
            "step" VARCHAR(100) NOT NULL,
            "status" VARCHAR(20) NOT NULL,
            "input_content" TEXT,
            "output_content" TEXT,
            "error_message" TEXT,
            "processing_time" REAL,
            "token_count" INT,
            "chunk_count" INT NOT NULL DEFAULT 0,
            "started_at" TIMESTAMP NOT NULL,
            "completed_at" TIMESTAMP,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- 创建 Midscene 上传文件表
        CREATE TABLE IF NOT EXISTS "midscene_uploaded_files" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "session_id" VARCHAR(100) NOT NULL,
            "original_filename" VARCHAR(255) NOT NULL,
            "stored_filename" VARCHAR(255) NOT NULL,
            "file_path" VARCHAR(500) NOT NULL,
            "file_size" INT NOT NULL,
            "file_type" VARCHAR(50) NOT NULL,
            "mime_type" VARCHAR(100) NOT NULL,
            "image_width" INT,
            "image_height" INT,
            "image_format" VARCHAR(20),
            "status" VARCHAR(20) NOT NULL DEFAULT 'uploaded',
            "processed_at" TIMESTAMP,
            "uploaded_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- 创建 Midscene 模板表
        CREATE TABLE IF NOT EXISTS "midscene_templates" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "name" VARCHAR(100) NOT NULL,
            "description" TEXT NOT NULL,
            "category" VARCHAR(50) NOT NULL,
            "requirement_template" TEXT NOT NULL,
            "yaml_template" TEXT,
            "playwright_template" TEXT,
            "agent_config" JSON NOT NULL DEFAULT '{}',
            "parameters" JSON NOT NULL DEFAULT '{}',
            "usage_count" INT NOT NULL DEFAULT 0,
            "success_rate" REAL NOT NULL DEFAULT 0.0,
            "is_active" INT NOT NULL DEFAULT 1,
            "is_public" INT NOT NULL DEFAULT 0,
            "created_by" INT,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- 创建 Midscene 统计表
        CREATE TABLE IF NOT EXISTS "midscene_statistics" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            "date" DATE NOT NULL,
            "total_sessions" INT NOT NULL DEFAULT 0,
            "completed_sessions" INT NOT NULL DEFAULT 0,
            "failed_sessions" INT NOT NULL DEFAULT 0,
            "total_files" INT NOT NULL DEFAULT 0,
            "total_file_size" BIGINT NOT NULL DEFAULT 0,
            "avg_processing_time" REAL NOT NULL DEFAULT 0.0,
            "total_tokens" INT NOT NULL DEFAULT 0,
            "ui_analysis_count" INT NOT NULL DEFAULT 0,
            "interaction_analysis_count" INT NOT NULL DEFAULT 0,
            "midscene_generation_count" INT NOT NULL DEFAULT 0,
            "script_generation_count" INT NOT NULL DEFAULT 0,
            "success_rate" REAL NOT NULL DEFAULT 0.0,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE ("date")
        );

        -- 创建索引
        CREATE INDEX IF NOT EXISTS "idx_midscene_sessions_session_id" ON "midscene_sessions" ("session_id");
        CREATE INDEX IF NOT EXISTS "idx_midscene_sessions_user_id" ON "midscene_sessions" ("user_id");
        CREATE INDEX IF NOT EXISTS "idx_midscene_sessions_status" ON "midscene_sessions" ("status");
        CREATE INDEX IF NOT EXISTS "idx_midscene_sessions_created_at" ON "midscene_sessions" ("created_at");

        CREATE INDEX IF NOT EXISTS "idx_midscene_agent_logs_session_id" ON "midscene_agent_logs" ("session_id");
        CREATE INDEX IF NOT EXISTS "idx_midscene_agent_logs_agent_name" ON "midscene_agent_logs" ("agent_name");
        CREATE INDEX IF NOT EXISTS "idx_midscene_agent_logs_status" ON "midscene_agent_logs" ("status");
        CREATE INDEX IF NOT EXISTS "idx_midscene_agent_logs_started_at" ON "midscene_agent_logs" ("started_at");

        CREATE INDEX IF NOT EXISTS "idx_midscene_uploaded_files_session_id" ON "midscene_uploaded_files" ("session_id");
        CREATE INDEX IF NOT EXISTS "idx_midscene_uploaded_files_status" ON "midscene_uploaded_files" ("status");
        CREATE INDEX IF NOT EXISTS "idx_midscene_uploaded_files_uploaded_at" ON "midscene_uploaded_files" ("uploaded_at");

        CREATE INDEX IF NOT EXISTS "idx_midscene_templates_category" ON "midscene_templates" ("category");
        CREATE INDEX IF NOT EXISTS "idx_midscene_templates_is_active" ON "midscene_templates" ("is_active");
        CREATE INDEX IF NOT EXISTS "idx_midscene_templates_is_public" ON "midscene_templates" ("is_public");
        CREATE INDEX IF NOT EXISTS "idx_midscene_templates_created_by" ON "midscene_templates" ("created_by");

        CREATE INDEX IF NOT EXISTS "idx_midscene_statistics_date" ON "midscene_statistics" ("date");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- 删除索引
        DROP INDEX IF EXISTS "idx_midscene_sessions_session_id";
        DROP INDEX IF EXISTS "idx_midscene_sessions_user_id";
        DROP INDEX IF EXISTS "idx_midscene_sessions_status";
        DROP INDEX IF EXISTS "idx_midscene_sessions_created_at";

        DROP INDEX IF EXISTS "idx_midscene_agent_logs_session_id";
        DROP INDEX IF EXISTS "idx_midscene_agent_logs_agent_name";
        DROP INDEX IF EXISTS "idx_midscene_agent_logs_status";
        DROP INDEX IF EXISTS "idx_midscene_agent_logs_started_at";

        DROP INDEX IF EXISTS "idx_midscene_uploaded_files_session_id";
        DROP INDEX IF EXISTS "idx_midscene_uploaded_files_status";
        DROP INDEX IF EXISTS "idx_midscene_uploaded_files_uploaded_at";

        DROP INDEX IF EXISTS "idx_midscene_templates_category";
        DROP INDEX IF EXISTS "idx_midscene_templates_is_active";
        DROP INDEX IF EXISTS "idx_midscene_templates_is_public";
        DROP INDEX IF EXISTS "idx_midscene_templates_created_by";

        DROP INDEX IF EXISTS "idx_midscene_statistics_date";

        -- 删除表
        DROP TABLE IF EXISTS "midscene_statistics";
        DROP TABLE IF EXISTS "midscene_templates";
        DROP TABLE IF EXISTS "midscene_uploaded_files";
        DROP TABLE IF EXISTS "midscene_agent_logs";
        DROP TABLE IF EXISTS "midscene_sessions";
    """
