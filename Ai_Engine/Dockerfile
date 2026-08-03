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

# Cap CPU math-library thread pools (OpenMP/MKL/OpenBLAS) at 1.
# Without this, torch/numpy size their internal thread pools off detected
# CPU/memory and blow past the Cloud Run memory limit on every cold start
# (measured: usage scales ~with the container's memory limit, not a fixed need).
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false

# Run the web service on container startup using gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app