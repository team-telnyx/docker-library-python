@Library("github.com/team-telnyx/infra-ci-pipelines@latest") _

dockerImage {
    namespace = "jenkins"
    image_name = "python"
    tag = "latest"
    service_version = "latest"

    channel = "python-jenkins"

    build_stage_targets = [
        // "3.11-rc/jammy/Dockerimage",
        "3.10/jammy/Dockerimage",
        // "3.9/jammy/Dockerimage",
        // "3.8/jammy/Dockerimage",
        "3.7/jammy/Dockerimage",
        // "3.11-rc/slim-jammy/Dockerimage",
        // "3.10/slim-jammy/Dockerimage",
        // "3.9/slim-jammy/Dockerimage",
        // "3.8/slim-jammy/Dockerimage",
        // "3.7/slim-jammy/Dockerimage",
    ]

    test_stage_targets = [
        // "test-3.11-rc/jammy/Dockerimage",
        "test-3.10/jammy/Dockerimage",
        // "test-3.9/jammy/Dockerimage",
        // "test-3.8/jammy/Dockerimage",
        "test-3.7/jammy/Dockerimage",
        // "test-3.11-rc/slim-jammy/Dockerimage",
        // "test-3.10/slim-jammy/Dockerimage",
        // "test-3.9/slim-jammy/Dockerimage",
        // "test-3.8/slim-jammy/Dockerimage",
        // "test-3.7/slim-jammy/Dockerimage",
    ]

    image_additional_images = [
        // "3.11-rc",
        "3.10",
        // "3.9",
        // "3.8",
        "3.7",
        // "3.11-rc-slim",
        // "3.10-slim",
        // "3.9-slim",
        // "3.8-slim",
        // "3.7-slim",
    ]
}
