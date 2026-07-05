# 1. Use the official Node.js runtime as the base image
FROM node:20-slim

# 2. Install Python 3, pip, and system dependencies in the container
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy package manifests and install Node.js dependencies
COPY package*.json ./
RUN npm install --production --ignore-scripts

# 5. Copy Python requirements
COPY requirements.txt ./

# 6. Initialize a local Python virtual environment inside the container
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --no-cache-dir --upgrade pip
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of the application files
COPY . .

# 8. Expose the port Express is listening on (default Render port is 10000 or PORT env)
EXPOSE 3000

# 9. Define environment variables
ENV PORT=3000
ENV NODE_ENV=production

# 10. Start the Node.js Express server
CMD ["node", "server.js"]
