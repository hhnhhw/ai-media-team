"""
SQLite 记忆模块
- 对话历史持久化（跨 Streamlit 会话）
- Agent 上下文记忆（LangGraph MemorySaver）
- 生成内容存档（文章 + 配图记录）
"""
import sqlite3
import os

DB_PATH = os.environ.get(
    "MEMORY_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.db"),
)


_SCHEMA_SQL = """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'agent_log')),
            agent_name TEXT DEFAULT '',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            platform TEXT DEFAULT '',
            style TEXT DEFAULT '',
            word_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            search_query TEXT NOT NULL DEFAULT '',
            image_url TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_articles_conv ON articles(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_images_conv ON images(conversation_id);
"""

_schema_initialized = False


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """确保表结构存在（每个进程只执行一次）。

    读函数可能在 init_db() 之前被调用：Streamlit 自上而下执行脚本，
    侧边栏的 list_conversations() 出现在 init_db() 之前，因此在全新数据库
    （例如刚挂载的空持久卷）上会直接抛 "no such table: conversations"。
    把建表收敛到"建立连接"这一步，任何调用方都不必再关心顺序。
    """
    global _schema_initialized
    if _schema_initialized:
        return
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    _schema_initialized = True


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(conn)
    return conn


def init_db():
    """初始化数据库表（保留此入口以兼容旧调用；get_conn() 同样会确保建表）"""
    get_conn().close()


# ── 对话管理 ──────────────────────────────────────────────────

def create_conversation(title: str = "") -> int:
    conn = get_conn()
    cur = conn.execute("INSERT INTO conversations (title) VALUES (?)", (title,))
    conv_id = cur.lastrowid
    conn.commit()
    conn.close()
    return conv_id


def update_conversation_title(conv_id: int, title: str):
    conn = get_conn()
    conn.execute(
        "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, conv_id),
    )
    conn.commit()
    conn.close()


def list_conversations(limit: int = 50) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_conversation(conv_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()


# ── 消息管理 ──────────────────────────────────────────────────

def save_message(conv_id: int, role: str, content: str, agent_name: str = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (conversation_id, role, agent_name, content) VALUES (?, ?, ?, ?)",
        (conv_id, role, agent_name, content),
    )
    conn.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()


def get_messages(conv_id: int, limit: int = 200) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
        (conv_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 内容存档 ──────────────────────────────────────────────────

def save_article(conv_id: int, title: str, content: str, platform: str = "", style: str = "", word_count: int = 0):
    conn = get_conn()
    conn.execute(
        "INSERT INTO articles (conversation_id, title, content, platform, style, word_count) VALUES (?, ?, ?, ?, ?, ?)",
        (conv_id, title, content, platform, style, word_count),
    )
    conn.commit()
    conn.close()


def save_image_record(conv_id: int, search_query: str, image_url: str, source: str = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO images (conversation_id, search_query, image_url, source) VALUES (?, ?, ?, ?)",
        (conv_id, search_query, image_url, source),
    )
    conn.commit()
    conn.close()


# ── Agent 记忆（LangGraph MemorySaver）────────────────────────

def get_agent_memory():
    """获取 Agent 上下文记忆检查点（内存型，会话内有效）"""
    try:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
    except ImportError:
        return None


