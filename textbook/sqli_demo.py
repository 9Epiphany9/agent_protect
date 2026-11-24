"""教材原理复现：控制指令与数据混淆（SQL 注入）及“指令-数据分离”（参数化查询）。

对应谢希仁《计算机网络》第 8 版第 7 章（网络安全）对应用层攻击的讨论。
本脚本使用 sqlite3 内存数据库，演示：
  1. 字符串拼接：用户输入被当作 SQL 指令执行（注入成功）；
  2. 参数化查询：用户输入始终只是数据（注入失败）。
这正是 LLM 提示注入的经典对应物：System Prompt 与用户输入同处一个自然语言通道。
"""
import sqlite3


def build_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users(name TEXT, secret TEXT)")
    conn.executemany(
        "INSERT INTO users VALUES(?, ?)",
        [("alice", "alice-secret"), ("bob", "bob-secret")],
    )
    return conn


def vulnerable_query(conn, name: str):
    sql = f"SELECT name, secret FROM users WHERE name = '{name}'"  # 指令与数据拼接
    return sql, conn.execute(sql).fetchall()


def safe_query(conn, name: str):
    sql = "SELECT name, secret FROM users WHERE name = ?"  # 指令与数据分离
    return sql, conn.execute(sql, (name,)).fetchall()


if __name__ == "__main__":
    conn = build_db()
    for label, payload in [("正常输入", "alice"), ("注入载荷", "x' OR '1'='1")]:
        print(f"--- {label}: {payload!r}")
        sql, rows = vulnerable_query(conn, payload)
        print(f"[拼接]   SQL={sql}\n         返回 {len(rows)} 行: {rows}")
        sql, rows = safe_query(conn, payload)
        print(f"[参数化] SQL={sql}\n         返回 {len(rows)} 行: {rows}")
