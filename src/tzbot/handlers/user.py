"""Everything a normal user can reach.

A factory for the same reason as the admin router: no module-level router
means no shared state between two dispatchers in one process.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.types import CallbackQuery, Message

from tzbot import keyboards as kb
from tzbot.i18n import LANGUAGES, t
from tzbot.storage import Storage
from tzbot.tracker import Tracker


def guess_language(message: Message) -> str:
    """Start people off in their Telegram client language when we support it."""
    code = ((message.from_user.language_code if message.from_user else "") or "")
    code = code.split("-")[0]
    return code if code in LANGUAGES else "en"


async def render_menu(
    target: Message | CallbackQuery, storage: Storage, admin_ids: frozenset[int]
) -> None:
    user_id = target.from_user.id
    language = await storage.get_language(user_id)
    markup = kb.menu(
        language,
        subscribed=await storage.is_subscribed(user_id),
        is_admin=user_id in admin_ids,
    )
    title = t(language, "menu_title")

    if isinstance(target, CallbackQuery):
        if target.message is not None:
            await target.message.edit_text(title, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(title, reply_markup=markup)


async def render_zones(call: CallbackQuery, storage: Storage) -> None:
    language = await storage.get_language(call.from_user.id)
    selected = await storage.zone_filter(call.from_user.id)
    title = t(language, "zones_title")
    if not selected:
        title = f"{title}\n\n{t(language, 'zones_all')}"
    await call.message.edit_text(title, reply_markup=kb.zone_choice(language, selected))
    await call.answer()


def build_router() -> Router:
    router = Router(name="user")

    @router.message(CommandStart())
    @router.message(Command("menu"))
    async def open_menu_command(
        message: Message, storage: Storage, admin_ids: frozenset[int]
    ) -> None:
        await storage.ensure_user(message.from_user.id, guess_language(message))
        await render_menu(message, storage, admin_ids)

    @router.callback_query(F.data == "menu:open")
    async def open_menu(
        call: CallbackQuery, storage: Storage, admin_ids: frozenset[int]
    ) -> None:
        await render_menu(call, storage, admin_ids)

    @router.callback_query(F.data == "subscription:toggle")
    async def toggle_subscription(
        call: CallbackQuery, storage: Storage, admin_ids: frozenset[int]
    ) -> None:
        user_id = call.from_user.id
        subscribed = not await storage.is_subscribed(user_id)
        await storage.set_subscribed(user_id, subscribed)
        language = await storage.get_language(user_id)
        await call.answer(t(language, "subscribed" if subscribed else "unsubscribed"))
        await render_menu(call, storage, admin_ids)

    @router.callback_query(F.data == "language:open")
    async def open_language(call: CallbackQuery, storage: Storage) -> None:
        language = await storage.get_language(call.from_user.id)
        await call.message.edit_text(
            t(language, "choose_language"), reply_markup=kb.language_choice(language)
        )
        await call.answer()

    @router.callback_query(F.data.startswith("language:set:"))
    async def set_language(
        call: CallbackQuery, storage: Storage, admin_ids: frozenset[int]
    ) -> None:
        code = call.data.rsplit(":", 1)[-1]
        if code not in LANGUAGES:
            await call.answer()
            return
        await storage.set_language(call.from_user.id, code)
        await render_menu(call, storage, admin_ids)

    @router.callback_query(F.data == "zone:current")
    async def show_current(call: CallbackQuery, storage: Storage, tracker: Tracker) -> None:
        language = await storage.get_language(call.from_user.id)
        snapshot = tracker.snapshot if tracker else None

        if snapshot is None:
            await call.message.edit_text(
                t(language, "no_data"), reply_markup=kb.back(language)
            )
            await call.answer()
            return

        blocks = [
            f"{t(language, 'current_header')}\n- {snapshot.current_label()}",
            f"{t(language, 'next_header')}\n- {snapshot.next_label()}",
        ]
        advert = await storage.advert()
        if advert:
            blocks.append(f"-----------\n{advert}")

        await call.message.edit_text("\n\n".join(blocks), reply_markup=kb.back(language))
        await call.answer()

    @router.callback_query(F.data == "zones:open")
    async def open_zones(call: CallbackQuery, storage: Storage) -> None:
        await render_zones(call, storage)

    @router.callback_query(F.data.startswith("zones:toggle:"))
    async def toggle_zone(call: CallbackQuery, storage: Storage) -> None:
        raw = call.data.rsplit(":", 1)[-1]
        if not raw.isdigit():
            await call.answer()
            return
        await storage.toggle_zone(call.from_user.id, int(raw))
        await render_zones(call, storage)

    return router
