# CrashPeek

**Сбои и зависания программ.** Какая программа упала, какой модуль, какой код исключения. Если Windows записала зависание — отдельная карточка.

**Автор:** darkshade ([@vlx0](https://github.com/vlx0))

**365 дней open source** · **неделя 10 — «Следы»** · день 66.

Не BootPeek: там включения машины. Здесь падения приложений.

---

## Возможности

- список: свежие сверху
- сбой (Application Error 1000) и зависание (Application Hang 1002)
- имя, версия, модуль, код, путь — если Windows это записала
- период 7 / 14 / 30 / 90 дней
- журнал Application, без журнала Security и без прав администратора

## Установка

```powershell
git clone https://github.com/vlx0/CrashPeek.git
cd CrashPeek
pythonw run_crashpeek.pyw
```

Или `start.bat`.

Нужен Windows 10+ и Python 3.10+. Внешних зависимостей нет.

## Лицензия

MIT. См. [LICENSE](LICENSE).
