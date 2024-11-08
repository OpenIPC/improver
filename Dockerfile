# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Define environment variables
ENV FLASK_APP=py_config_gs.app
ENV FLASK_ENV=production

# Run Gunicorn to serve the app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "py_config_gs.app:app"]
