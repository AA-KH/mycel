from .models import (
    OutputContract, OutputPackageContract, OutputContractStatus, OutputType, 
    Cardinality, ArtifactPolicy, DeliveryPolicy
)

def get_base_output_contracts() -> list[OutputContract]:
    
    return [
        # ---------------------------------------------------------
        # CREATIVE
        # ---------------------------------------------------------
        OutputContract(
            output_contract_id="promotional_video",
            name="Promotional Video",
            display_name="Promotional Video",
            domain="creative",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.VIDEO,
            cardinality=Cardinality.ONE,
            formats=["mp4"],
            artifact_policy=ArtifactPolicy.REQUIRED,
            delivery_policy=DeliveryPolicy.USER_DOWNLOAD,
            user_visible=True,
            is_final=True,
            metadata_requirements={},
            content_requirements=[]
        ),
        OutputContract(
            output_contract_id="creative_image",
            name="Creative Image",
            display_name="Creative Image",
            domain="creative",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.IMAGE,
            cardinality=Cardinality.ONE,
            formats=["png", "jpg", "webp"],
            artifact_policy=ArtifactPolicy.REQUIRED,
            delivery_policy=DeliveryPolicy.INLINE,
            user_visible=True,
            is_final=True,
        ),
        # ---------------------------------------------------------
        # ENGINEERING
        # ---------------------------------------------------------
        OutputContract(
            output_contract_id="code_package",
            name="Code Package",
            display_name="Code Package",
            domain="engineering",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.CODE_PACKAGE,
            cardinality=Cardinality.ONE,
            formats=["zip"],
            artifact_policy=ArtifactPolicy.REQUIRED,
            delivery_policy=DeliveryPolicy.USER_DOWNLOAD,
            user_visible=True,
            is_final=True,
        ),
        # ---------------------------------------------------------
        # RESEARCH
        # ---------------------------------------------------------
        OutputContract(
            output_contract_id="research_report",
            name="Research Report",
            display_name="Research Report",
            domain="research",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.REPORT,
            cardinality=Cardinality.ONE,
            formats=["pdf", "md"],
            artifact_policy=ArtifactPolicy.REQUIRED,
            delivery_policy=DeliveryPolicy.INLINE,
            user_visible=True,
            is_final=True,
            content_requirements=[
                "summary", "findings", "conclusion", "sources"
            ]
        ),
        # ---------------------------------------------------------
        # LEGAL
        # ---------------------------------------------------------
        OutputContract(
            output_contract_id="legal_analysis",
            name="Legal Analysis",
            display_name="Legal Analysis",
            domain="legal",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.DOCUMENT,
            cardinality=Cardinality.ONE,
            formats=["pdf", "docx"],
            artifact_policy=ArtifactPolicy.REQUIRED,
            delivery_policy=DeliveryPolicy.USER_DOWNLOAD,
            user_visible=True,
            is_final=True,
            content_requirements=[
                "issue", "jurisdiction", "analysis", "authorities", "risk_notes"
            ]
        ),
        # ---------------------------------------------------------
        # INTERNAL / UTILITY (Not user visible by default)
        # ---------------------------------------------------------
        OutputContract(
            output_contract_id="test_result",
            name="Test Result",
            display_name="Test Result",
            domain="engineering",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.STRUCTURED_DATA,
            cardinality=Cardinality.ONE,
            artifact_policy=ArtifactPolicy.NONE,
            delivery_policy=DeliveryPolicy.REFERENCE,
            user_visible=False,
            is_final=False,
        ),
        OutputContract(
            output_contract_id="structured_requirement",
            name="Structured Requirement",
            display_name="Structured Requirement",
            domain="management",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.STRUCTURED_DATA,
            cardinality=Cardinality.ONE,
            artifact_policy=ArtifactPolicy.NONE,
            user_visible=False,
            is_final=False,
        ),
        OutputContract(
            output_contract_id="source_collection",
            name="Source Collection",
            display_name="Source Collection",
            domain="research",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.DATASET,
            cardinality=Cardinality.MANY,
            artifact_policy=ArtifactPolicy.OPTIONAL,
            user_visible=False,
            is_final=False,
        ),
        OutputContract(
            output_contract_id="verified_evidence",
            name="Verified Evidence",
            display_name="Verified Evidence",
            domain="research",
            status=OutputContractStatus.ACTIVE,
            output_type=OutputType.STRUCTURED_DATA,
            cardinality=Cardinality.MANY,
            artifact_policy=ArtifactPolicy.OPTIONAL,
            user_visible=False,
            is_final=False,
        )
    ]
