# handlers/states/state_insta.py

import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from services.instagram import download_instagram
from core.database import log_upload_success

INSTA_SEMAPHORE = asyncio.Semaphore(5)


async def handle_insta_state(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    step: str,
    text: str,
    chat_id: str,
    state_data: dict,
):
    if step == "waiting_ig_link":
        if "instagram.com" not in text:
            await update.message.reply_text("❌ لینک نامعتبر است.")
            return

        asyncio.create_task(
            background_download_insta_link(context, chat_id, text)
        )


async def background_download_insta_link(context, chat_id, link: str):
    processing_msg = await context.bot.send_message(
        chat_id=chat_id,
        text="⏳ در حال دانلود از اینستاگرام... لطفا کمی صبر کنید",
    )

    async with INSTA_SEMAPHORE:
        file_path = None
        try:
            file_path = await asyncio.wait_for(
                asyncio.to_thread(download_instagram, link), timeout=60.0
            )

            if file_path and os.path.exists(file_path):
                try:
                    await processing_msg.edit_text(
                        "📤 دانلود تکمیل شد! در حال ارسال..."
                    )
                except Exception:
                    pass

                if file_path.endswith(".mp4"):
                    await context.bot.send_video(chat_id=chat_id, video=file_path)
                else:
                    await context.bot.send_document(
                        chat_id=chat_id, document=file_path
                    )
                await log_upload_success("instagram", chat_id)

                try:
                    await processing_msg.delete()
                except Exception:
                    pass
            else:
                await processing_msg.edit_text(
                    "❌ دانلود شکست خورد. ممکن است پیج پرایوت باشد."
                )

        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                "⏳ زمان درخواست به پایان رسید (بیش از ۶۰ ثانیه)."
            )
        except Exception as e:
            print(f"Insta DL Error: {e}")
            await processing_msg.edit_text("❌ خطای غیرمنتظره‌ای رخ داد.")
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass


async def handle_insta_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
