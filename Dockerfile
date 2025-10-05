# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install base tools needed to add the Google Chrome repository.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        gnupg \
        unzip \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Configure the Google Chrome APT repository and install Chrome with the
# libraries it requires to run in headless mode.
RUN wget -q -O /usr/share/keyrings/google-linux-signing-key.gpg https://dl.google.com/linux/linux_signing_key.pub \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        google-chrome-stable \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcups2 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnss3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libxshmfence1 \
        xdg-utils \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/google-chrome

# Install a ChromeDriver build that matches the installed Chrome version.
RUN set -eux; \
    CHROME_VERSION="$(${CHROME_BIN} --version | awk '{print $3}')"; \
    CHROME_MAJOR="${CHROME_VERSION%%.*}"; \
    if [ "${CHROME_MAJOR}" -ge 115 ]; then \
        wget -q -O /tmp/versions.json "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"; \
        DRIVER_URL=$(grep -o "\"url\":\"https://[^\"]*chromedriver-linux64.zip\"" /tmp/versions.json | grep "/${CHROME_VERSION}/" | head -1 | cut -d'"' -f4); \
        if [ -z "${DRIVER_URL}" ]; then \
            DRIVER_URL=$(wget -q -O - "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR}" | \
                xargs -I {} echo "https://storage.googleapis.com/chrome-for-testing-public/{}/linux64/chromedriver-linux64.zip"); \
        fi; \
        wget -q "${DRIVER_URL}" -O /tmp/chromedriver-linux64.zip; \
        unzip /tmp/chromedriver-linux64.zip -d /tmp/; \
        mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver; \
        rm -rf /tmp/chromedriver-linux64.zip /tmp/chromedriver-linux64 /tmp/versions.json; \
    else \
        DRIVER_VERSION="$(wget -q -O - "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}")"; \
        wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver-linux64.zip"; \
        unzip chromedriver-linux64.zip -d /usr/local/bin/; \
        rm chromedriver-linux64.zip; \
    fi; \
    chmod +x /usr/local/bin/chromedriver

ENV CHROMEDRIVER=/usr/local/bin/chromedriver

WORKDIR /app

COPY pyproject.toml README.md pytest.ini ./
COPY src ./src
COPY tests ./tests

RUN pip install --upgrade pip \
    && pip install .

ENTRYPOINT ["pytest"]
CMD []
