FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

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
RUN playwright install-deps
RUN playwright install

RUN pip install Flask[async]

# Copy the current directory contents into the container at /app
COPY . .

# Make the script executable
RUN chmod +x script.sh

# Make port 9002 available to the world outside this container
EXPOSE 9002

# Run the script when the container launches
CMD ["./script.sh"]
