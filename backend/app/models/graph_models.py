"""Knowledge-graph domain models for the Agricultural AI platform."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Disease(BaseModel):
    """Represents a crop disease in the knowledge graph."""

    name: str = Field(..., description="English name of the disease.")
    arabic_name: str = Field(..., description="Arabic name of the disease.")
    description: str = Field(..., description="Detailed description of the disease.")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Severity level of the disease."
    )


class Symptom(BaseModel):
    """Observable symptom associated with a crop disease."""

    name: str = Field(..., description="English name of the symptom.")
    arabic_name: str = Field(..., description="Arabic name of the symptom.")
    visual_description: str = Field(
        ..., description="Description of how the symptom appears visually."
    )


class Crop(BaseModel):
    """Agricultural crop entity."""

    name: str = Field(..., description="Common English name of the crop.")
    arabic_name: str = Field(..., description="Arabic name of the crop.")
    scientific_name: str = Field(..., description="Scientific (Latin) name of the crop.")
    category: str = Field(..., description="Crop category (e.g. 'cereal', 'fruit').")


class Fertilizer(BaseModel):
    """Fertilizer or soil amendment entity."""

    name: str = Field(..., description="English name of the fertilizer.")
    arabic_name: str = Field(..., description="Arabic name of the fertilizer.")
    type: str = Field(..., description="Fertilizer type (e.g. 'organic', 'chemical').")
    application_method: str = Field(
        ..., description="Recommended method of application."
    )


class WeatherCondition(BaseModel):
    """Weather condition that may influence crop health."""

    name: str = Field(..., description="English name of the weather condition.")
    arabic_name: str = Field(..., description="Arabic name of the weather condition.")
    temperature_range: Optional[str] = Field(
        default=None, description="Applicable temperature range (e.g. '25-35°C')."
    )
    humidity_range: Optional[str] = Field(
        default=None, description="Applicable humidity range (e.g. '60-80%')."
    )


class Treatment(BaseModel):
    """Treatment or intervention for a crop disease."""

    name: str = Field(..., description="English name of the treatment.")
    arabic_name: str = Field(..., description="Arabic name of the treatment.")
    description: str = Field(..., description="Detailed treatment instructions.")
    duration: str = Field(
        ..., description="Expected treatment duration (e.g. '7 days')."
    )


class GraphRelationship(BaseModel):
    """Typed, weighted edge between two knowledge-graph entities."""

    source_type: str = Field(
        ..., description="Type of the source entity (e.g. 'Disease')."
    )
    source_name: str = Field(..., description="Name of the source entity.")
    relationship: Literal[
        "causes",
        "treated_by",
        "worsened_by",
        "triggered_by",
        "requires",
        "improves_with",
    ] = Field(..., description="Semantic relationship between entities.")
    target_type: str = Field(
        ..., description="Type of the target entity (e.g. 'Treatment')."
    )
    target_name: str = Field(..., description="Name of the target entity.")
    confidence: float = Field(
        default=1.0, description="Confidence score for this relationship (0.0–1.0)."
    )
