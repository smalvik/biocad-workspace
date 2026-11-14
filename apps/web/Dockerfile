# syntax=docker/dockerfile:1
FROM node:22.12.0-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
RUN npm run build

FROM build AS test
CMD ["npm", "test"]

FROM nginx:1.27.3-alpine AS runtime
ARG GIT_SHA=dev
LABEL org.opencontainers.image.source="biocad-workspace" org.opencontainers.image.revision=$GIT_SHA
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
EXPOSE 80
