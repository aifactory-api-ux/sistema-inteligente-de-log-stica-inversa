# =============================================================================
# Frontend Dockerfile - Multi-stage build for Sistema Inteligente de Logistica Inversa
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and build the React application
# -----------------------------------------------------------------------------
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Serve application with nginx
# -----------------------------------------------------------------------------
FROM nginx:1.25-alpine as runtime

RUN apk add --no-cache curl && \
    addgroup -g 1001 -S nginxgroup && \
    adduser -S nginx -u 1001 -G nginxgroup

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginx:nginxgroup /usr/share/nginx/html && \
    chown -R nginx:nginxgroup /var/cache/nginx && \
    chown -R nginx:nginxgroup /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginxgroup /var/run/nginx.pid

USER nginx

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
