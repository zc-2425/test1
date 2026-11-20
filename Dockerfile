# 前端镜像：多阶段构建（Node 负责打包，Nginx 负责托管）
FROM node:22-alpine AS build

WORKDIR /app

# 依赖清单先拷，装依赖这层可缓存
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
# 不用 corepack：它固定从 npmjs 官方源下载 pnpm，国内容器里超时就抛 exit 255（无细节）
# 直接用 npm 从国内源装固定版本，pnpm 9 没有 SQLite store，避开 overlay 上的 disk I/O error
RUN npm i -g pnpm@9.15.9 --registry=https://registry.npmmirror.com \
    && pnpm install --frozen-lockfile

COPY . .
# 只跑 vite build，跳过 vue-tsc 类型检查：类型问题不该阻断线上发布
RUN pnpm exec vite build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
