IMAGE_NAME=dataspike
CONTAINER_NAME=dataspike_service

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --rm -it \
		--name $(CONTAINER_NAME) \
		--gpus all --cpus=6 --memory=6g \
		-e DATA_DIR=/app \
		-e SOURCE_DIR=/app \
		-v $(PWD)/config/params:/app/config \
		-v $(PWD)/input:/app/input \
		$(IMAGE_NAME)

start: build run

shell:
	docker exec -it $(CONTAINER_NAME) bash

stop:
	docker stop $(CONTAINER_NAME)

clean:
	-docker rmi -f $(IMAGE_NAME)
	docker system prune -a --volumes -f

.PHONY: build run start stop clean