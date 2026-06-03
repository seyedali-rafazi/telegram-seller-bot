# handlers/states/youtube/task.py

import os
import asyncio
from core.database import (
    is_vip,
    decrement_yt_downloads,
    get_cached_video,
    increment_yt_video_view,
)
from services.youtube import (
    download_youtube_video,
    download_youtube_audio,
    get_video_info,
    uploaded_at_from_video_info,
    get_video_filesize,
)
from services.zip_utils import make_zip_single

from .config import (
    telegram_normal_semaphore,
    telegram_vip_semaphore,
    MAX_NORMAL_DOWNLOADS,
    MAX_VIP_DOWNLOADS,
)
from core.yt_moderation import (
    MSG_BLOCKED_CHANNEL,
    check_video_info_allowed,
)
from .helpers import (
    extract_yt_id,
    send_cached_files,
    format_duration,
    format_size,
    get_waiting_count,
    process_and_send_document_parts,
    process_and_send_video_parts,
    upload_audio_to_storage_once,
    send_audio_once,
    save_to_global_cache,
)

MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024


def _effective_format(format_type: str, delivery_mode: str) -> str:
    if format_type == "audio":
        return "audio_zip"
    if format_type == "video" and delivery_mode == "zip":
        return "video_zip"
    return format_type


def _use_youtube_cache(format_type: str, delivery_mode: str) -> bool:
    if format_type == "video" and delivery_mode == "video":
        return False
    return True


async def background_yt_download(
    context,
    url: str,
    chat_id: str,
    format_type: str,
    quality: str = "480",
    delivery_mode: str = "zip",
):
    video_id = extract_yt_id(url)
    effective_format = _effective_format(format_type, delivery_mode)
    cache_key = f"{video_id}_{effective_format}_telegram_{quality}"

    if _use_youtube_cache(format_type, delivery_mode):
        cached_files = await get_cached_video(cache_key)

        if cached_files:
            info_cached = await asyncio.to_thread(get_video_info, url)
            if not await check_video_info_allowed(info_cached):
                await context.bot.send_message(
                    chat_id=chat_id, text=MSG_BLOCKED_CHANNEL
                )
                await decrement_yt_downloads(chat_id)
                return

            await send_cached_files(
                context,
                chat_id,
                cached_files,
                effective_format,
            )

            await increment_yt_video_view(cache_key)
            await save_to_global_cache(
                cache_key,
                video_id,
                cached_files,
                title=info_cached.get("title") if info_cached else None,
                channel_name=info_cached.get("uploader") if info_cached else None,
                uploaded_at=uploaded_at_from_video_info(info_cached),
            )
            return

    info = await asyncio.to_thread(get_video_info, url)

    if not await check_video_info_allowed(info):
        await context.bot.send_message(chat_id=chat_id, text=MSG_BLOCKED_CHANNEL)
        await decrement_yt_downloads(chat_id)
        return

    estimated_size = None
    try:
        if format_type == "video":
            format_selector = (
                f"best[height<={quality}][ext=mp4]/best[height<={quality}]/best"
            )
            estimated_size = await asyncio.to_thread(
                get_video_filesize, url, format_selector
            )
        else:
            estimated_size = await asyncio.to_thread(
                get_video_filesize, url, "bestaudio/best"
            )

        if estimated_size and estimated_size > MAX_FILE_BYTES:
            size_mb = round(estimated_size / (1024 * 1024), 1)
            limit_mb = round(MAX_FILE_BYTES / (1024 * 1024), 1)
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"❌ حجم فایل حدود {size_mb} مگابایت است.\n\n"
                    f"حداکثر حجم مجاز تلگرام {limit_mb} مگابایت است."
                ),
            )
            await decrement_yt_downloads(chat_id)
            return
    except Exception as e:
        print(f"⚠️ Error checking filesize: {e}")

    if info and info.get("thumbnail"):
        duration_text = format_duration(info.get("duration", 0))
        size_text = format_size(estimated_size) if estimated_size else None
        caption = (
            f"🎥 **{info['title']}**\n"
            f"👤 کانال: {info['uploader']}\n"
            f"⏱ زمان: {duration_text}\n"
            + (f"💾 حجم فایل: {size_text}\n" if size_text else "")
            + "\n"
            f"⏳ در حال آماده‌سازی برای دانلود..."
        )
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=info["thumbnail"],
                caption=caption,
                parse_mode="Markdown",
            )
        except Exception:
            pass

    user_is_vip = await is_vip(chat_id)
    active_semaphore = (
        telegram_vip_semaphore if user_is_vip else telegram_normal_semaphore
    )
    max_concurrent = MAX_VIP_DOWNLOADS if user_is_vip else MAX_NORMAL_DOWNLOADS
    waiting_count = get_waiting_count(active_semaphore, max_concurrent)

    if waiting_count > 0:
        status_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ درخواست شما ثبت شد.\nسرور شلوغ است. در صف قرار گرفتید...",
        )
    else:
        status_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ درخواست شما ثبت شد و پردازش آغاز گردید...",
        )

    try:
        async with active_semaphore:
            progress_dict = {"text": "شروع پردازش...", "is_finished": False}

            async def update_progress_message():
                last_text = ""
                while not progress_dict.get("is_finished", False):
                    current_text = progress_dict.get("text", "")
                    if current_text and current_text != last_text:
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=status_msg.message_id,
                                text=f"⏳ در حال پردازش...\n\n{current_text}",
                            )
                            last_text = current_text
                        except Exception:
                            pass
                    await asyncio.sleep(5)

            updater_task = asyncio.create_task(update_progress_message())

            try:
                if format_type == "video":
                    downloaded_files = []
                    zip_artifacts = []
                    raw_file = None

                    try:
                        raw_file = await asyncio.to_thread(
                            download_youtube_video,
                            url,
                            quality,
                            progress_dict,
                            MAX_FILE_BYTES,
                        )
                        progress_dict["is_finished"] = True

                        if raw_file == "TOO_LARGE":
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text="❌ حجم فایل بیش از 2 گیگابایت است.",
                            )
                            await decrement_yt_downloads(chat_id)
                            return

                        if raw_file and isinstance(raw_file, str):
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=status_msg.message_id,
                                text="⏳ در حال آماده‌سازی ویدیو...",
                            )

                            if delivery_mode == "zip":
                                await context.bot.send_message(
                                    chat_id=chat_id,
                                    text="📦 در حال ساخت ZIP...",
                                )
                                zip_basename = f"youtube_{video_id}_{quality}p"
                                out_dir = os.path.dirname(raw_file) or "."
                                zip_path = os.path.join(out_dir, f"{zip_basename}.zip")
                                await asyncio.to_thread(
                                    make_zip_single, raw_file, zip_path
                                )
                                zip_artifacts.append(zip_path)
                                archive_basename = zip_basename
                                split_method = "single"
                                result = [zip_path]
                            else:
                                archive_basename = ""
                                split_method = "single"
                                result = [raw_file]

                            downloaded_files.extend(result)

                            if delivery_mode == "zip":
                                await process_and_send_document_parts(
                                    context,
                                    chat_id,
                                    result,
                                    label=f"Video ID: {video_id}",
                                    cache_key=cache_key,
                                    archive_basename=archive_basename,
                                    split_method=split_method,
                                    video_id=video_id,
                                    title=info.get("title") if info else None,
                                    channel_name=info.get("uploader") if info else None,
                                    uploaded_at=uploaded_at_from_video_info(info),
                                )
                            else:
                                await process_and_send_video_parts(
                                    context,
                                    chat_id,
                                    result,
                                    video_id=video_id,
                                    cache_key=cache_key,
                                    title=info.get("title") if info else None,
                                    channel_name=info.get("uploader") if info else None,
                                    uploaded_at=uploaded_at_from_video_info(info),
                                )
                        else:
                            raise Exception("Download failed")

                    except Exception as send_err:
                        print(f"❌ Video error: {send_err}")
                        error_text = str(send_err).lower()
                        if raw_file == "TOO_LARGE" or any(
                            k in error_text
                            for k in (
                                "too large",
                                "max-filesize",
                                "size",
                                "exceed",
                                "limit",
                            )
                        ):
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text="❌ حجم فایل بیشتر از 2 گیگابایت است.",
                            )
                        else:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text="❌ خطا در دانلود یا ارسال ویدیو. لطفاً بعداً دوباره تلاش کنید.",
                            )
                        await decrement_yt_downloads(chat_id)

                    finally:
                        for file_path in downloaded_files:
                            if os.path.exists(file_path):
                                try:
                                    await asyncio.to_thread(os.remove, file_path)
                                except Exception:
                                    pass
                        for z in zip_artifacts:
                            if z and isinstance(z, str) and os.path.exists(z):
                                try:
                                    await asyncio.to_thread(os.remove, z)
                                except Exception:
                                    pass

                elif format_type == "audio":
                    file_path = None
                    try:
                        file_path = await asyncio.to_thread(
                            download_youtube_audio,
                            url,
                            MAX_FILE_BYTES,
                        )
                        progress_dict["is_finished"] = True

                        if file_path == "TOO_LARGE":
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text="❌ حجم فایل صوتی بیش از 2 گیگابایت است.",
                            )
                            await decrement_yt_downloads(chat_id)
                            return

                        if (
                            file_path
                            and isinstance(file_path, str)
                            and os.path.exists(file_path)
                        ):
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text="📤 در حال آپلود فایل صوتی...",
                            )
                            caption = f"Audio ID: {video_id}"
                            file_id = await upload_audio_to_storage_once(
                                context, file_path, caption
                            )
                            if not await send_audio_once(context, chat_id, file_id):
                                await context.bot.send_message(
                                    chat_id=chat_id,
                                    text=(
                                        "⚠️ ممکن است فایل ارسال شده باشد؛ "
                                        "لطفاً چت را بررسی کنید."
                                    ),
                                )
                            await save_to_global_cache(
                                cache_key,
                                video_id,
                                [file_id],
                                title=info.get("title") if info else None,
                                channel_name=info.get("uploader") if info else None,
                                uploaded_at=uploaded_at_from_video_info(info),
                            )
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text="✅ پایان عملیات ارسال.",
                            )
                        else:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text="❌ دانلود شکست خورد.",
                            )
                            await decrement_yt_downloads(chat_id)

                    except Exception as send_err:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"❌ خطا: {str(send_err)}",
                        )
                        await decrement_yt_downloads(chat_id)

                    finally:
                        if file_path and os.path.exists(file_path):
                            try:
                                await asyncio.to_thread(os.remove, file_path)
                            except Exception:
                                pass

            except Exception as e:
                progress_dict["is_finished"] = True
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ خطا: {str(e)}",
                )
                await decrement_yt_downloads(chat_id)

            finally:
                progress_dict["is_finished"] = True
                updater_task.cancel()

    except Exception as e:
        print(f"Semaphore Error: {e}")
        await decrement_yt_downloads(chat_id)
