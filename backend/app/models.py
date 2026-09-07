from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FactBase(BaseModel):
    category: str = Field(..., description="E.g., financial, operational, macroeconomic, corporate_governance, semantic")
    subject: str = Field(..., description="Subject of the fact, e.g. Delhivery FY24 Consolidated Revenue")
    predicate: str = Field(..., description="Attribute or relationship, e.g. reported_value, growth_rate")
    value: str = Field(..., description="Extracted numerical or semantic value")
    unit: Optional[str] = Field("", description="Unit if applicable, e.g. INR Crores, %, Pin Codes")
    temporal_context: Optional[str] = Field("", description="Time period or vintage, e.g. FY 2023-24, May 2011")
    scope_context: Optional[str] = Field("", description="Scope or methodology, e.g. Consolidated, Pre-IPO, Advance Estimate")
    exact_quote: str = Field(..., description="Verbatim ground-truth quote from document")
    char_offset_start: Optional[int] = 0
    char_offset_end: Optional[int] = 0
    confidence: Optional[float] = 1.0
    is_failure_example: Optional[bool] = False
    failure_notes: Optional[str] = ""
    bbox: Optional[List[float]] = Field(default_factory=list, description="Spatial coordinates [x0, y0, x1, y1] on page")

class FactCreate(FactBase):
    document_id: str
    page_number: int

class FactResponse(FactBase):
    id: str
    document_id: str
    document_filename: Optional[str] = ""
    page_number: int
    created_at: str

class DocumentSummary(BaseModel):
    id: str
    filename: str
    filesize: int
    page_count: int
    dataset_tag: str
    status: str
    summary: str
    fact_count: Optional[int] = 0
    created_at: str

class DocumentDetail(DocumentSummary):
    facts: List[FactResponse] = []

class RelationshipBase(BaseModel):
    relationship_type: str = Field(..., description="corroboration, genuine_contradiction, contextual_reconciliation, extraction_failure")
    confidence: float = 1.0
    reasoning: str = Field(..., description="Detailed explanation of relationship")
    context_difference: Optional[str] = Field("", description="temporal, scope, units, methodology")
    case_category: Optional[str] = Field("", description="case_1_corroboration, case_2_contradiction, case_3_contextual, case_4_failure")

class RelationshipResponse(RelationshipBase):
    id: str
    fact_1: FactResponse
    fact_2: FactResponse
    created_at: str

class ShowcaseCase(BaseModel):
    case_number: int
    case_title: str
    case_type: str
    summary: str
    why_it_matters: str
    fact_1: Optional[FactResponse] = None
    fact_2: Optional[FactResponse] = None
    reasoning: str
    evidence_1: Optional[Dict[str, Any]] = None
    evidence_2: Optional[Dict[str, Any]] = None
    resolution_or_mitigation: Optional[str] = None

class ShowcaseResponse(BaseModel):
    cases: List[ShowcaseCase]

class StatsResponse(BaseModel):
    total_documents: int
    total_pages: int
    total_facts: int
    total_relationships: int
    corroborations_count: int
    contradictions_count: int
    contextual_reconciliations_count: int
    failures_cataloged_count: int

class ProcessRequest(BaseModel):
    reconcile_immediately: bool = True
    max_pages: Optional[int] = None
