IMAGE_NAME=dataspike
CONTAINER_NAME=dataspike_service

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --rm \
	-v $(PWD):/app \
	-it $(IMAGE_NAME)

shell:
	docker run --rm -it \
	-v $(PWD):/app \
	$(IMAGE_NAME) bash

stop:
	docker stop $(CONTAINER_NAME)

clean:
	docker rmi $(IMAGE_NAME)