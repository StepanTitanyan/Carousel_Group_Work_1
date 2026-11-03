FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    sqlalchemy>=2.0.0 \
    psycopg2-binary>=2.9.0 \
    pydantic>=2.5.0

# Copy backend code
COPY backend/ ./backend/

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
