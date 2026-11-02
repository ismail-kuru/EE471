# Base image: Python on Debian 12, a Linux version the Azure Speech SDK supports.
FROM python:3.12-slim-bookworm

# Linux libraries the Azure Speech SDK needs: certificates for its secure connection
# to Azure, OpenSSL, and the ALSA audio library it loads even when no sound card is used.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libssl3 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# All following commands, and the running app, use this folder inside the image.
WORKDIR /app

# Install the packages before copying the code. Docker reuses this cached layer until
# requirements.txt changes, so editing the code does not reinstall everything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the files the app needs. The .env file with the Azure key stays out of the image.
COPY app.py commands.py custom_classes.py speech.py ./
COPY static ./static
COPY templates ./templates

# Run as a normal user instead of root, so a bug in the app has fewer permissions.
RUN useradd --create-home appuser
USER appuser

# Documents the port the app listens on; docker run -p publishes it to the Mac.
EXPOSE 5001

# Show Python's output in docker logs immediately.
ENV PYTHONUNBUFFERED=1

# Listen on 0.0.0.0: the default 127.0.0.1 could only be reached from inside the container.
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5001"]
