"""Admin panel.

``build_router`` is a factory rather than a module-level router on purpose.
The guard is installed on the router itself, so every handler inside inherits
it and none can be added without the check; and building a fresh router per
call keeps the wiring free of global state (two dispatchers in one process, as
in the tests, would otherwise fight over one router instance).

aiogram checks a router's own filters before propagating an event to it at all,
which is what makes this a structural guarantee instead of a convention.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from tzbot import keyboards as kb
from tzbot.filters import IsAdmin
from tzbot.storage import Storage
from tzbot.tracker import Broadcaster

MAX_ADVERT_DAYS = 365


class AdminStates(StatesGroup):
    announcement = State()
    ads_text = State()
    ads_days = State()


async def _panel(call: CallbackQuery, storage: Storage) -> None:
    await call.message.edit_text(
        "Admin panel",
        reply_markup=kb.admin_panel(
            maintenance=await storage.maintenance(),
            advert_active=await storage.advert() is not None,
        ),
    )
    await call.answer()


def build_router(admin_ids: frozenset[int]) -> Router:
    router = Router(name="admin")
    guard = IsAdmin(admin_ids)
    router.message.filter(guard)
    router.callback_query.filter(guard)

    @router.callback_query(F.data == "admin:open")
    async def open_panel(call: CallbackQuery, storage: Storage, state: FSMContext) -> None:
        await state.clear()
        await _panel(call, storage)

    @router.callback_query(F.data == "admin:stats")
    async def show_stats(call: CallbackQuery, storage: Storage) -> None:
        stats = await storage.stats()
        await call.message.edit_text(
            "\n".join(
                (
                    f"Users total: {stats['total']}",
                    f"Reachable: {stats['active']}",
                    f"Subscribed: {stats['subscribed']}",
                    f"With a zone filter: {stats['filtered']}",
                )
            ),
            reply_markup=kb.admin_back(),
        )
        await call.answer()

    @router.callback_query(F.data == "admin:maintenance")
    async def toggle_maintenance(call: CallbackQuery, storage: Storage) -> None:
        await storage.set_maintenance(not await storage.maintenance())
        await _panel(call, storage)

    # ------------------------------------------------------- announcement

    @router.callback_query(F.data == "admin:announce")
    async def ask_announcement(call: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(AdminStates.announcement)
        await call.message.edit_text(
            "Send the announcement text:", reply_markup=kb.admin_back()
        )
        await call.answer()

    @router.message(AdminStates.announcement)
    async def send_announcement(
        message: Message, state: FSMContext, storage: Storage, broadcaster: Broadcaster
    ) -> None:
        await state.clear()
        text = (message.text or "").strip()
        if not text:
            await message.answer(
                "Empty announcement, nothing sent.", reply_markup=kb.admin_back()
            )
            return

        recipients = dict.fromkeys(await storage.all_active_ids(), text)
        delivered = await broadcaster.fan_out(recipients)
        await message.answer(
            f"Announcement delivered to {delivered}/{len(recipients)} users.",
            reply_markup=kb.admin_back(),
        )

    # --------------------------------------------------------------- ads

    @router.callback_query(F.data == "admin:ads")
    async def ads_menu(call: CallbackQuery, storage: Storage) -> None:
        advert = await storage.advert()
        header = f"Current advert:\n\n{advert}" if advert else "No active advert."
        await call.message.edit_text(
            header, reply_markup=kb.ads_panel(advert_active=advert is not None)
        )
        await call.answer()

    @router.callback_query(F.data == "admin:ads:delete")
    async def delete_ads(call: CallbackQuery, storage: Storage) -> None:
        await storage.clear_advert()
        await ads_menu(call, storage)

    @router.callback_query(F.data == "admin:ads:set")
    async def ask_ads_text(call: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(AdminStates.ads_text)
        await call.message.edit_text("Send the advert text:", reply_markup=kb.admin_back())
        await call.answer()

    @router.message(AdminStates.ads_text)
    async def ask_ads_days(message: Message, state: FSMContext) -> None:
        await state.update_data(ads_text=message.text or "")
        await state.set_state(AdminStates.ads_days)
        await message.answer("For how many days?", reply_markup=kb.admin_back())

    @router.message(AdminStates.ads_days)
    async def store_ads(message: Message, state: FSMContext, storage: Storage) -> None:
        raw = (message.text or "").strip()
        if not raw.isdigit() or not 1 <= int(raw) <= MAX_ADVERT_DAYS:
            await message.answer(
                f"Enter a whole number of days between 1 and {MAX_ADVERT_DAYS}."
            )
            return

        data = await state.get_data()
        await state.clear()
        await storage.set_advert(data.get("ads_text", ""), int(raw))
        await message.answer(
            f"Advert set for {raw} day(s). It rides along with the next rotations.",
            reply_markup=kb.admin_back(),
        )

    return router
