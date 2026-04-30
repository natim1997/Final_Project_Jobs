# 1. Base Image: Use a slim version of Python to keep the container lightweight
FROM python:3.10-slim

# 2. Prevent Python from writing .pyc files and force stdout logging (good for GCP logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# 5. Install dependencies
# SCALABILITY TRICK: We install the CPU-only version of PyTorch. 
# It saves ~3GB of image size and massive RAM costs on Cloud Run, and is plenty fast for inference!
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# 6. Copy the rest of the application (Models, Scripts, etc.)
COPY . .

# 7. Define the port environment variable (Google Cloud Run expects port 8080 by default)
ENV PORT=8080

# 8. Start the Gunicorn Web Server
# --workers 1: We use 1 worker because the AI models (RoBERTa) are huge and consume RAM.
# --threads 4: We use 4 threads to handle multiple concurrent requests asynchronously.
# --timeout 120: Gives the AI up to 120 seconds to process complex CVs before throwing an error.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app