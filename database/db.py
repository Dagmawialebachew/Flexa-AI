import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from utils.logger import logger

class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database connection pool established")

            # Ensure tables exist
            async with self.pool.acquire() as conn:
                await self._create_tables(conn)
                # await self.reset_schema()

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def _create_tables(self, conn: asyncpg.Connection):
        # Enable pgcrypto for UUID generation
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

        # USERS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                language TEXT CHECK (language IN ('en','am')) DEFAULT 'en',
                credit_balance INT DEFAULT 0,
                total_generations INT DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMPTZ DEFAULT now(),
                last_active TIMESTAMPTZ DEFAULT now()
            );
        """)

        # STYLES
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS styles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name_en TEXT NOT NULL,
                name_am TEXT,
                description_en TEXT,
                description_am TEXT,
                prompt_template TEXT NOT NULL,
                credit_cost INT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                display_order INT DEFAULT 0
            );
        """)
        
       

        # GENERATIONS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                style_id UUID REFERENCES styles(id) ON DELETE SET NULL,
                status TEXT CHECK (status IN ('pending','processing','completed','failed','manual_queue')) DEFAULT 'pending',
                original_photo_url TEXT,
                generated_photo_url TEXT,
                credits_spent INT DEFAULT 0,
                error_message TEXT,
                api_provider TEXT CHECK (api_provider IN ('gemini','banana','manual')),
                processing_time_ms INT,
                created_at TIMESTAMPTZ DEFAULT now(),
                completed_at TIMESTAMPTZ
            );
        """)

        # PAYMENTS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                package_type TEXT NOT NULL,
                amount_birr INT NOT NULL,
                credits_amount INT NOT NULL,
                screenshot_url TEXT,
                ocr_extracted_data JSONB,
                status TEXT CHECK (status IN ('pending','approved','rejected')) DEFAULT 'pending',
                admin_id BIGINT REFERENCES users(id),
                admin_note TEXT,
                submitted_at TIMESTAMPTZ DEFAULT now(),
                reviewed_at TIMESTAMPTZ
            );
        """)

        # CREDIT TRANSACTIONS
        await conn.execute(""" CREATE TABLE IF NOT EXISTS credit_transactions ( id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id BIGINT REFERENCES users(id) ON DELETE CASCADE, amount INT NOT NULL, transaction_type TEXT CHECK (transaction_type IN ('bonus','purchase','generation','admin_adjustment')), reference_id UUID, balance_after INT NOT NULL, note TEXT, created_at TIMESTAMPTZ DEFAULT now() ); """)
        await conn.execute(""" ALTER TABLE styles ADD COLUMN IF NOT EXISTS preview_image_url TEXT; ALTER TABLE styles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now(); """)
        await conn.execute(""" ALTER TABLE payments
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();
 """)
        await conn.execute(""" ALTER TABLE users
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();
 """)
        

        logger.info("Ensured required tables exist")
        
    
    async def reset_schema(self):
        """
        Drops all tables in the schema and recreates them.
        WARNING: This will delete ALL data permanently.
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Drop tables in reverse dependency order
                await conn.execute("DROP TABLE IF EXISTS credit_transactions CASCADE;")
                await conn.execute("DROP TABLE IF EXISTS payments CASCADE;")
                await conn.execute("DROP TABLE IF EXISTS generations CASCADE;")
                await conn.execute("DROP TABLE IF EXISTS styles CASCADE;")
                await conn.execute("DROP TABLE IF EXISTS users CASCADE;")

                # Recreate tables
                await self._create_tables(conn)

        logger.warning("Schema has been reset: all tables dropped and recreated")

    async def create_user(self, user_id: int, username: Optional[str], first_name: str, language: str, bonus_credits: int) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("""
                    INSERT INTO users (id, username, first_name, language, credit_balance, is_admin)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE SET
                        username = EXCLUDED.username,
                        last_active = now()
                    RETURNING *
                """, user_id, username, first_name, language, bonus_credits, False)

                if user['credit_balance'] == bonus_credits:
                    await conn.execute("""
                        INSERT INTO credit_transactions (user_id, amount, transaction_type, balance_after, note)
                        VALUES ($1, $2, $3, $4, $5)
                    """, user_id, bonus_credits, 'bonus', bonus_credits, 'Welcome bonus')

                return dict(user)
            
    
    async def user_has_active_generation(self, user_id: int) -> bool:
        """
        Check if the user has any generation still pending/processing/manual_queue.
        Returns True if they should not be allowed to start another.
        """
        async with self.pool.acquire() as conn:
            cnt = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM generations
                WHERE user_id = $1 
                  AND status IN ('pending','processing','manual_queue')
                """,
                user_id
            )
            return (cnt or 0) > 0

    
    
    async def create_style(
        self,
        name_en: str,
        name_am: Optional[str],
        description_en: Optional[str],
        description_am: Optional[str],
        prompt_template: str,
        credit_cost: int,
        preview_image_url: Optional[str] = None,
        is_active: bool = True,
        display_order: int = 0,
    ) -> int:
        """
        Insert a new style into the styles table and return its ID.
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                style = await conn.fetchrow(
                    """
                    INSERT INTO styles (
                        name_en,
                        name_am,
                        description_en,
                        description_am,
                        prompt_template,
                        credit_cost,
                        preview_image_url,
                        is_active,
                        display_order,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, now())
                    RETURNING id
                    """,
                    name_en,
                    name_am,
                    description_en,
                    description_am,
                    prompt_template,
                    credit_cost,
                    preview_image_url,
                    is_active,
                    display_order,
                )
                return style["id"]


    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            return dict(user) if user else None

    async def update_user_language(self, user_id: int, language: str):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET language = $1 WHERE id = $2", language, user_id)

    async def update_last_active(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET last_active = now() WHERE id = $1", user_id)

    async def get_active_styles(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            styles = await conn.fetch("SELECT * FROM styles WHERE is_active = true ORDER BY display_order ASC")
            return [dict(style) for style in styles]

    async def get_style(self, style_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            style = await conn.fetchrow("SELECT * FROM styles WHERE id = $1", style_id)
            return dict(style) if style else None

    async def deduct_credits(self, user_id: int, amount: int) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("UPDATE users SET credit_balance = credit_balance - $1, total_generations = total_generations + 1 WHERE id = $2 AND credit_balance >= $1 RETURNING credit_balance", amount, user_id)
                if not user:
                    return False
                await conn.execute("INSERT INTO credit_transactions (user_id, amount, transaction_type, balance_after, note) VALUES ($1, $2, $3, $4, $5)", user_id, -amount, 'generation', user['credit_balance'], 'Photo generation')
                return True

    async def add_credits(self, user_id: int, amount: int, transaction_type: str) -> int:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("UPDATE users SET credit_balance = credit_balance + $1 WHERE id = $2 RETURNING credit_balance", amount, user_id)
                new_balance = user['credit_balance']
                await conn.execute("INSERT INTO credit_transactions (user_id, amount, transaction_type, balance_after) VALUES ($1, $2, $3, $4)", user_id, amount, transaction_type, new_balance)
                return new_balance

    async def create_generation(self, user_id: int, style_id: str, original_photo_url: str, credits_spent: int) -> str:
        async with self.pool.acquire() as conn:
            gen_id = await conn.fetchval("INSERT INTO generations (user_id, style_id, original_photo_url, status, credits_spent) VALUES ($1, $2, $3, $4, $5) RETURNING id", user_id, style_id, original_photo_url, 'pending', credits_spent)
            return str(gen_id)

    async def update_generation(self, generation_id: str, status: str, generated_photo_url: Optional[str] = None, error_message: Optional[str] = None, api_provider: Optional[str] = None, processing_time_ms: Optional[int] = None):
        async with self.pool.acquire() as conn:
            completed_at = datetime.utcnow() if status in ['completed', 'failed'] else None
            await conn.execute("UPDATE generations SET status = $1, generated_photo_url = $2, error_message = $3, api_provider = $4, processing_time_ms = $5, completed_at = $6 WHERE id = $7", status, generated_photo_url, error_message, api_provider, processing_time_ms, completed_at, generation_id)

    async def get_generation(self, generation_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            gen = await conn.fetchrow("SELECT * FROM generations WHERE id = $1", generation_id)
            return dict(gen) if gen else None

    async def get_manual_queue(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            gens = await conn.fetch("SELECT g.*, u.first_name, u.username, s.name_en as style_name FROM generations g JOIN users u ON g.user_id = u.id JOIN styles s ON g.style_id = s.id WHERE g.status = 'manual_queue' ORDER BY g.created_at ASC LIMIT 10")
            return [dict(g) for g in gens]

    async def create_payment(
        self,
        user_id: int,
        package_type: str,
        amount_birr: int,
        credits_amount: int,
        screenshot_url: str,
        ocr_data: Optional[Dict] = None,
        status: str = "pending"
    ) -> str:
        async with self.pool.acquire() as conn:
            pid = await conn.fetchval(
                """
                INSERT INTO payments (
                    user_id, package_type, amount_birr, credits_amount,
                    screenshot_url, ocr_extracted_data, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                user_id, package_type, amount_birr, credits_amount,
                screenshot_url, json.dumps(ocr_data) if ocr_data else None, status
            )
            return str(pid)


    async def get_pending_payments(self, limit: int = 10) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            payments = await conn.fetch("SELECT p.*, u.first_name, u.username FROM payments p JOIN users u ON p.user_id = u.id WHERE p.status = 'pending' ORDER BY p.submitted_at ASC LIMIT $1", limit)
            return [dict(p) for p in payments]

    async def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            p = await conn.fetchrow("SELECT * FROM payments WHERE id = $1", payment_id)
            return dict(p) if p else None

    async def approve_payment(self, payment_id: str, admin_id: int) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                payment = await conn.fetchrow("UPDATE payments SET status = 'approved', admin_id = $1, reviewed_at = now() WHERE id = $2 AND status = 'pending' RETURNING user_id, credits_amount", admin_id, payment_id)
                if not payment:
                    return False
                await self.add_credits(payment['user_id'], payment['credits_amount'], 'purchase')
                return True

    async def reject_payment(self, payment_id: str, admin_id: int, note: str):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE payments SET status = 'rejected', admin_id = $1, admin_note = $2, reviewed_at = now() WHERE id = $3", admin_id, note, payment_id)

    async def get_stats(self) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            total_gens = await conn.fetchval("SELECT COUNT(*) FROM generations")
            pending_payments = await conn.fetchval("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
            manual_queue = await conn.fetchval("SELECT COUNT(*) FROM generations WHERE status = 'manual_queue'")
            return {'total_users': total_users, 'total_generations': total_gens, 'pending_payments': pending_payments, 'manual_queue': manual_queue}

    async def get_all_users(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            users = await conn.fetch("SELECT id, username, first_name, language, credit_balance, total_generations, is_active, joined_at FROM users ORDER BY joined_at DESC LIMIT $1", limit)
            return [dict(u) for u in users]
        
    
    async def get_all_styles(self) -> List[Dict[str, Any]]:
        """
        Return all styles (no filtering). Each row is returned as a dict.
        Useful for admin listing / browsing.
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM styles ORDER BY display_order ASC, name_en ASC")
            return [dict(r) for r in rows]

    async def get_styles_paginated(self, page: int = 0, page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Return a page of styles for listing UIs.
        - page: zero-based page index
        - page_size: number of items per page
        """
        offset = page * page_size
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM styles ORDER BY display_order ASC, name_en ASC LIMIT $1 OFFSET $2",
                page_size, offset
            )
            return [dict(r) for r in rows]

    # You already have get_style; keep it as-is. If you want a defensive wrapper:
    async def get_style(self, style_id: str) -> Optional[Dict[str, Any]]:
        """
        Return a single style by id (UUID string). Returns None if not found.
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM styles WHERE id = $1", style_id)
            return dict(row) if row else None
    
    async def get_manual_queue_paginated(
        self, 
        page: int = 0, 
        page_size: int = 5
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Return a page of manual-queue generations and the total count.
        Manual queue statuses: 'manual_queue' and maybe 'failed' if you want to include retries.
        Returns (rows_list, total_count)
        """
        offset = page * page_size
        async with self.pool.acquire() as conn:
            # total count
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM generations WHERE status = 'manual_queue'"
            )
            rows = await conn.fetch(
                """
                SELECT g.*, u.first_name, u.username, s.name_en as style_name, s.prompt_template
                FROM generations g
                LEFT JOIN users u ON g.user_id = u.id
                LEFT JOIN styles s ON g.style_id = s.id
                WHERE g.status = 'manual_queue'
                ORDER BY g.created_at ASC
                LIMIT $1 OFFSET $2
                """,
                page_size, offset
            )
            return [dict(r) for r in rows], (total or 0)

    async def get_manual_task(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """
        Return a single generation row with joined user and style info for admin manual processing.
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT g.*, u.first_name, u.username, s.name_en as style_name, s.prompt_template
                FROM generations g
                LEFT JOIN users u ON g.user_id = u.id
                LEFT JOIN styles s ON g.style_id = s.id
                WHERE g.id = $1
                """,
                generation_id
            )
            return dict(row) if row else None
        
    
        
        # in db.py or wherever your Database class lives
    async def get_pending_payments_paginated(
        self,
        page: int = 0,
        page_size: int = 5
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Return a page of pending payments and the total count.
        Payment statuses: 'pending' (waiting for admin review).
        Returns (rows_list, total_count)
        """
        offset = page * page_size
        async with self.pool.acquire() as conn:
            # total count
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM payments WHERE status = 'pending'"
            )
            rows = await conn.fetch(
                """
                SELECT p.*, u.first_name, u.username
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.id
                WHERE p.status = 'pending'
                ORDER BY p.created_at ASC
                LIMIT $1 OFFSET $2
                """,
                page_size, offset
            )
            return [dict(r) for r in rows], (total or 0)

    
    
    async def get_users_paginated(
        self,
        page: int = 0,
        page_size: int = 5
    ) -> tuple[list[dict], int]:
        """
        Return a page of users and the total count.
        Returns (rows_list, total_count).
        """
        offset = page * page_size
        async with self.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM users")
            rows = await conn.fetch(
                """
                SELECT u.*, 
                    (SELECT COUNT(*) FROM generations g WHERE g.user_id = u.id) AS total_generations
                FROM users u
                ORDER BY u.created_at ASC
                LIMIT $1 OFFSET $2
                """,
                page_size, offset
            )
            return [dict(r) for r in rows], (total or 0)
        
    
    async def update_style(self, style_id: int, **fields) -> None:
        """
        Update an existing style by ID.
        """
        query = """
            UPDATE styles
            SET name_en = $1,
                name_am = $2,
                description_en = $3,
                description_am = $4,
                prompt_template = $5,
                credit_cost = $6,
                is_active = $7,
                display_order = $8,
                preview_image_url = $9
            WHERE id = $10
        """
        await self.pool.execute(
            query,
            fields.get("name_en"),
            fields.get("name_am"),
            fields.get("description_en"),
            fields.get("description_am"),
            fields.get("prompt_template"),
            fields.get("credit_cost"),
            fields.get("is_active"),
            fields.get("display_order"),
            fields.get("preview_image_url"),
            style_id,
        )

    async def delete_style(self, style_id: str) -> None:
        query = "DELETE FROM styles WHERE id = $1"
        await self.pool.execute(query, style_id)



    


