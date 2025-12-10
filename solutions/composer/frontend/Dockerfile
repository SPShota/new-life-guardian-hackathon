FROM node:18-alpine

WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係のインストール
RUN npm install

# アプリケーションコードのコピー
COPY . .

EXPOSE 3000

CMD ["npm", "start"]
