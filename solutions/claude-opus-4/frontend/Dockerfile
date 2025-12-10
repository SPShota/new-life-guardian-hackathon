FROM node:20-alpine

WORKDIR /app

# 依存関係のインストール
COPY package.json .
RUN npm install

# アプリケーションコードのコピー
COPY . .

# 環境変数（Docker環境用）
ENV VITE_API_URL=http://backend:8000

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host"]
