# Front-образ для dev-режиму: Vite dev-server.
# Продакшн-раздача статики (build + nginx) — поза скоупом цієї зміни.
FROM node:24-slim

WORKDIR /app

# Залежності окремим шаром (кеш не інвалідовується при зміні коду)
COPY package.json package-lock.json ./
RUN npm ci

# Код застосунку
COPY . .

EXPOSE 5173

# --host щоб dev-server слухав 0.0.0.0 і був доступний з хоста
CMD ["npm", "run", "dev", "--", "--host"]
