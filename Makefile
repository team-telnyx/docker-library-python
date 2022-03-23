SHELL := bash

base_image := buildpack-deps:focal
image := registry.internal.telnyx.com/ubuntu/pybase

versions_url := https://www.python.org/ftp/python/
versions_list_file := /tmp/docker-python.ubuntu.versions.txt
python_full_version := `grep $(PYTHON_VERSION) $(versions_list_file) | tail -n1`

trivy_argument := $(if $(BUILD_URL),client --remote http://trivy.query.consul,image)


# image: versions-list build-ubuntu
# 	@echo -e "\nPYTHON_VERSION=$(PYTHON_VERSION)"
# 	@echo "PYTHON_VERSION_FULL=$(python_full_version)"

# 	docker build \
# 		--tag $(image):$(PYTHON_VERSION) \
# 		--build-arg="PYTHON_VERSION=$(python_full_version)" \
# 		--file ubuntu/$(PYTHON_VERSION).Dockerfile \
# 		ubuntu/


# build-ubuntu:
# 	make refresh-distro
# 	docker build \
# 		--file ubuntu/base.Dockerfile \
# 		--tag ubuntu:telnyx \
# 		ubuntu


buildpack-deps-focal.Dockerimage:
	docker pull ${base_image}
	docker image inspect ${base_image} | jq .[0].Id > $@

versions-list:
	@[ -f $(versions_list_file) ] \
		&& echo ">>> Python versions list already downloaded!" \
		|| curl $(versions_url) \
			| grep -oP "\d\.\d+\.\d+" \
			| sort -t. -k 1,1n -k 2,2n -k 3,3n  \
			| uniq \
			| tee $(versions_list_file)

.PHONY: build-%
build-%:
	make --always-make version-$(*F)
	make $(*F)/focal/Dockerfile
	make $(*F)/focal/Dockerimage

.PHONY: test-%
test-%:
	docker run --rm $(image):$(*F) python --version

	trivy $(trivy_argument) \
		--severity HIGH \
		--exit-code 0 \
		$(image):$(*F)

	trivy $(trivy_argument) \
		--severity CRITICAL \
		--exit-code 1 \
		$(image):$(*F)


# actual files in the repo
versions.json: versions.sh
	./versions.sh

.PHONY: version-%
version-%: versions.sh
	./versions.sh $(*F)

%/focal/Dockerfile: Dockerfile-linux.template
	./apply-templates.sh $(*F)

%/focal/Dockerimage: %/focal/Dockerfile buildpack-deps-focal.Dockerimage
	docker build \
		--pull \
		--tag $(image):$(*F) \
		--file $(subst image,file,$@) \
		--iidfile $@ \
		.
