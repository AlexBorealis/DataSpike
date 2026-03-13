IMAGE_NAME=dataspike
CONTAINER_NAME=dataspike_service

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run -it \
	-v $(PWD)/config:/config \
	$(IMAGE_NAME)

shell:
	docker run -it \
	-v $(PWD)/config:/config \
	$(IMAGE_NAME) \
	bash

stop:
	docker stop $(CONTAINER_NAME)

clean:
	docker rmi $(IMAGE_NAME)