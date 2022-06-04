import itertools
import pathlib

import requests


REPO_ROOT = pathlib.Path(__file__).parent


class Targets:
    os_variants = ["jammy", "slim-jammy"]
    python_versions = ["3.7", "3.8", "3.9", "3.10", "3.11-rc"]

    source_for_variant = {
        "jammy": "bullseye",
        "slim-jammy": "slim-bullseye",
    }

    def __init__(self, osv, pyv):
        self.os_variant = osv
        self.python_version = pyv
        self.base_os = self.source_for_variant[self.os_variant]

        self.target_dir = (REPO_ROOT / self.python_version / self.os_variant)

    @property
    def subdir(self):
        return "{}/{}".format(self.python_version, self.os_variant)


class DockerfileTargets(Targets):
    @property
    def basename(self):
        return "{}/Dockerfile".format(self.subdir)

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


class DockerimageTargets(Targets):
    latest = "3.10"

    @property
    def basename(self):
        return "{}/Dockerimage".format(self.subdir)

    @property
    def associated_dockerfile_target(self):
        return DockerfileTargets(self.os_variant, self.python_version)

    @property
    def tag(self):
        if "slim" in self.os_variant:
            subtag = self.python_version + "-slim"
        else:
            subtag = self.python_version
        return "registry.internal.telnyx.com/jenkins/python:{}".format(subtag)

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
                    self.tag,
                    self.target_dir,
                ],
            ]
            if self.python_version == self.latest:
                actions.append([
                    "docker",
                    "tag",
                    self.tag,
                    self.tag.split(":")[0] + ":latest",
                ])
            yield {
                "basename": self.basename,
                "file_dep": [self.associated_dockerfile_target.basename],
                "actions": actions,
            }
