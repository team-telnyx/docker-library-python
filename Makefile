SHELL := bash
.ONESHELL:
.SHELLFLAGS := -o errexit -o nounset -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

base_image := buildpack-deps:focal
slim_base_image := ubuntu:focal

namespace := jenkins
image_name := python

image := registry.internal.telnyx.com/${namespace}/${image_name}
latest := 3.10

trivy_argument := $(if $(BUILD_URL),client --remote http://trivy.query.consul,image)

# includes wget, gawk, jq used by the template/update/build scripts
tools.Dockerimage: tools.Dockerfile
	docker build \
		--tag dockerpythonbuildtool:latest \
		--file $< \
		--iidfile $@ \
		.

# base image for focal containers
buildpack-deps-focal.Dockerimage:
	docker pull ${base_image}
	docker image inspect ${base_image} | jq .[0].Id > $@

# base image for slim-focal containers
slim-focal.Dockerimage:
	docker pull ${slim_base_image}
	docker image inspect ${slim_base_image} | jq .[0].Id > $@

.PHONY: build
build:
	make --always-make versions.json
	make 3.7/focal/Dockerimage
	make 3.8/focal/Dockerimage
	make 3.9/focal/Dockerimage
	make 3.10/focal/Dockerimage
	make 3.11-rc/focal/Dockerimage
	make 3.7/slim-focal/Dockerimage
	make 3.8/slim-focal/Dockerimage
	make 3.9/slim-focal/Dockerimage
	make 3.10/slim-focal/Dockerimage
	make 3.11-rc/slim-focal/Dockerimage

.PHONY: build-%
build-%:
	make $(*F)/focal/Dockerimage
	if [ $(*F) == ${latest} ]
	then
		docker tag $(image):$(*F) $(image):latest
	fi

# Folder names start with slim-, so build targets will too, even though the convention
# for docker images is a -slim suffix (e.g. python:3-slim). Don't blame me.
.PHONY: build-slim-%
build-slim-%:
	make $(*F)/slim-focal/Dockerimage
	if [ $(*F) == ${latest} ]
	then
		docker tag $(image):$(*F)-slim $(image):slim
	fi

.PHONY: test-%
test-%:
	# trying to avoid mem overload
	if [ $(*F) == "3.8" ]; then sleep 5; fi
	if [ $(*F) == "3.9" ]; then sleep 10; fi
	if [ $(*F) == "3.10" ]; then sleep 15; fi
	if [ $(*F) == "3.11-rc" ]; then sleep 20; fi

	docker run --rm $(image):$(*F) python --version

	trivy $(trivy_argument) \
		--severity HIGH \
		--exit-code 0 \
		$(image):$(*F)

	trivy $(trivy_argument) \
		--severity CRITICAL \
		--exit-code 1 \
		$(image):$(*F)

.PHONY: test-%
test-slim-%:
	# trying to avoid mem overload
	if [ $(*F) == "3.8" ]; then sleep 5; fi
	if [ $(*F) == "3.9" ]; then sleep 10; fi
	if [ $(*F) == "3.10" ]; then sleep 15; fi
	if [ $(*F) == "3.11-rc" ]; then sleep 20; fi

	docker run --rm $(image):$(*F) python --version

	trivy $(trivy_argument) \
		--severity HIGH \
		--exit-code 0 \
		$(image):$(*F)-slim

	trivy $(trivy_argument) \
		--severity CRITICAL \
		--exit-code 1 \
		$(image):$(*F)-slim

# actual files in the repo
versions.json: versions.sh
	flock --exclusive --timeout 120 --conflict-exit-code 42 versions.json \
		bash -o xtrace versions.sh

.PHONY: version-%
version-%: versions.sh
	flock --exclusive --timeout 120 --conflict-exit-code 42 versions.json \
		bash -o xtrace versions.sh $(*F)

%/focal/Dockerfile: Dockerfile-linux.template
	docker run \
		--rm --tty \
		--user $(shell id -u):$(shell id -g) \
		--volume $(shell pwd):/mnt \
		$$(docker build \
			--quiet \
			--file tools.Dockerfile \
			. \
		) \
			bash -o xtrace apply-templates.sh $(*F)

%/focal/Dockerimage: buildpack-deps-focal.Dockerimage
	docker build \
		--pull \
		--tag $(image):$(*F) \
		--file $(subst image,file,$@) \
		--iidfile $@ \
		.

%/slim-focal/Dockerfile: Dockerfile-linux.template
	docker run \
		--rm --tty \
		--user $(shell id -u):$(shell id -g) \
		--volume $(shell pwd):/mnt \
		$$(docker build \
			--quiet \
			--file tools.Dockerfile \
			. \
		) \
			bash -o xtrace apply-templates.sh $(*F)

%/slim-focal/Dockerimage: slim-focal.Dockerimage
	docker build \
		--pull \
		--tag $(image):$(*F)-slim \
		--file $(subst image,file,$@) \
		--iidfile $@ \
		.
