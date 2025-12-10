# Stage 1: build frontend
FROM node:18 as nodebuild
WORKDIR /app
# copy frontend sources
COPY frontend/package.json /app/package.json
COPY frontend/package-lock.json /app/package-lock.json
COPY frontend/vite.config.js /app/vite.config.js
COPY frontend/index.html /app/index.html
COPY frontend/src /app/src
RUN npm ci
RUN npm run build

# Stage 2: python runtime
FROM python:3.11-slim
WORKDIR /app

# system deps (if necessary)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# copy backend code
COPY ./backend /app

# copy built frontend into static folder
COPY --from=nodebuild /app/dist /app/static

RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_ENV=production
ENV PORT=8000

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app", "--workers", "2"]
