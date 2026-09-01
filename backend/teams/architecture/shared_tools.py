import json
from jsonschema import validate, ValidationError
from typing import Dict, Any, List

async def generate_mermaid_graph(graph_type: str, elements: List[Dict[str, Any]], title: str = "Architecture Diagram") -> str:
    """
    Generates Mermaid.js syntax for architecture diagrams.
    
    Args:
        graph_type (str): Type of graph (e.g., 'flowchart', 'sequence', 'er').
        elements (list): A list of relationships or components.
            For flowcharts: [{"source": "A", "target": "B", "label": "calls"}]
            For sequence: [{"from": "Client", "to": "Server", "message": "GET /api"}]
        title (str): Title of the diagram.
    """
    if graph_type == "flowchart":
        mermaid = f"---\ntitle: {title}\n---\nflowchart TD\n"
        for idx, el in enumerate(elements):
            source = el.get("source", f"Node{idx}")
            target = el.get("target", f"Node{idx+1}")
            label = el.get("label", "")
            
            # Clean up node names for mermaid (remove spaces for IDs)
            src_id = source.replace(" ", "_").replace("-", "_")
            tgt_id = target.replace(" ", "_").replace("-", "_")
            
            if label:
                mermaid += f"    {src_id}[\"{source}\"] -->|\"{label}\"| {tgt_id}[\"{target}\"]\n"
            else:
                mermaid += f"    {src_id}[\"{source}\"] --> {tgt_id}[\"{target}\"]\n"
        return mermaid
        
    elif graph_type == "sequence":
        mermaid = f"---\ntitle: {title}\n---\nsequenceDiagram\n"
        for el in elements:
            frm = el.get("from", "A")
            to = el.get("to", "B")
            msg = el.get("message", "calls")
            mermaid += f"    {frm}->>{to}: {msg}\n"
        return mermaid
        
    else:
        return f"Unsupported graph_type: {graph_type}. Use 'flowchart' or 'sequence'."


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
