FROM python:3.11-slim
WORKDIR /app

# Install Node.js and Yarn for frontend build
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g yarn

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files including frontend source
COPY . /app

# Build frontend
RUN cd web_ui && yarn install --frozen-lockfile && yarn build

CMD ["python", "main.py"]
