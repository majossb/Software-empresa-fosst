# ── Etapa 1: build del frontend (Vite + React + TS) ──────────────
FROM node:18-alpine AS build

WORKDIR /app

# Variables de build de Vite (se inlinan en el bundle)
ARG VITE_API_URL=/api
ARG VITE_USE_MOCK=false
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_USE_MOCK=$VITE_USE_MOCK

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Etapa 2: servir el build con Nginx ───────────────────────────
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
