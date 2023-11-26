ARG ARCH="linux/amd64"
FROM python:3.12
ENV PYTHONDONTWRITEBYTECODE=1

RUN mkdir "/app"

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 --no-cache-dir install -r requirements.txt \
    && curl -LO https://dl-ssl.google.com/linux/linux_signing_key.pub \
    && gpg --no-default-keyring --keyring /etc/apt/keyrings/google-chrome.gpg --import linux_signing_key.pub \
    && rm -rf linux_signing_key.pub \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt update \
    && apt install google-chrome-stable -y \
    && apt clean autoclean \
    && rm -rf /var/lib/{apt,dpkg,cache,log}/

# We copy this last to help with code edits and faster builds
COPY main.py /app

CMD ["python", "/app/main.py"]
