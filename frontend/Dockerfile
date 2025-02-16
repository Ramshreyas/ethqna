# Use a slim Python base image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the entire project into the container (build context is the project root)
COPY . .

# Switch to the frontend folder
WORKDIR /app/frontend

# Install dependencies from the project-level requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose port 5000
EXPOSE 5000

# Run the frontend Flask app, binding to all interfaces
CMD ["python", "app.py", "--host=0.0.0.0"]
