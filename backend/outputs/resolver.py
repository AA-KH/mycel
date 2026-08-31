from typing import Optional, List
from .models import OutputContract
from .registry import OutputContractRegistry
from .merger import OutputContractMerger

class OutputContractResolver:
    """
    Resolves the final effective OutputContract by evaluating the hierarchy:
    Task > Pipeline > Stage > Team
    """
    
    def __init__(self, registry: OutputContractRegistry):
        self.registry = registry
        
    async def resolve(self, contract_ids: List[str]) -> Optional[OutputContract]:
        """
        Takes an ordered list of contract IDs (from least specific to most specific).
        Merges them in order.
        """
        if not contract_ids:
            return None
            
        base_contract = None
        
        for contract_id in contract_ids:
            if not contract_id:
                continue
                
            contract = await self.registry.get_contract(contract_id)
            if not contract:
                continue # or raise error if required
                
            if base_contract is None:
                base_contract = contract
            else:
                base_contract = OutputContractMerger.merge(base_contract, contract)
                
        return base_contract
