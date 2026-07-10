# =============================================================
# Pantry Helper Web - Multi-stage Dockerfile
#   dev stage  : Vite dev server with HMR (default target)
#   prod stage : Static build served by nginx
# =============================================================

# ---- Build Stage (shared) ----
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ---- Dev Stage ----
FROM build AS dev

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---- Production Stage ----
FROM nginx:stable-alpine AS prod

RUN apk add --no-cache curl

RUN rm /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

COPY pantry.conf /etc/nginx/conf.d/pantry.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -sf http://127.0.0.1:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
