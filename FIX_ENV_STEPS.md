# Исправление проблемы с BOT_TOKEN в Docker

## Проблема
Docker Compose видит токен в `.env`, но внутри контейнера переменная пустая.

## Решение

### Шаг 1: Остановите контейнер
```powershell
docker-compose down
```

### Шаг 2: Убедитесь, что .env файл правильный
```powershell
Get-Content .env
```

Должно быть:
```
BOT_TOKEN=
```

**Проверьте:**
- Нет пробелов вокруг `=`
- Нет лишних символов
- Файл сохранен в кодировке UTF-8 без BOM

### Шаг 3: Проверьте конфигурацию Docker Compose
```powershell
docker-compose config | Select-String -Pattern "BOT_TOKEN" -Context 2
```

Должно показать токен (не пустое значение).

### Шаг 4: Пересоздайте контейнер
```powershell
# Удалите старый контейнер полностью
docker-compose down -v

# Пересоздайте и запустите
docker-compose up -d
```

### Шаг 5: Проверьте переменную внутри контейнера
```powershell
docker-compose exec bot printenv BOT_TOKEN
```

Должен вывести токен.

### Шаг 6: Проверьте логи
```powershell
docker-compose logs -f
```

Ошибка о токене должна исчезнуть.

---

## Альтернативное решение: явная передача переменной

Если `env_file` не работает, можно передать токен напрямую:

```powershell
docker-compose down
$env:BOT_TOKEN=""
docker-compose up -d
```

Но это менее удобно, так как токен нужно будет передавать каждый раз.

---

## Если ничего не помогает

1. **Удалите всё и начните заново:**
   ```powershell
   docker-compose down -v
   docker system prune -f
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Проверьте кодировку .env файла:**
   ```powershell
   # Пересоздайте файл в правильной кодировке
   "BOT_TOKEN=" | Out-File -Encoding utf8 -NoNewline .env
   ```

3. **Используйте абсолютный путь к .env:**
   В `docker-compose.yml` измените:
   ```yaml
   env_file:
     - ${PWD}/.env
   ```

