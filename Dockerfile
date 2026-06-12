FROM node:20-bullseye

# Устанавливаем Python 3 и pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости Node.js и устанавливаем их
COPY package*.json ./
RUN npm ci

# Копируем остальной код
COPY . .

# Собираем React + Vite
RUN npm run build

# Открываем порт для Render
EXPOSE 3000

# Запускаем полностек приложение (сервер Node.js, который сам запустит бота Python)
CMD ["npm", "start"]
