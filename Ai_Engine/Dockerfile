# Use an official Python runtime as a parent image (lightweight version)
FROM python:3.13-slim
# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies 
# (Using --no-cache-dir keeps the image size small)
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn for production server
RUN pip install gunicorn

# Copy the rest of the application code (including Models and saved_matching_model)
COPY . .

# Set the port environment variable to 8080 (Cloud Run default)
ENV PORT 8080

# Run the web service on container startup using gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app