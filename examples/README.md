# Примеры скинов / Example skins

Скины принадлежат их авторам. Они включены только как примеры для проверки работы инструмента и **будут удалены по просьбе автора** (issue или письмо владельцу репозитория).
These skins belong to their authors. They are included only as usage examples and will be removed at the author's request.

## `skins/` — набор для быстрой проверки (слот = имя файла)
| Файл (слот) | Автор / источник |
|---|---|
| `Pink.png` | **M1rs3m** — скин владельца репозитория |
| `Valorie.png` | **ModemIX** — профиль: поиск по нику на NameMC: <https://namemc.com/search?q=ModemIX> |
| `Violet.png` | **RYIlook** — профиль: поиск по нику на NameMC: <https://namemc.com/search?q=RYIlook> |
| `Alex.png` | **AXOLOTsh** — профиль: поиск по нику на NameMC: <https://namemc.com/search?q=AXOLOTsh> |

`config.json` — режим глаз `hide` для всех.

## `extra/` — скины из NameMC, использовавшиеся для проверок
| Файл | Источник |
|---|---|
| `elf_13c576e23cfbe8ac.png` | <https://namemc.com/skin/13c576e23cfbe8ac> (эльфийка, slim; глаза нарисованы на y=13) |
| `namemc_351050d0c83b1e14.png` | <https://namemc.com/skin/351050d0c83b1e14> (slim) |
| `namemc_be907cfc4aac3be8.png` | <https://namemc.com/skin/be907cfc4aac3be8> (глаза на y=12; для проверки моргания) |

Имена авторов этих трёх скинов берите на странице NameMC по ссылке. Чтобы скачать любой скин самому: <https://s.namemc.com/i/ID.png>, либо в GUI по нику Mojang.

## Запуск
```
python tools/extract_from_game.py --aes 0x...        # один раз
python skintool/build.py --skins examples/skins       # соберёт и установит
python skintool/build.py --skins examples/extra --no-install   # только собрать
```
