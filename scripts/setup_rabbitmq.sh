#!/bin/bash
# Script to setup and start RabbitMQ for GDial

echo "======================================================================"
echo "                 RabbitMQ Setup Script for GDial                      "
echo "======================================================================"
echo

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to set up system RabbitMQ
setup_system_rabbitmq() {
  echo "Installing RabbitMQ directly on the system..."
  
  # Check if we're on a Debian/Ubuntu system
  if command_exists apt-get; then
    echo "Detected Debian/Ubuntu system. Using apt-get..."
    
    echo "Updating package lists..."
    sudo apt-get update
    
    echo "Installing RabbitMQ server..."
    sudo apt-get install -y rabbitmq-server
    
    echo "Enabling RabbitMQ management plugin..."
    sudo rabbitmq-plugins enable rabbitmq_management
    
    echo "Starting RabbitMQ service..."
    sudo systemctl start rabbitmq-server
    
    echo "Checking RabbitMQ service status..."
    sudo systemctl status rabbitmq-server
    
  # Check if we're on a RHEL/CentOS/Fedora system
  elif command_exists yum; then
    echo "Detected RHEL/CentOS/Fedora system. Using yum..."
    
    echo "Installing EPEL repository..."
    sudo yum install -y epel-release
    
    echo "Updating package lists..."
    sudo yum update -y
    
    echo "Installing RabbitMQ server..."
    sudo yum install -y rabbitmq-server
    
    echo "Enabling RabbitMQ management plugin..."
    sudo rabbitmq-plugins enable rabbitmq_management
    
    echo "Starting RabbitMQ service..."
    sudo systemctl start rabbitmq-server
    
    echo "Checking RabbitMQ service status..."
    sudo systemctl status rabbitmq-server
    
  else
    echo "Unsupported package manager. Please install RabbitMQ manually."
    exit 1
  fi
  
  echo "System RabbitMQ setup complete."
  echo "Management interface available at: http://localhost:15672/"
  echo "Default credentials: guest / guest"
}

# Function to set up Docker RabbitMQ
setup_docker_rabbitmq() {
  echo "Setting up RabbitMQ using Docker..."
  
  if ! command_exists docker; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
  fi
  
  # Check if RabbitMQ container is already running
  if docker ps | grep -q rabbitmq; then
    echo "RabbitMQ container is already running."
    docker ps | grep rabbitmq
  else
    # Check if container exists but is stopped
    if docker ps -a | grep -q rabbitmq; then
      echo "RabbitMQ container exists but is not running. Starting it..."
      docker start rabbitmq
    else
      echo "Creating and starting RabbitMQ container..."
      docker run -d --hostname rabbit --name rabbitmq \
        -p 5672:5672 -p 15672:15672 \
        -e RABBITMQ_DEFAULT_USER=guest \
        -e RABBITMQ_DEFAULT_PASS=guest \
        rabbitmq:3-management
    fi
  fi
  
  echo "Waiting for RabbitMQ to start up..."
  sleep 10
  
  echo "Docker RabbitMQ setup complete."
  echo "Management interface available at: http://localhost:15672/"
  echo "Default credentials: guest / guest"
}

# Function to set up Docker Compose RabbitMQ
setup_docker_compose_rabbitmq() {
  echo "Setting up RabbitMQ using Docker Compose..."
  
  if ! command_exists docker-compose; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
  fi
  
  # Create a docker-compose.yml file for RabbitMQ
  cat > docker-compose.yml << EOF
version: '3'
services:
  rabbitmq:
    image: rabbitmq:3-management
    container_name: rabbitmq
    hostname: rabbit
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

volumes:
  rabbitmq_data:
EOF
  
  echo "Starting RabbitMQ using Docker Compose..."
  docker-compose up -d
  
  echo "Waiting for RabbitMQ to start up..."
  sleep 10
  
  echo "Docker Compose RabbitMQ setup complete."
  echo "Management interface available at: http://localhost:15672/"
  echo "Default credentials: guest / guest"
}

# Function to start the GDial workers
start_gdial_workers() {
  echo "Setting up and starting GDial workers..."
  
  # Check if pika is installed
  source venv/bin/activate
  if ! python -c "import pika" > /dev/null 2>&1; then
    echo "Installing pika (RabbitMQ client)..."
    pip install pika
  fi
  
  # Make sure workers scripts are executable
  chmod +x scripts/start_workers.sh scripts/stop_workers.sh
  
  # Start the workers
  ./scripts/start_workers.sh
  
  echo "GDial workers started."
}

# Main execution flow
echo "Please select RabbitMQ installation method:"
echo "1) Install directly on system (requires sudo)"
echo "2) Use Docker container"
echo "3) Use Docker Compose"
echo "4) Skip RabbitMQ setup (if already installed)"
read -p "Enter your choice (1-4): " choice

case $choice in
  1)
    setup_system_rabbitmq
    ;;
  2)
    setup_docker_rabbitmq
    ;;
  3)
    setup_docker_compose_rabbitmq
    ;;
  4)
    echo "Skipping RabbitMQ setup."
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

# Set environment variable for workers
export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"

# Ask if user wants to start GDial workers
read -p "Do you want to start GDial workers now? (y/n): " start_workers

if [ "$start_workers" = "y" ] || [ "$start_workers" = "Y" ]; then
  start_gdial_workers
else
  echo "Skipping worker startup. You can start workers later using:"
  echo "./scripts/start_workers.sh"
fi

echo
echo "======================================================================"
echo "                 RabbitMQ Setup Complete                              "
echo "======================================================================"
echo "Management interface: http://localhost:15672/"
echo "AMQP URL: amqp://guest:guest@localhost:5672/"
echo
echo "To start workers: ./scripts/start_workers.sh"
echo "To stop workers:  ./scripts/stop_workers.sh"
echo "======================================================================"