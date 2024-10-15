FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright and its dependencies
RUN pip install playwright
# RUN playwright install-deps
# RUN playwright install

# Copy the current directory contents into the container at /app
COPY . .

# Make the script executable
RUN chmod +x script.sh

# Make port 9002 available to the world outside this container
EXPOSE 9002

# Run the script when the container launches
CMD ["./script.sh"]
