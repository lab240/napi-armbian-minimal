# NAPI-C minimal Armbian

Профиль уменьшает образ Armbian для NAPI-C с RK3308.
Форк Armbian должен уже содержать поддержку NAPI-C.
Для скриптов нужны Bash и Python 3.9 или новее.

## Сборка

Запусти скрипт из этого репозитория:

```bash
./build.sh /home/dmn/qwa-armbian-build
```

Скрипт устанавливает профиль и запускает сборку Ubuntu Noble.
Образ появляется в `output/images` форка Armbian.

Для отдельной установки запусти:

```bash
./install.sh /path/to/armbian
cd /path/to/armbian
./compile.sh build napi-minimal
```

Установщик сохраняет файл платы.
Установщик отказывается заменять отличающиеся файлы.
Для обновления запусти `./install.sh /path/to/armbian --force`.
Установщик создаёт резервные копии заменяемых файлов.

## Конфигурация

Изменяй `config/cleanup/napi-c.conf`, затем повтори установку.

- `INSTALL_PACKAGES`: устанавливаемые замены.
- `REMOVE_DOCUMENTATION`: очистка документации.
- `KEEP_DOCUMENTATION`: сохраняемые лицензии и примеры.
- `REMOVE_APT_LISTS`: очистка индексов APT в конце сборки.
- `PRUNE_KERNEL_DTBS`: очистка копий DTB ядра.
- `KEEP_KERNEL_DTBS`: сохраняемые DTB и overlays.
- `REMOVE_PACKAGES`: удаляемые пакеты.
- `KEEP_PACKAGES`: защищённые пакеты.
- `REMOVE_MAN_PAGES`: удаление man-страниц.
- `PRUNE_FIRMWARE`: очистка прошивок.
- `KEEP_FIRMWARE`: сохраняемые прошивки.
- `KERNEL_DISABLE`: отключаемые параметры ядра.
- `KERNEL_ENABLE`: явно включаемые параметры ядра.

Не отключай `SHMEM`, `TMPFS` и `TMPFS_POSIX_ACL`: эти параметры нужны системным монтированиям.

Профиль отключает звук, Wi-Fi, Bluetooth, видео, PCIe, SATA, NVMe, UFS и USB 3.
Профиль сохраняет драйверы Ethernet, SD/eMMC, USB 2, USB-накопителей, USB-модемов, UART, I²C, SPI, CAN и GPIO.
Профиль сохраняет `nano` и дополнительные пакеты NAPI-C.
Профиль заменяет `vim` на `vim-tiny`.
Перед установкой пакетов в образе выполни `sudo apt update`.

Для просмотра очистки готовой файловой системы запусти:

```bash
bash tools/clean-napi-image.sh /path/to/rootfs config/cleanup/napi-c.conf
```

Добавь `--apply` для выполнения очистки.

## Проверки

```bash
python3 -m unittest discover -s tests -v
```

Сборка проверена 9 октября 2026 года: NAPI-C, Ubuntu Noble, Linux 6.18.55.
Сборка `clean2b` останавливается при загрузке: в ядре выключен `CONFIG_TMPFS`.
Образ `tmpfs-fix` явно включает tmpfs.
Пользователь подтверждает загрузку NAPI-C и получение адреса по DHCP.
QEMU запускает этот образ до приглашения входа.
UART, I²C, SPI и CAN пока не проверены.

| Размер | Исходный образ | Первая очистка | Вторая очистка |
|---|---:|---:|---:|
| Файлы перед упаковкой | 1843 МиБ | 1089 МиБ | 861 МиБ |
| Образ | 2420 МиБ | 1440 МиБ | 1144 МиБ |

Профиль повторяет настройки сборки.
Для одинакового бинарного образа нужно также зафиксировать исходники, пакеты и инструменты сборки.

Лицензия: GPL-2.0.
