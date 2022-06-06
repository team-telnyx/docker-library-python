import collections
import datetime
import itertools
import json
import os
import pathlib
import socket
import time

import jinja2
import requests


REPO_ROOT = pathlib.Path(__file__).parent
ADMONITION = "## THIS FILE IS AUTOGENERATED -- DO NOT EDIT"
S6_TEMPLATE = "s6-Dockerfile.jinja2"
S6_VARS = "s6-vars.json"
IMAGE_REGISTRY = "registry.internal.telnyx.com"

BUILD_URL = os.environ.get("BUILD_URL", "http://{}".format(socket.gethostname()))
BUILD_DATE = datetime.datetime.now().isoformat()
BUILD_NUMBER = os.environ.get("BUILD_NUMBER", "0.{}".format(int(time.time())))


class Targets:
    os_variants = ["jammy", "slim-jammy"]
    python_versions = ["3.7", "3.8", "3.9", "3.10", "3.11-rc"]

    source_for_variant = {
        "jammy": "bullseye",
        "slim-jammy": "slim-bullseye",
    }

    basename_suffix = None

    def __init__(self, osv, pyv):
        self.os_variant = osv
        self.python_version = pyv
        self.base_os = self.source_for_variant[self.os_variant]

        self.target_dir = (REPO_ROOT / self.python_version / self.os_variant)

    @property
    def subdir(self):
        return "{}/{}".format(self.python_version, self.os_variant)

    @property
    def basename(self):
        if self.basename_suffix is None:
            raise NotImplementedError()
        return "{}/{}".format(self.subdir, self.basename_suffix)

    @property
    def subtag(self):
        """3.8, 3.9-slim, 3.11-rc-slim, etc. Just the part past the colon"""
        if "slim" in self.os_variant:
            return self.python_version + "-slim"
        return self.python_version

    @property
    def fulltag(self):
        return "{}/{}/{}:{}".format(IMAGE_REGISTRY, self.image_namespace, self.image_name, self.subtag)


class DockerfileTargets(Targets):
    basename_suffix = "Dockerfile"

    def patch(self, original):
        if "slim" in self.os_variant:
            new = original.replace(
                "FROM debian:{}".format("-".join(reversed(self.base_os.split("-")))),
                # ^^^ yeah... slim-bullseye -> bullseye-slim
                # see: https://github.com/docker-library/python/blob/d6d83a628de3c5/3.11-rc/slim-bullseye/Dockerfile#L7
                "FROM ubuntu:{}".format(self.os_variant.split("-")[1]),
            )
        else:
            new = original.replace(
                "FROM buildpack-deps:{}".format(self.base_os),
                "FROM buildpack-deps:{}".format(self.os_variant),
            )
        if new == original:
            raise ValueError("FROM target patch failed, no changes.")

        return new

    def build(self):
        url = "https://raw.githubusercontent.com/docker-library/python/master/{py_ver}/{base_os}/Dockerfile".format(
            base_os=self.base_os,
            py_ver=self.python_version,
        )

        self.target_dir.mkdir(parents=True, exist_ok=True)

        response = requests.get(url)
        response.raise_for_status()

        original = response.text
        patched = self.patch(original)

        with (self.target_dir / "Dockerfile").open(mode="w") as f:
            f.write(patched)

    @classmethod
    def create_doit_tasks(cls):
        for osv, pyv in itertools.product(cls.os_variants, cls.python_versions):
            self = cls(osv, pyv)
            yield {
                "basename": self.basename,
                "actions": [self.build],
            }


class S6DockerfileTargets(Targets):
    basename_suffix = "with-s6.Dockerfile"

    @classmethod
    def create_doit_tasks(cls):
        for osv, pyv in itertools.product(cls.os_variants, cls.python_versions):
            self = cls(osv, pyv)
            yield {
                "basename": self.basename,
                "file_dep": ["s6-Dockerfile.jinja2", "s6-vars.json"],
                "actions": [self.build],
            }

    def build(self):
        with open(REPO_ROOT / S6_VARS) as f:
            all_vars = json.load(f)

        vars = collections.ChainMap(all_vars["global"], all_vars[self.subtag])

        tplenv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(REPO_ROOT),
            keep_trailing_newline=True,
            undefined=jinja2.StrictUndefined,
        )
        template = tplenv.get_template(S6_TEMPLATE)
        output = template.render(vars)

        output = ADMONITION + "\n" + output

        with open(self.basename, mode="w") as f:
            f.write(output)
        # return output


class DockerimageTargets(Targets):
    latest = "3.10"
    basename_suffix = "Dockerimage"
    associated_dockerfile_cls = DockerfileTargets
    image_namespace = "jenkins"
    image_name = "python"

    @property
    def associated_dockerfile_target(self):
        return self.associated_dockerfile_cls(self.os_variant, self.python_version)

    @classmethod
    def create_doit_tasks(cls):
        for osv, pyv in itertools.product(cls.os_variants, cls.python_versions):
            self = cls(osv, pyv)
            actions = [
                [
                    "docker",
                    "build",
                    "--pull",
                    "--iidfile",
                    self.basename,
                    "--tag",
                    self.fulltag,
                    self.target_dir,
                ],
            ]
            if self.python_version == self.latest:
                actions.append([
                    "docker",
                    "tag",
                    self.fulltag,
                    self.fulltag.split(":")[0] + ":latest",
                ])
            yield {
                "basename": self.basename,
                # "file_dep": [self.associated_dockerfile_target.basename],
                "actions": actions,
            }


class S6DockerimageTargets(DockerimageTargets):
    basename_suffix = "with-s6.Dockerimage"
    associated_dockerfile_cls = S6DockerfileTargets

    # appending to (sub) tag rather than using different image name because
    # the Jenkins job expects a single base name with maybe multiple tags
    # image_name = "py3s6"

    @property
    def subtag(self):
        return super().subtag + "-s6"

    @classmethod
    def create_doit_tasks(cls):
        for osv, pyv in itertools.product(cls.os_variants, cls.python_versions):
            self = cls(osv, pyv)
            actions = [
                [
                    "docker",
                    "build",
                    "--file",
                    self.associated_dockerfile_target.basename,
                    "--iidfile",
                    self.basename,
                    "--tag",
                    self.fulltag,
                    "--build-arg",
                    "PY3S6_BUILD_DATE={}".format(BUILD_DATE),
                    "--build-arg",
                    "PY3S6_BUILD_URL={}".format(BUILD_URL),
                    "--build-arg",
                    "PY3S6_BUILD_NUMBER={}".format(BUILD_NUMBER),
                    "--build-arg",
                    "PY3S6_GIT_COMMIT=d",
                    "--build-arg",
                    "PY3S6_GIT_COMMIT_DATE=e",
                    "dockerbuildcontext",
                ],
            ]
            if self.python_version == self.latest:
                actions.append([
                    "docker",
                    "tag",
                    self.fulltag,
                    self.fulltag.split(":")[0] + ":latest",
                ])
            yield {
                "basename": self.basename,
                # "file_dep": [self.associated_dockerfile_target.basename],
                "actions": actions,
            }


class DockerimageTests(DockerimageTargets):
    basename_suffix = "Dockerimage.test"

    @property
    def associated_dockerimage_target(self):
        return DockerimageTargets(self.os_variant, self.python_version)

    @classmethod
    def create_doit_tasks(cls):
        for osv, pyv in itertools.product(cls.os_variants, cls.python_versions):
            self = cls(osv, pyv)

            trivy_arguments = ["client", "--remote", "http://trivy.query.consul"] if "BUILD_URL" in os.environ else ["image"]

            actions = [
                ["docker", "run", "--rm", self.fulltag, "python", "--version"],
                ["trivy", *trivy_arguments, "--severity", "HIGH", "--exit-code", "0", self.fulltag],
                ["trivy", *trivy_arguments, "--severity", "CRITICAL", "--exit-code", "1", self.fulltag],
            ]
            yield {
                "basename": self.basename,
                # "file_dep": [self.associated_dockerimage_target.basename],
                "actions": actions,
            }


class S6DockerimageTests(DockerimageTests):
    basename_suffix = "with-s6.Dockerimage.test"

    @property
    def subtag(self):
        return super().subtag + "-s6"


def task_shortcuts():
    for osv, pyv in itertools.product(Targets.os_variants, Targets.python_versions):
        subdir = "{}/{}".format(pyv, osv)
        yield {
            "basename": subdir,
            "actions": None,
            "task_dep": [
                "{}/Dockerfile".format(subdir),
                "{}/with-s6.Dockerfile".format(subdir),
                "{}/Dockerimage".format(subdir),
                "{}/with-s6.Dockerimage".format(subdir),
            ],
        }
        yield {
            "basename": "test-" + subdir,
            "actions": None,
            "task_dep": [
                "{}/Dockerimage.test".format(subdir),
                "{}/with-s6.Dockerimage.test".format(subdir),
            ],
        }
