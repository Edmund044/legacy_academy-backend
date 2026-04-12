# app/scripts/seed_admin.py
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

async def seed():
    async with AsyncSessionLocal() as db:
        exists = (await db.execute(select(User).where(User.email == "edmundopiyo2@gmail.com"))).scalar_one_or_none()
        plain = "Admin@1234"
        print("PLAIN:", plain)
        print("BYTES:", len(plain.encode("utf-8")))
        hashed = get_password_hash(plain)
        print("HASHED:", hashed)
        if exists:
            print("Admin already exists")
            return
        user = User(
            email="edmundopiyo2@gmail.com",
            password_hash=get_password_hash("Admin@1234"),
            role="technical_director",
            first_name="Edmund",
            last_name="Opiyo",
            is_active=True,
        )
        db.add(user)
        
        await db.commit()
        print("Admin seeded ✅")

asyncio.run(seed())