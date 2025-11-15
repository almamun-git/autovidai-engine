# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    elif [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i --frozen-lockfile; \
    else npm i; fi
COPY . .
RUN npm run build

# --- runtime stage (nginx) ---
FROM nginx:alpine
ARG NGINX_BACKEND_URL
ENV NGINX_BACKEND_URL=${NGINX_BACKEND_URL}
COPY --from=build /app/dist /usr/share/nginx/html
# Nginx config with proxy to backend for /api and /files
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
