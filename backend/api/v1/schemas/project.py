from pydantic import BaseModel, Field
from typing import List, Optional

class ProductDetails(BaseModel):
    name: str = Field(..., description="E.g., Graphite pencils")
    description: Optional[str] = Field(None, description="What is it, what is it made of, who is it for?")
    categories: Optional[List[str]] = Field(default_factory=list)

class NetworkRegions(BaseModel):
    supply: Optional[str] = Field(None, description="Where can you source from? e.g. India Only, Specific Countries")
    operations: Optional[str] = Field(None, description="Manufacturing / warehouse locations")
    customers: Optional[str] = Field(None, description="Where do you sell / distribute?")

class ExistingKnowledge(BaseModel):
    suppliers: Optional[List[str]] = Field(default_factory=list)
    contracts: Optional[List[str]] = Field(default_factory=list)
    warehouses: Optional[List[str]] = Field(default_factory=list)
    manufacturing: Optional[List[str]] = Field(default_factory=list)
    logistics_agreements: Optional[List[str]] = Field(default_factory=list)
    hard_constraints: Optional[List[str]] = Field(default_factory=list)

class ProjectPayload(BaseModel):
    business_type: str = Field(..., description="E.g., Retail / Ecommerce, Wholesaler / Distributor")
    product: ProductDetails
    regions: NetworkRegions
    priorities: List[str] = Field(default_factory=list, description="Ordered array of priorities like Lowest Cost, Maximum Resilience")
    existing_knowledge: Optional[ExistingKnowledge] = None
