from pydantic import BaseModel, Field
from typing import List, Optional

class ConstraintEntry(BaseModel):
    category: str
    text: str

class ProjectPayload(BaseModel):
    businessType: str = Field("", alias="business_type")
    businessDescription: str = Field("", alias="business_description")
    productName: str = Field("", alias="product_name")
    productDescription: str = Field("", alias="product_description")
    categories: str = ""
    brands: str = ""
    skuRange: str = Field("", alias="sku_range")
    customerTypes: str = Field("", alias="customer_types")
    supplySource: str = Field("", alias="supply_source")
    supplyCountries: str = Field("", alias="supply_countries")
    operations: str = ""
    operationsDetails: str = Field("", alias="operations_details")
    customerScope: str = Field("", alias="customer_scope")
    customerAreas: str = Field("", alias="customer_areas")
    volume: str = ""
    demandPattern: str = Field("", alias="demand_pattern")
    peakSurge: str = Field("", alias="peak_surge")
    timeline: str = ""
    targetDate: str = Field("", alias="target_date")
    deadlineType: str = Field("", alias="deadline_type")
    budgetTolerance: str = Field("", alias="budget_tolerance")
    freightModes: List[str] = Field(default_factory=list, alias="freight_modes")
    priorities: List[str] = Field(default_factory=list)
    constraints: List[ConstraintEntry] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True
