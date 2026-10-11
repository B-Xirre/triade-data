FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS web
WORKDIR /web
COPY lab/web/package.json lab/web/package-lock.json ./
RUN npm ci --ignore-scripts
COPY lab/web ./
RUN npm run test && npm run build

FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY lab/requirements.lock ./lab/requirements.lock
RUN pip install --no-cache-dir -r lab/requirements.lock
COPY lab ./lab
COPY tools ./tools
COPY schema ./schema
COPY content ./content
COPY tests ./tests
COPY --from=web /web/dist ./lab/web/dist
RUN useradd --uid 10001 --create-home labuser
USER 10001
EXPOSE 8765
CMD ["uvicorn","lab.api:app","--host","0.0.0.0","--port","8765"]
