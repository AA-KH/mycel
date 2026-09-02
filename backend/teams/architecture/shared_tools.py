import json
from jsonschema import validate, ValidationError
from typing import Dict, Any, List

async def generate_mermaid_graph(mermaid_syntax: str, title: str = "Architecture Diagram") -> str:
    """
    Generates Mermaid.js syntax for architecture diagrams.
    
    Args:
        mermaid_syntax (str): Raw Mermaid.js syntax (e.g., 'flowchart TD\n  A-->B').
        title (str): Title of the diagram.
    """
    mermaid = f"---\ntitle: {title}\n---\n"
    mermaid += mermaid_syntax
    return mermaid


async def validate_json_schema(schema: Dict[str, Any], sample_data: Dict[str, Any]) -> str:
    """
    Validates sample data against a JSON schema to ensure architectural data models are correct.
    
    Args:
        schema (dict): The JSON schema definition.
        sample_data (dict): The sample payload to validate.
    """
    try:
        validate(instance=sample_data, schema=schema)
        return "SUCCESS: The sample data perfectly matches the proposed JSON schema."
    except ValidationError as e:
        return f"VALIDATION ERROR: Data does not match schema.\nReason: {e.message}\nPath: {'/'.join(str(p) for p in e.path)}"
    except Exception as e:
        return f"SYSTEM ERROR parsing schema: {str(e)}"
