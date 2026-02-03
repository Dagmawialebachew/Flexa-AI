import asyncio
from database import Database
from config import settings

async def test():
    db = Database(settings.DATABASE_URL)
    await db.connect()
    styles = await db.get_all_styles()
    print(f'✅ Connected! Styles: {len(styles)}')
    await db.close()

asyncio.run(test())



# import asyncio
# import base64
# from services.ai_image import AIImageService
# from config import settings

# async def test_photo_generation():
#     ai_service = AIImageService()

#     # Load a sample photo from disk (simulate Telegram upload)
#     with open("sample.jpg", "rb") as f:
#         image_bytes = f.read()

#     prompt = "Passport photo style, white background, neutral expression"

#     result_bytes, error, provider, processing_time = await ai_service.generate_image(image_bytes, prompt)

#     print(f"Provider: {provider}, Time: {processing_time}ms")

#     if result_bytes:
#         print("✅ Gemini returned an image!")
#         # Save to file so you can inspect it
#         with open("result.jpg", "wb") as out:
#             out.write(result_bytes)
#         print("Result saved as result.jpg")
#     else:
#         print(f"❌ No image returned. Error: {error}")

# asyncio.run(test_photo_generation())




# test.py
# import asyncio
# from services.ai_image import AIImageService

# async def test():
#     ai = AIImageService()
#     with open("sample.jpg", "rb") as f:
#         image_bytes = f.read()
#     prompt = "Passport photo style, white background, neutral expression"
#     result_bytes, error, provider, time_ms = await ai.generate_image(image_bytes, prompt)
#     print("Provider:", provider, "Time(ms):", time_ms, "Error:", error)
#     if result_bytes:
#         with open("result.png", "wb") as out:
#             out.write(result_bytes)
#         print("✅ Saved result.png")
#     else:
#         print("❌ Generation failed:", error)

# if __name__ == "__main__":
#     asyncio.run(test())




# import asyncio
# from database.db import Database
# from config.settings import settings

# async def main():
#     db = Database(settings.DATABASE_URL)
#     await db.connect()

#     # 1. Print all users
#     users = await db.get_all_users(limit=100)  # adjust limit if needed
#     print("=== Users Table ===")
#     for u in users:
#         print(f"ID={u['id']} | username={u['username']} | first_name={u['first_name']} | "
#               f"lang={u['language']} | credits={u['credit_balance']} | total_gens={u['total_generations']}")

#     # 2. Increase credits for a specific user
#     target_user_id = 1131741322   # replace with the actual Telegram user_id
#     amount_to_add = 100          # number of credits to add

#     new_balance = await db.add_credits(target_user_id, amount_to_add, transaction_type='admin_adjustment')
#     print(f"✅ Added {amount_to_add} credits to user {target_user_id}. New balance: {new_balance}")

#     await db.close()

# if __name__ == "__main__":
#     asyncio.run(main())


#Trunculate the users table



# import asyncio
# from database.db import Database
# from config.settings import settings

# async def main():
#     db = Database(settings.DATABASE_URL)
#     await db.connect()

#     # ⚠️ Dangerous operation: truncate all users
#     try:
#         await db.pool.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
#         print("✅ Users table truncated successfully.")
#     except Exception as e:
#         print(f"❌ Failed to truncate users table: {e}")

#     await db.close()

# if __name__ == "__main__":
#     asyncio.run(main())
