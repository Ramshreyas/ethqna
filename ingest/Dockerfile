# Use a slim Python base image
FROM python:3.11-slim

# Set the working directory to /app (project root)
WORKDIR /app

# Copy the entire project into the container (build context is the project root)
COPY . .

# Install dependencies from the project-level requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your backend uses (adjust if needed)
EXPOSE 5001

# Run the backend using the module flag (-m) so that relative imports work.
CMD ["python", "-m", "backend.main"]
