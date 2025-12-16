# Настройка переменных окружения для Docker

## Способ 1: Использование .env файла (рекомендуется)

1. **Создайте файл `.env` в корне проекта:**

```bash
# Windows PowerShell
echo "BOT_TOKEN=ваш_токен_здесь" > .env

# Windows CMD
echo BOT_TOKEN=ваш_токен_здесь > .env

# Linux/Mac
echo "BOT_TOKEN=ваш_токен_здесь" > .env
```

2. **Или создайте файл вручную:**

Создайте файл `.env` со следующим содержимым:
```
BOT_TOKEN=ваш_токен_от_BotFather
```

3. **Проверьте файл:**
```bash
# Windows PowerShell
Get-Content .env

# Linux/Mac
cat .env
```

4. **Запустите Docker Compose:**
```bash
docker-compose up -d
```

Docker Compose автоматически загрузит переменные из `.env` файла.

---

## Способ 2: Установка переменной окружения напрямую

### Windows PowerShell:
```powershell
$env:BOT_TOKEN="ваш_токен"
docker-compose up -d
```

### Windows CMD:
```cmd
set BOT_TOKEN=ваш_токен
docker-compose up -d
```

### Linux/Mac:
```bash
export BOT_TOKEN="ваш_токен"
docker-compose up -d
```

---

## Способ 3: Передача через командную строку

### Windows PowerShell:
```powershell
$env:BOT_TOKEN="ваш_токен"; docker-compose up -d
```

### Linux/Mac:
```bash
BOT_TOKEN="ваш_токен" docker-compose up -d
```

---

## Проверка

После запуска проверьте логи:
```bash
docker-compose logs
```

Если токен установлен правильно, вы не увидите предупреждение:
```
The "BOT_TOKEN" variable is not set
```

---

## Безопасность

⚠️ **Важно:**
- Файл `.env` находится в `.gitignore` и не попадет в репозиторий
- Никогда не коммитьте токен бота в Git
- Если токен скомпрометирован, создайте новый через @BotFather

---

## Пример .env файла

```
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

Где получить токен:
1. Откройте Telegram
2. Найдите [@BotFather](https://t.me/BotFather)
3. Отправьте `/newbot` или `/token` для существующего бота
4. Скопируйте полученный токен

