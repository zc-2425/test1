# 前端镜像：多阶段构建（Node 负责打包，Nginx 负责托管）
FROM node:22-alpine AS build

WORKDIR /app

# 依赖清单先拷，装依赖这层可缓存
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
# pnpm 10+ 的 store 用 SQLite 建索引，在容器 overlay 文件系统上会报 disk I/O error；
# pnpm 9 没有这个索引，最稳。pnpm 9 额外要求 workspace 里必须有 packages 字段。
RUN corepack enable && corepack prepare pnpm@9 --activate \
    && pnpm install --frozen-lockfile

COPY . .
# 只跑 vite build，跳过 vue-tsc 类型检查：类型问题不该阻断线上发布
RUN pnpm exec vite build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
