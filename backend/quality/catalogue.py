from .models import (
    QualityGate, QualityGateStatus, QualityGateScope, QualityCheckSeverity,
    QualityPolicy, QualityCheck, QualityCheckType
)

def get_base_quality_gates() -> list[QualityGate]:
    """Returns a catalogue of foundational reusable Quality Gates."""
    
    return [
        # ---------------------------------------------------------
        # GLOBAL
        # ---------------------------------------------------------
        QualityGate(
            quality_gate_id="global_artifact_exists",
            name="Global Artifact Exists Gate",
            display_name="Output Artifact Exists",
            description="Verifies that an expected artifact reference was successfully registered in the context.",
            scope=QualityGateScope.OUTPUT,
            status=QualityGateStatus.ACTIVE,
            severity=QualityCheckSeverity.ERROR,
            policy=QualityPolicy.ALL_REQUIRED_PASS,
            checks=[
                QualityCheck(
                    check_id="check_artifact_exists",
                    name="Artifact Exists Check",
                    type=QualityCheckType.EXISTS,
                    required=True,
                    severity=QualityCheckSeverity.ERROR,
                    configuration={"artifact_key": "primary_output"}
                )
            ]
        ),
        # ---------------------------------------------------------
        # VIDEO SPECIFIC
        # ---------------------------------------------------------
        QualityGate(
            quality_gate_id="video_artifact_validity",
            name="Video Artifact Validity Gate",
            display_name="Valid Video Output",
            description="Verifies the artifact is an mp4 video.",
            scope=QualityGateScope.ARTIFACT,
            status=QualityGateStatus.ACTIVE,
            severity=QualityCheckSeverity.CRITICAL,
            policy=QualityPolicy.CRITICAL_FAILURE_BLOCKS,
            checks=[
                QualityCheck(
                    check_id="check_video_exists",
                    name="Video Exists",
                    type=QualityCheckType.EXISTS,
                    required=True,
                    severity=QualityCheckSeverity.CRITICAL,
                    configuration={"artifact_key": "video_output"}
                ),
                QualityCheck(
                    check_id="check_video_format",
                    name="Video Format is MP4",
                    type=QualityCheckType.FORMAT,
                    required=True,
                    severity=QualityCheckSeverity.CRITICAL,
                    configuration={"artifact_key": "video_output", "expected_format": "video/mp4"}
                )
            ]
        ),
        # ---------------------------------------------------------
        # ENGINEERING
        # ---------------------------------------------------------
        QualityGate(
            quality_gate_id="code_test_gate",
            name="Code Test Passing Gate",
            display_name="Tests Pass",
            description="Ensures code tests completed successfully.",
            scope=QualityGateScope.STAGE,
            status=QualityGateStatus.ACTIVE,
            severity=QualityCheckSeverity.ERROR,
            policy=QualityPolicy.ALL_REQUIRED_PASS,
            checks=[
                QualityCheck(
                    check_id="check_tests_pass",
                    name="Tests Pass Check",
                    type=QualityCheckType.TEST, # In future, maps to a specific executor for test payloads
                    required=True,
                    severity=QualityCheckSeverity.ERROR,
                    configuration={}
                )
            ]
        )
    ]
