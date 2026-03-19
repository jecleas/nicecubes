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

# Create instance directory for SQLite (use a volume in production)
RUN mkdir -p /data

# Set environment variables
ENV FLASK_APP=app
ENV FLASK_ENV=production
ENV DATABASE_PATH=/data/app.sqlite

EXPOSE 8080

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:create_app()"]
