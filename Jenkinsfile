@Library("github.com/team-telnyx/infra-ci-pipelines@latest") _

dockerImage {
    namespace = "jenkins"
    image_name = "python"
    tag = "latest"
    service_version = "latest"

    channel = "python-jenkins"

    build_stage_targets = [
        // "3.11-rc/jammy",
        "3.10/jammy",
        // "3.9/jammy",
        // "3.8/jammy",
        "3.7/jammy",
        // "3.11-rc/slim-jammy",
        // "3.10/slim-jammy",
        // "3.9/slim-jammy",
        // "3.8/slim-jammy",
        // "3.7/slim-jammy",
    ]

    test_stage_targets = [
        // "3.11-rc/jammy.test",
        "3.10/jammy.test",
        // "3.9/jammy.test",
        // "3.8/jammy.test",
        "3.7/jammy.test",
        // "3.11-rc/slim-jammy.test",
        // "3.10/slim-jammy.test",
        // "3.9/slim-jammy.test",
        // "3.8/slim-jammy.test",
        // "3.7/slim-jammy.test",
    ]

    image_additional_images = [
        // "3.11-rc",
        "3.10",
        "3.10-s6",
        // "3.9",
        // "3.8",
        "3.7",
        "3.7-s6",
        // "3.11-rc-slim",
        // "3.10-slim",
        // "3.9-slim",
        // "3.8-slim",
        // "3.7-slim",
    ]
}
