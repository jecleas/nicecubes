# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask app
COPY app/ ./app/

# Copy built React frontend into app/static/dist
COPY --from=frontend-build /frontend/dist ./app/static/dist

# Image-level fallback for local `docker run` without a volume. On Fly the
# volume hides this directory; the app creates it again on first boot if needed.
RUN mkdir -p /data

# Set environment variables
ENV FLASK_APP=app
ENV FLASK_ENV=production
ENV DATABASE_PATH=/data/app.sqlite

EXPOSE 8080

# Run with gunicorn.
# SQLite on the mounted volume is the source of truth for users, stats, and trays.
# One worker keeps writes to that file simple.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "app:create_app()"]
