# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Add the project root to the python path
ENV PYTHONPATH=/app

# Copy the requirements first for better caching
COPY ./backend/requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the container for proper imports
COPY . /app

# Set the Python path to include both the app root and backend
ENV PYTHONPATH=/app:/app/backend

# Set working directory to backend
WORKDIR /app/backend

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the app when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
