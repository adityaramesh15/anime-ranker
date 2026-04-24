# Use the official lightweight Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our actual Python code into the container
COPY app.py .
COPY ranker.py .

# Run the app using gunicorn, binding to the dynamic PORT Cloud Run provides
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app