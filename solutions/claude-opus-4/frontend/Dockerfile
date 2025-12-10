FROM node:20-alpine

WORKDIR /app

# 依存関係のインストール
COPY package.json .
RUN npm install

# アプリケーションコードのコピー
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host"]
