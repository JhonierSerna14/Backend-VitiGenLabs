"""
Gene Models Module

This module defines Pydantic models for gene-related data structures
including gene data from VCF files, search criteria, and search results.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class WineType(str, Enum):
    """
    Enumeration of supported wine/grape types.
    
    Defines the types of grape varieties supported
    by the genetic analysis system.
    """
    CHARDONNAY = "chardonnay"
    CABERNET = "cabernet"
    PINOT_NOIR = "pinot_noir"
    MERLOT = "merlot"
    SAUVIGNON_BLANC = "sauvignon_blanc"


class GeneSearchCriteria(BaseModel):
    """
    Gene search criteria model.
    
    Defines the parameters that can be used to search
    and filter genetic data in the database.
    """
    search: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Search term for filtering genes"
    )
    chromosome: Optional[str] = Field(
        default=None,
        description="Filter by specific chromosome"
    )
    position_start: Optional[int] = Field(
        default=None,
        ge=0,
        description="Start position for range filtering"
    )
    position_end: Optional[int] = Field(
        default=None,
        ge=0,
        description="End position for range filtering"
    )
    quality_min: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Minimum quality score"
    )
    filter_status: Optional[str] = Field(
        default=None,
        description="Filter by filter status (PASS, FAIL, etc.)"
    )
    sort_by: Optional[str] = Field(
        default=None,
        description="Field to sort results by"
    )
    sort_direction: Optional[str] = Field(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort direction: 'asc' or 'desc'"
    )

    @field_validator("position_end")
    @classmethod
    def validate_position_range(cls, v, values):
        """Validate that end position is greater than start position."""
        if v is not None and values.get("position_start") is not None:
            if v <= values["position_start"]:
                raise ValueError("End position must be greater than start position")
        return v


class GeneBase(BaseModel):
    """
    Base gene model with core genetic variant information.
    
    Represents the fundamental data structure for genetic variants
    as defined in VCF (Variant Call Format) specification.
    """
    chromosome: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Chromosome identifier (e.g., '1', 'X', 'Y')"
    )
    position: int = Field(
        ...,
        ge=1,
        description="1-based position of the variant on the chromosome"
    )
    id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Unique identifier for the variant (dbSNP ID, etc.)"
    )
    reference: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Reference allele sequence"
    )
    alternate: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Alternative allele sequence"
    )
    quality: float = Field(
        ...,
        ge=0.0,
        description="Phred-scaled quality score for the variant"
    )
    filter_status: str = Field(
        ...,
        max_length=50,
        description="Filter status (PASS, FAIL, or filter names)"
    )
    info: Optional[str] = Field(
        default="",
        description="Additional variant information in VCF INFO format"
    )
    format_field: Optional[str] = Field(
        default="",
        alias="format",
        description="Format specification for sample data"
    )
    additional_info: Optional[Dict[str, Union[str, float, int]]] = Field(
        default=None,
        description="Parsed additional information from INFO field"
    )
    format_info: Optional[Dict[str, Union[str, float, int]]] = Field(
        default=None,
        description="Parsed format information"
    )

    @field_validator("chromosome")
    @classmethod
    def validate_chromosome(cls, v: str) -> str:
        """Validate chromosome identifier format."""
        # Remove 'chr' prefix if present and normalize
        if v.lower().startswith('chr'):
            v = v[3:]
        
        # Validate chromosome identifier
        valid_chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y', 'MT', 'M']
        if v.upper() not in [c.upper() for c in valid_chromosomes]:
            # Allow any string for flexibility, but log a warning
            pass
        
        return v.upper()


class GeneCreate(GeneBase):
    """
    Gene creation model for VCF file parsing.
    
    Extends the base gene model with additional fields
    needed when creating gene records from VCF files.
    """
    outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sample-specific data from VCF file"
    )
    file_source: Optional[str] = Field(
        default=None,
        description="Source file path or identifier"
    )
    parsed_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the record was parsed"
    )


class GeneInDB(GeneBase):
    """
    Gene model as stored in the database.
    
    Includes database-specific fields like document ID
    and research file references.
    """
    id: str = Field(..., description="Database document identifier")
    research_file_id: str = Field(
        ...,
        description="Reference to the source research file"
    )
    collection_name: Optional[str] = Field(
        default=None,
        description="Name of the MongoDB collection containing this gene"
    )
    indexed_at: Optional[str] = Field(
        default=None,
        description="Timestamp when the record was indexed"
    )


class GeneBatchUpload(BaseModel):
    """
    Model for batch gene uploads.
    
    Used when uploading multiple genes at once,
    typically from VCF file processing.
    """
    genes: List[GeneCreate] = Field(
        ...,
        min_items=1,
        description="List of genes to upload"
    )
    research_file_metadata: Dict[str, Union[str, int]] = Field(
        ...,
        description="Metadata about the source research file"
    )
    batch_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this batch upload"
    )


class GeneSearchResult(BaseModel):
    """
    Gene search result model.
    
    Contains the results of a gene search query with
    pagination information and metadata.
    """
    total_results: int = Field(
        ...,
        ge=0,
        description="Total number of matching genes"
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number"
    )
    per_page: int = Field(
        ...,
        ge=1,
        le=1000,
        description="Number of results per page"
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages"
    )
    results: List[GeneCreate] = Field(
        ...,
        description="List of matching genes"
    )
    search_time_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Search execution time in milliseconds"
    )
    collection_name: Optional[str] = Field(
        default=None,
        description="Name of the searched collection"
    )

    @field_validator("total_pages")
    @classmethod
    def calculate_total_pages(cls, v, values):
        """Calculate total pages based on total results and per_page."""
        if "total_results" in values and "per_page" in values:
            import math
            return math.ceil(values["total_results"] / values["per_page"])
        return v


class FileUploadResult(BaseModel):
    """
    File upload result model.
    
    Contains information about a successful file upload
    and processing operation.
    """
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    collection_name: str = Field(..., description="Name of the created gene collection")
    total_genes: int = Field(..., ge=0, description="Number of genes processed")
    file_size: int = Field(..., ge=0, description="Size of the uploaded file in bytes")
    filename: str = Field(..., description="Original filename")
    processing_time_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Time taken to process the file"
    )
    status: str = Field(default="completed", description="Processing status")