import sqlite3 as sql
from typing import Optional


def init_db():
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reason_blocks(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reason_title TEXT NOT NULL,
                    is_fraud BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unp TEXT UNIQUE NOT NULL,
                    status_block BOOLEAN DEFAULT FALSE,
                    current_reason_id INTEGER NULL,
                    FOREIGN KEY (current_reason_id) REFERENCES reason_blocks (id) ON DELETE SET NULL
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS log_blocks_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_id INTEGER,
                    status_block BOOLEAN NOT NULL,
                    reason_id INTEGER NULL,
                    client_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reason_id) REFERENCES reason_blocks (id) ON DELETE SET NULL,
                    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE,
                    FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE SET NULL
                )
            """)

            cur.execute("SELECT COUNT(*) FROM users")
            if cur.fetchone()[0] == 0:
                test_user = ('Тестовый пользователь', )
                cur.execute("INSERT INTO users (username) VALUES (?)", test_user)

            cur.execute("SELECT COUNT(*) FROM reason_blocks")
            if cur.fetchone()[0] == 0:
                reasons = [
                    ('Подозрение в мошенничестве', True),
                    ('Мошенничество', True),
                    ('Неверные реквизиты', False)
                ]
                cur.executemany("INSERT INTO reason_blocks(reason_title, is_fraud) VALUES (?, ?)", reasons)

            cur.execute("CREATE INDEX IF NOT EXISTS idx_clients_unp ON clients(unp);")
            conn.commit()

        except Exception as e:
            print(f'При инициализации базы данных возникла ошибка: {e}')
        finally:
            cur.close()


###########
# CLIENTS #
###########

def select_client(unp):
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                """
                    SELECT clients.id, clients.unp, clients.status_block, 
                    clients.current_reason_id, reason_blocks.reason_title, reason_blocks.is_fraud
                    FROM clients LEFT JOIN reason_blocks ON clients.current_reason_id = reason_blocks.id
                    WHERE unp = ?
                """, (unp, )
            )
            client = cur.fetchone()
            if client:
                if client[2] == 1:
                    response = {
                            'id': client[0],
                            'unp': client[1],
                            'status_block': True,
                            'current_reason': {
                                'current_reason_id': client[3],
                                'reason_title': client[4],
                                'is_fraud': True if client[5] == 1 else False
                            }
                    }
                else:
                    response = {
                            'id': client[0],
                            'unp': client[1],
                            'status_block': False
                    }
                return response
            return None
        except Exception as e:
            print(e)
        finally:
            cur.close()


def select_clients():
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                """
                    SELECT clients.id, clients.unp, clients.status_block, 
                    clients.current_reason_id, reason_blocks.reason_title, reason_blocks.is_fraud
                    FROM clients LEFT JOIN reason_blocks ON clients.current_reason_id = reason_blocks.id
                """
            )

            clients = cur.fetchall()
            response = []
            for client in clients:
                if client[2] == 1:
                    response.append(
                        {
                            'id': client[0],
                            'unp': client[1],
                            'status_block': True,
                            'current_reason': {
                                'current_reason_id': client[3],
                                'reason_title': client[4],
                                'is_fraud': True if client[5] == 1 else False
                            }
                        })
                else:
                    response.append(
                        {
                            'id': client[0],
                            'unp': client[1],
                            'status_block': False
                        })
            if response:
                return response
            return None
        except Exception as e:
            print(e)
        finally:
            cur.close()


def create_client(unp: str):
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute("""INSERT INTO clients (unp) VALUES (?);""", (unp, ))
            conn.commit()
            return True
        except Exception as e:
            print(e)
        finally:
            cur.close()


###########
# REASONS #
###########

def create_reason(reason_title, is_fraud):
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO reason_blocks (reason_title, is_fraud) VALUES (?, ?);
                """, (reason_title, is_fraud)
            )
            conn.commit()
            return True
        except Exception as e:
            print('Ошибка при создании причины блокировки:', e)
            return False
        finally:
            cur.close()


def select_reasons():
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, reason_title, is_fraud FROM reason_blocks")
            reasons = cur.fetchall()
            if not reasons:
                return None
            response = []
            for reason in reasons:
                response.append(
                    {
                        'id': reason[0],
                        'reason_title': reason[1],
                        'is_fraud': reason[2]
                    })
            if response:
                return response
            return None
        except Exception as e:
            print(e)
        finally:
            cur.close()


def select_reason(reason_id: Optional[int] = None, reason_title: Optional[str] = None):
    with sql.connect('db_blocking_payments.db') as conn:
        try:

            if reason_id is None and reason_title is None:
                raise ValueError("Должен быть указан reason_id или reason_title")

            cur = conn.cursor()

            if reason_id is not None:
                cur.execute("SELECT id, reason_title, is_fraud FROM reason_blocks WHERE id=?", (reason_id, ))
            elif reason_title is not None:
                cur.execute("SELECT id, reason_title, is_fraud FROM reason_blocks WHERE reason_title=?",
                            (reason_title,))

            reason = cur.fetchone()
            if not reason:
                return None
            response = {
                    'id': reason[0],
                    'reason_title': reason[1],
                    'is_fraud': reason[2]
                    }
            if response:
                return response
            return None
        except Exception as e:
            print(e)
        finally:
            cur.close()


################
# блок\разблок #
################


def block(client_id, reason_id, user_id):
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()

            cur.execute("""UPDATE clients SET status_block = TRUE, current_reason_id = ? WHERE id = ?""",
                        (reason_id, client_id))

            # логирование
            cur.execute("""
                INSERT INTO log_blocks_payments (status_block, reason_id, client_id, author_id)
                VALUES (TRUE, ?, ?, ?)
            """, (reason_id, client_id, user_id))
            conn.commit()

        except Exception as e:
            print(e)
        finally:
            cur.close()


def unblock(client_id, user_id):
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()

            cur.execute("""UPDATE clients SET status_block = FALSE, current_reason_id = NULL WHERE id = ?""",
                        (client_id, ))

            # логирование
            cur.execute("""
                INSERT INTO log_blocks_payments (status_block, client_id, author_id)
                VALUES (FALSE, ?, ?)
            """, (client_id, user_id))
            conn.commit()

        except Exception as e:
            print(e)
        finally:
            cur.close()


def select_log(client_id):
    with sql.connect('db_blocking_payments.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    log_blocks_payments.id, 
                    log_blocks_payments.status_block,
                    log_blocks_payments.created_at,
                    reason_blocks.id, 
                    reason_blocks.reason_title, 
                    reason_blocks.is_fraud,
                    clients.id, 
                    clients.unp, 
                    users.id, 
                    users.username
                FROM log_blocks_payments 
                LEFT JOIN reason_blocks ON log_blocks_payments.reason_id = reason_blocks.id
                LEFT JOIN clients ON log_blocks_payments.client_id = clients.id
                LEFT JOIN users ON log_blocks_payments.author_id = users.id
                WHERE log_blocks_payments.client_id = ?
                ORDER BY log_blocks_payments.created_at DESC
            """, (client_id,))

            logs = cur.fetchall()

            response = []
            for log in logs:

                reason_block = None
                if log[3] is not None:
                    reason_block = {
                        'reason_block_id': log[3],
                        'reason_title': log[4],
                        'is_fraud': True if log[5] == 1 else False
                    }

                user = None
                if log[8] is not None:
                    user = {
                        'user_id': log[8],
                        'username': log[9]
                    }

                response.append({
                    'id': log[0],
                    'status_block': True if log[1] == 1 else False,
                    'created_at': log[2],
                    'reason_block': reason_block,
                    'client': {
                        'client_id': log[6],
                        'client_unp': log[7]
                    },
                    'user': user
                })
            if response:
                return response
            else:
                return None
        except Exception as e:
            print(e)
        finally:
            cur.close()
