@Library("github.com/team-telnyx/infra-ci-pipelines@latest") _

dockerImage {
    namespace = "ubuntu"
    image_name = "pybase"
    tag = "latest"
    service_version = "latest"

    channel = "python-jenkins"

    build_stage_targets = [
        "build-3.11-rc",
        "build-3.10",
        "build-3.9",
        "build-3.8",
        "build-3.7",
    ]

    test_stage_targets = [
        "test-3.11-rc",
        "test-3.10",
        "test-3.9",
        "test-3.8",
        "test-3.7",
    ]

    image_additional_images = [
        "3.10",
        "3.9",
        "3.8",
        "3.7",
    ]
}
