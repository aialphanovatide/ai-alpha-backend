FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    wget \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install system dependencies including gcc
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --verbose

# Install playwright and its dependencies
RUN pip install playwright
RUN playwright install
RUN playwright install --with-deps

RUN pip install Flask[async]

# Copy the current directory contents into the container at /app
COPY . .

# Make the script executable
RUN chmod +x script.sh

# Make port 9002 available to the world outside this container
EXPOSE 9002

# Run the script when the container launches
CMD ["./script.sh"]