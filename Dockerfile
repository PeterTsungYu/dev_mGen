FROM arm32v7/ubuntu:latest

# Set the working directory
WORKDIR /mGen

# Update package lists
RUN apt-get update

# Install necessary packages or dependencies
RUN apt-get install -y python3 python3-pip

# Copy files or set up your application
COPY mGen.py .
COPY tangramModbus.py .
COPY requirements.txt .

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

CMD python3 tangramModbus.py