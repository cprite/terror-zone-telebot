"""Interface strings.

The original stored each locale as three lists indexed by position, so a string
was referred to as ``language["menu"][5]`` and adding one in the middle shifted
every call site.  Keys are named now; ``DEFAULT_LOCALE`` fills any gap so a
missing translation degrades to English instead of raising KeyError.
"""

from __future__ import annotations

DEFAULT_LOCALE = "en"

LOCALES: dict[str, dict[str, str]] = {
    "en": {
        "flag": "\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}",
        "menu_title": "Main menu",
        "btn_subscribe": "Start notifications",
        "btn_unsubscribe": "Stop notifications",
        "btn_zones": "Pick zones",
        "btn_current": "Current zone",
        "btn_language": "Language",
        "btn_back": "Back",
        "btn_done": "Done",
        "current_header": "Current zone:",
        "next_header": "Next zone:",
        "choose_language": "Choose the language of the bot interface:",
        "zones_title": "Choose the terror zones you want to be notified about:",
        "zones_all": "No zone selected - you will be notified about every zone.",
        "subscribed": "Notifications are on. You will get a heads-up before every rotation.",
        "unsubscribed": "Notifications are off.",
        "prealert": "Warriors of Sanctuary,\n\nThe corruption begins to fade. 15 minutes until the next terror zone:",
        "rotation": "Warriors of Sanctuary,\n\nCorrupted tremors strike:",
        "no_data": "The tracker has not reported a zone yet. Try again in a minute.",
        "maintenance": "The bot is under maintenance. Please try again later.",
    },
    "ru": {
        "flag": "\N{REGIONAL INDICATOR SYMBOL LETTER R}\N{REGIONAL INDICATOR SYMBOL LETTER U}",
        "menu_title": "Главное меню",
        "btn_subscribe": "Включить уведомления",
        "btn_unsubscribe": "Выключить уведомления",
        "btn_zones": "Выбор зон",
        "btn_current": "Текущая зона",
        "btn_language": "Язык",
        "btn_back": "Назад",
        "btn_done": "Готово",
        "current_header": "Текущая зона:",
        "next_header": "Следующая зона:",
        "choose_language": "Выберите язык интерфейса бота:",
        "zones_title": "Выберите нужные террор-зоны для уведомлений:",
        "zones_all": "Ни одна зона не выбрана - уведомления будут приходить по всем.",
        "subscribed": "Уведомления включены. Предупрежу перед каждой сменой зоны.",
        "unsubscribed": "Уведомления выключены.",
        "prealert": "Воины Санктуария,\n\nТолчки сбавляют интенсивность. 15 минут до зоны ужаса:",
        "rotation": "Воины Санктуария,\n\nТлетворные толчки снова бушуют! Их цель:",
        "no_data": "Трекер ещё не сообщил зону. Попробуйте через минуту.",
        "maintenance": "Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.",
    },
    "uk": {
        "flag": "\N{REGIONAL INDICATOR SYMBOL LETTER U}\N{REGIONAL INDICATOR SYMBOL LETTER A}",
        "menu_title": "Головне меню",
        "btn_subscribe": "Увімкнути сповіщення",
        "btn_unsubscribe": "Вимкнути сповіщення",
        "btn_zones": "Вибір зон",
        "btn_current": "Поточна зона",
        "btn_language": "Мова",
        "btn_back": "Назад",
        "btn_done": "Готово",
        "current_header": "Поточна зона:",
        "next_header": "Наступна зона:",
        "choose_language": "Виберіть мову інтерфейсу бота:",
        "zones_title": "Виберіть необхідні терор-зони для сповіщень:",
        "zones_all": "Жодної зони не вибрано - сповіщення надходитимуть про всі.",
        "subscribed": "Сповіщення увімкнено. Попереджу перед кожною зміною зони.",
        "unsubscribed": "Сповіщення вимкнено.",
        "prealert": "Воїни Святилища,\n\nПоштовхи зменшують інтенсивність. 15 хвилин до зони жаху:",
        "rotation": "Воїни Святилища,\n\nТлетворні поштовхи знову вирують! Їх ціль:",
        "no_data": "Трекер ще не повідомив зону. Спробуйте за хвилину.",
        "maintenance": "Бот на технічному обслуговуванні. Будь ласка, спробуйте пізніше.",
    },
    "zh": {
        "flag": "\N{REGIONAL INDICATOR SYMBOL LETTER C}\N{REGIONAL INDICATOR SYMBOL LETTER N}",
        "menu_title": "主菜单",
        "btn_subscribe": "开启通知",
        "btn_unsubscribe": "关闭通知",
        "btn_zones": "选择区域",
        "btn_current": "当前区域",
        "btn_language": "语言",
        "btn_back": "返回",
        "btn_done": "完成",
        "current_header": "当前区域:",
        "next_header": "下一个区域:",
        "choose_language": "选择机器人界面语言:",
        "zones_title": "选择需要的恐怖区域以接收通知:",
        "zones_all": "未选择任何区域 - 将通知所有区域。",
        "subscribed": "通知已开启。每次轮换前都会提醒你。",
        "unsubscribed": "通知已关闭。",
        "prealert": "圣域战士们,\n\n腐化开始消退。距离下一个恐怖区域还有15分钟:",
        "rotation": "圣域战士们,\n\n腐化震颤再次袭来:",
        "no_data": "追踪器尚未报告区域。请一分钟后再试。",
        "maintenance": "机器人正在维护中。请稍后再试。",
    },
    "pt": {
        "flag": "\N{REGIONAL INDICATOR SYMBOL LETTER B}\N{REGIONAL INDICATOR SYMBOL LETTER R}",
        "menu_title": "Menu principal",
        "btn_subscribe": "Ativar notificações",
        "btn_unsubscribe": "Desativar notificações",
        "btn_zones": "Escolher zonas",
        "btn_current": "Zona atual",
        "btn_language": "Idioma",
        "btn_back": "Voltar",
        "btn_done": "Feito",
        "current_header": "Zona atual:",
        "next_header": "Próxima zona:",
        "choose_language": "Escolha o idioma da interface do bot:",
        "zones_title": "Escolha as zonas de terror para receber notificações:",
        "zones_all": "Nenhuma zona selecionada - você será notificado sobre todas.",
        "subscribed": "Notificações ativadas. Aviso antes de cada rotação.",
        "unsubscribed": "Notificações desativadas.",
        "prealert": "Guerreiros do Santuário,\n\nA corrupção começa a desaparecer. 15 minutos até a próxima zona de terror:",
        "rotation": "Guerreiros do Santuário,\n\nTremores corrompidos atacam:",
        "no_data": "O rastreador ainda não reportou uma zona. Tente em um minuto.",
        "maintenance": "O bot está em manutenção. Por favor, tente mais tarde.",
    },
    "de": {
        "flag": "\N{REGIONAL INDICATOR SYMBOL LETTER D}\N{REGIONAL INDICATOR SYMBOL LETTER E}",
        "menu_title": "Hauptmenü",
        "btn_subscribe": "Benachrichtigungen an",
        "btn_unsubscribe": "Benachrichtigungen aus",
        "btn_zones": "Zonen wählen",
        "btn_current": "Aktuelle Zone",
        "btn_language": "Sprache",
        "btn_back": "Zurück",
        "btn_done": "Fertig",
        "current_header": "Aktuelle Zone:",
        "next_header": "Nächste Zone:",
        "choose_language": "Wählen Sie die Sprache der Bot-Schnittstelle:",
        "zones_title": "Wählen Sie die Terrorzonen für Benachrichtigungen:",
        "zones_all": "Keine Zone gewählt - Sie werden über alle benachrichtigt.",
        "subscribed": "Benachrichtigungen sind an. Ich melde mich vor jedem Wechsel.",
        "unsubscribed": "Benachrichtigungen sind aus.",
        "prealert": "Krieger des Heiligtums,\n\nDie Korruption beginnt zu verblassen. 15 Minuten bis zur nächsten Terrorzone:",
        "rotation": "Krieger des Heiligtums,\n\nKorrupte Erschütterungen schlagen zu:",
        "no_data": "Der Tracker hat noch keine Zone gemeldet. Versuchen Sie es in einer Minute.",
        "maintenance": "Der Bot wird gewartet. Bitte versuchen Sie es später.",
    },
}

LANGUAGES: tuple[str, ...] = tuple(LOCALES)


def t(language: str, key: str) -> str:
    """Look up a string, falling back to English for missing translations."""
    locale = LOCALES.get(language, LOCALES[DEFAULT_LOCALE])
    value = locale.get(key)
    if value is None:
        value = LOCALES[DEFAULT_LOCALE].get(key, key)
    return value


def flag(language: str) -> str:
    return t(language, "flag")
