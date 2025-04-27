# Use an official Python image
FROM python:3.11

# Set work directory
WORKDIR /app

# Install qseckey directly from GitHub
RUN pip install qseckey==0.1.2
RUN pip install pycryptodome

# Copy your script into the container
COPY main.py .

# Default command to run the script
CMD ["python", "main.py"]


