# Define variables for image and container names
IMAGE_NAME := py-config-gs
CONTAINER_NAME := py-config-gs
DOCKER_COMPOSE_FILE := docker-compose.yaml
PORT := 8080  # The port on the host to access Nginx

# Target to build the Docker image using Docker Compose
build:
	@echo "Building Docker images with Docker Compose..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) build

# Target to run the Docker containers in the foreground
run: build
	@echo "Starting Docker containers..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) up

# Target to run Docker containers in detached mode (background)
run-detached: build
	@echo "Starting Docker containers in detached mode..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d

# Target to stop the Docker containers
stop:
	@echo "Stopping Docker containers..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down

# Target to view logs from all services
logs:
	@echo "Showing logs from all Docker services..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f

# Target to clean up all images and containers
clean:
	@echo "Removing Docker images and containers..."
	docker-compose -f $(DOCKER_COMPOSE_FILE) down --rmi all --volumes --remove-orphans

# Help target to show available commands
help:
	@echo "Available commands:"
	@echo "  make build           - Build the Docker images with Docker Compose"
	@echo "  make run             - Run the Docker containers in the foreground"
	@echo "  make run-detached    - Run the Docker containers in detached mode"
	@echo "  make stop            - Stop the running Docker containers"
	@echo "  make logs            - View logs for all services"
	@echo "  make clean           - Remove all containers, images, and volumes"
	@echo "  make help            - Show this help message"
