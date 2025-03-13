# Use an official Python image as base
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose ports for public and quantum channels
EXPOSE 8000 8081 4081

# Command to run the application
CMD ["python", "main.py"]
