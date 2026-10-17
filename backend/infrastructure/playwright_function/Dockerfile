# Keep the browser image and Python package on the same Playwright version.
FROM mcr.microsoft.com/playwright/python:v1.54.0-noble

WORKDIR /var/task
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY search ./search

# Lambda mounts the image read-only; Chromium's profile/cache belong in /tmp.
ENV HOME=/tmp \
    XDG_CACHE_HOME=/tmp/.cache \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["app.lambda_handler"]
