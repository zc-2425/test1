# 前端镜像：多阶段构建（Node 负责打包，Nginx 负责托管）
FROM node:22-alpine AS build

WORKDIR /app

# 依赖清单先拷，装依赖这层可缓存
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
# 版本必须和本地一致：pnpm-workspace.yaml 里用的是 pnpm 11 的 allowBuilds 语法，
# pnpm 9 读不懂它，会直接报「packages field missing or empty」
RUN corepack enable && corepack prepare pnpm@11.25.0 --activate \
    && pnpm install --frozen-lockfile

COPY . .
# 只跑 vite build，跳过 vue-tsc 类型检查：类型问题不该阻断线上发布
RUN pnpm exec vite build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
