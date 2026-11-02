# Base image: a small Debian with Python. The website only needs Flask and requests.
FROM python:3.12-slim-bookworm

# All following commands, and the running app, use this folder inside the image.
WORKDIR /app

# Install the packages before copying the code. Docker reuses this cached layer until
# requirements.txt changes, so editing the code does not reinstall everything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the files the website needs.
COPY app.py ./
COPY static ./static
COPY templates ./templates

# Run as a normal user instead of root, so a bug in the app has fewer permissions.
RUN useradd --create-home appuser
USER appuser

# Documents the port the app listens on; docker-compose.yml publishes it to the Mac.
EXPOSE 5001

# Show Python's output in docker logs immediately.
ENV PYTHONUNBUFFERED=1

# Listen on 0.0.0.0: the default 127.0.0.1 could only be reached from inside the container.
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5001"]
