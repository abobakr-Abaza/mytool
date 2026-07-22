"""Seed data for the catalog module.

Creates VAT types, categories and a broad catalog of billable treatments. Includes
pricing strategies (flat / per_tooth / per_surface / per_role) so that multi-tooth
treatments can scale price with the tooth count automatically.

Visualization rules use the new layered JSONB format:

    visualization_rules = [
        {"layer": "cenital_pattern", "pattern": "diagonal_stripes", "color": "#F59E0B"},
        {"layer": "lateral_icon",    "icon": "implant",            "color": "#10B981"}
    ]

Diagnostic findings (caries, fracture, etc.) are NOT billable and therefore are
not seeded here. Their visualization is driven by the odontogram module's
default rules for clinical_type.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    CatalogItemSession,
    TreatmentCatalogItem,
    TreatmentCategory,
    TreatmentOdontogramMapping,
    VatType,
)

# ============================================================================
# VAT types
# ============================================================================

VAT_TYPES: list[dict[str, Any]] = [
    {
        "key": "exempt",
        "names": {"es": "Exento", "en": "Exempt", "fr": "Exonéré", "ar": "معفى من الضريبة"},
        "rate": 0.0,
        "is_default": True,
    },
    {
        "key": "reduced",
        "names": {"es": "Reducido (10%)", "en": "Reduced (10%)", "fr": "Réduit (10%)", "ar": "مخفض (10%)"},
        "rate": 10.0,
        "is_default": False,
    },
    {
        "key": "standard",
        "names": {"es": "General (21%)", "en": "Standard (21%)", "fr": "Général (21%)", "ar": "قياسي (21%)"},
        "rate": 21.0,
        "is_default": False,
    },
]

# ============================================================================
# Categories
# ============================================================================

CATEGORIES: list[dict[str, Any]] = [
    {
        "key": "diagnostico",
        "names": {"es": "Diagnóstico", "en": "Diagnostic", "fr": "Diagnostic", "ar": "\u0627\u0644\u062a\u0634\u062e\u064a\u0635"},
        "descriptions": {
            "es": "Servicios de diagnóstico y evaluación",
            "en": "Diagnostic and evaluation services",
            "fr": "Services de diagnostique et d'évaluation",
            "ar": "\u062e\u062f\u0645\u0627\u062a \u0627\u0644\u062a\u0634\u062e\u064a\u0635 \u0648\u0627\u0644\u062a\u0642\u064a\u064a\u0645",
        },
        "display_order": 1,
        "icon": "i-lucide-stethoscope",
    },
    {
        "key": "preventivo",
        "names": {"es": "Preventivo", "en": "Preventive", "fr": "Préventif", "ar": "\u0627\u0644\u0648\u0642\u0627\u064a\u0629"},
        "descriptions": {
            "es": "Prevención e higiene dental",
            "en": "Preventive and hygiene",
            "fr": "Prévention et hygiène dentaire",
            "ar": "\u0627\u0644\u0648\u0642\u0627\u064a\u0629 \u0648\u0646\u0638\u0627\u0641\u0629 \u0627\u0644\u0623\u0633\u0646\u0627\u0646",
        },
        "display_order": 2,
        "icon": "i-lucide-shield-check",
    },
    {
        "key": "restauradora",
        "names": {"es": "Restauradora", "en": "Restorative", "fr": "Restauration", "ar": "\u0627\u0644\u062a\u0631\u0645\u064a\u0645"},
        "descriptions": {
            "es": "Restauración dental",
            "en": "Dental restoration",
            "fr": "Restauration dentaire",
            "ar": "\u062a\u0631\u0645\u064a\u0645 \u0627\u0644\u0623\u0633\u0646\u0627\u0646",
        },
        "display_order": 3,
        "icon": "i-lucide-brush",
    },
    {
        "key": "endodoncia",
        "names": {"es": "Endodoncia", "en": "Endodontics", "fr": "Endodontie", "ar": "\u0639\u0644\u0627\u062c \u0627\u0644\u062c\u0630\u0648\u0631"},
        "descriptions": {
            "es": "Tratamientos de conducto radicular",
            "en": "Root canal treatments",
            "fr": "Traitements des canaux radiculaires",
            "ar": "\u0639\u0644\u0627\u062c \u0639\u0635\u0628 \u0627\u0644\u0623\u0633\u0646\u0627\u0646",
        },
        "display_order": 4,
        "icon": "i-lucide-activity",
    },
    {
        "key": "periodoncia",
        "names": {"es": "Periodoncia", "en": "Periodontics", "fr": "Parodontie", "ar": "\u0627\u0644\u0644\u062b\u0629"},
        "descriptions": {
            "es": "Encías y tejidos de soporte",
            "en": "Gums and supporting tissues",
            "fr": "Gencives et tissus de soutien",
            "ar": "\u0627\u0644\u0644\u062b\u0629 \u0648\u0627\u0644\u0623\u0646\u0633\u062c\u0629 \u0627\u0644\u062f\u0627\u0639\u0645\u0629",
        },
        "display_order": 5,
        "icon": "i-lucide-heart-pulse",
    },
    {
        "key": "cirugia",
        "names": {"es": "Cirugía", "en": "Surgery", "fr": "Chirurgie", "ar": "\u0627\u0644\u062c\u0631\u0627\u062d\u0629"},
        "descriptions": {
            "es": "Procedimientos quirúrgicos dentales",
            "en": "Dental surgical procedures",
            "fr": "Procédures chirurgicales dentaires",
            "ar": "\u0627\u0644\u062c\u0631\u0627\u062d\u0629 \u0627\u0644\u0633\u0646\u064a\u0629",
        },
        "display_order": 6,
        "icon": "i-lucide-scissors",
    },
    {
        "key": "ortodoncia",
        "names": {"es": "Ortodoncia", "en": "Orthodontics", "fr": "Orthodontie", "ar": "\u062a\u0642\u0648\u064a\u0645 \u0627\u0644\u0623\u0633\u0646\u0627\u0646"},
        "descriptions": {
            "es": "Ortodoncia y alineación",
            "en": "Orthodontics and alignment",
            "fr": "Orthodontie et alignement",
            "ar": "\u062a\u0642\u0648\u064a\u0645 \u0627\u0644\u0623\u0633\u0646\u0627\u0646 \u0648\u062a\u0635\u062d\u064a\u062d \u0627\u0644\u0625\u0628\u062a\u0633\u0627\u0645\u0629",
        },
        "display_order": 7,
        "icon": "i-lucide-align-center",
    },
    {
        "key": "estetica",
        "names": {"es": "Estética", "en": "Cosmetic", "fr": "Esthétique", "ar": "\u0627\u0644\u062a\u062c\u0645\u064a\u0644"},
        "descriptions": {
            "es": "Estética dental",
            "en": "Cosmetic dentistry",
            "fr": "Esthétique dentaire",
            "ar": "\u062a\u062c\u0645\u064a\u0644 \u0627\u0644\u0623\u0633\u0646\u0627\u0646",
        },
        "display_order": 8,
        "icon": "i-lucide-sparkles",
    },
    {
        "key": "protesis",
        "names": {"es": "Prótesis", "en": "Prosthetics", "fr": "Prothèses", "ar": "\u0627\u0644\u062a\u0639\u0648\u064a\u0636\u0627\u062a"},
        "descriptions": {
            "es": "Prótesis y férulas",
            "en": "Prosthetics and splints",
            "fr": "Prothèses et gouttières",
            "ar": "\u062a\u0631\u0643\u064a\u0628\u0627\u062a \u0627\u0644\u0623\u0633\u0646\u0627\u0646 \u0648\u0627\u0644\u0637\u0641\u0631\u0629",
        },
        "display_order": 9,
        "icon": "i-lucide-puzzle",
    },
    {
        "key": "pediatrica",
        "names": {"es": "Odontopediatría", "en": "Pediatric", "fr": "Odontologie pédiatrique", "ar": "\u0637\u0628 \u0623\u0633\u0646\u0627\u0646 \u0627\u0644\u0623\u0637\u0641\u0627\u0644"},
        "descriptions": {
            "es": "Tratamientos para niños",
            "en": "Treatments for children",
            "fr": "Traitements pour enfants",
            "ar": "\u0639\u0644\u0627\u062c \u0627\u0644\u0623\u0633\u0646\u0627\u0646 \u0644\u0644\u0623\u0637\u0641\u0627\u0644",
        },
        "display_order": 10,
        "icon": "i-lucide-baby",
    },
]


# ============================================================================
# Visualization presets
# ============================================================================
#
# Keep helpers tiny and explicit to make adding new items obvious.


def pattern_fill(pattern: str, color: str) -> dict[str, Any]:
    """Cenital (occlusal) pattern fill. Common for crowns, bridges, inlays."""
    return {"layer": "cenital_pattern", "pattern": pattern, "color": color}


def lateral_icon(icon: str, color: str) -> dict[str, Any]:
    """Lateral view SVG icon. Common for implants, extractions, brackets."""
    return {"layer": "lateral_icon", "icon": icon, "color": color}


def pulp_fill(color: str, extent: str = "full") -> dict[str, Any]:
    """Pulp chamber fill on lateral view. Root canals."""
    return {"layer": "pulp_fill", "color": color, "extent": extent}


def occlusal_surface(color: str, kind: str = "solid_fill") -> dict[str, Any]:
    """Per-surface fill on occlusal view. Fillings, sealants, veneers."""
    return {"layer": "occlusal_surface", "color": color, "kind": kind}


# ============================================================================
# Treatments
# ============================================================================

TREATMENTS: dict[str, list[dict[str, Any]]] = {
    # ---------- Diagnóstico ----------
    "diagnostico": [
        {
            "internal_code": "DX-VISIT",
            "names": {"es": "Primera Visita", "en": "First Visit", "fr": "Première visite", "ar": "\u0643\u0634\u0641 \u0623\u0648\u0644"},
            "descriptions": {
                "es": "Consulta inicial con exploración y diagnóstico",
                "en": "Initial consultation with examination and diagnosis",
                "fr": "Consultation initiale avec examen et diagnostique",
                "ar": "\u0627\u0633\u062a\u0634\u0627\u0631\u0629 \u0623\u0648\u0644\u064a\u0629 \u0645\u0639 \u0641\u062d\u0635 \u0648\u062a\u0634\u062e\u064a\u0635",
            },
            "treatment_scope": "global_mouth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "default_price": Decimal("300.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-REVIEW",
            "names": {"es": "Revisión", "en": "Follow-up", "fr": "Contrôle", "ar": "\u0645\u0631\u0627\u062c\u0639\u0629"},
            "treatment_scope": "global_mouth",
            "default_price": Decimal("200.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-RXPA",
            "names": {
                "es": "Radiografía Periapical",
                "en": "Periapical X-Ray",
                "fr": "Radiographie périapicale",
                "ar": "\u0623\u0634\u0639\u0629 \u062d\u0648\u0644 \u0627\u0644\u0630\u0631\u0648\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("150.00"),
            "default_duration_minutes": 10,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-RXPAN",
            "names": {
                "es": "Radiografía Panorámica",
                "en": "Panoramic X-Ray",
                "fr": "Radiographie panoramique",
                "ar": "\u0623\u0634\u0639\u0629 \u0628\u0627\u0646\u0648\u0631\u0627\u0645\u0627",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("450.00"),
            "default_duration_minutes": 10,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-CBCT",
            "names": {
                "es": "CBCT (TAC 3D)",
                "en": "CBCT (3D Scan)",
                "fr": "CBCT (Tomodensitométrie 3D)",
                "ar": "\u0623\u0634\u0639\u0629 \u0645\u0642\u0637\u0639\u064a\u0629 CBCT",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("1200.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-STUDY",
            "names": {
                "es": "Estudio Ortodóncico",
                "en": "Orthodontic Study",
                "fr": "Étude orthodontique",
                "ar": "\u062f\u0631\u0627\u0633\u0629 \u062a\u0642\u0648\u064a\u0645\u064a\u0629",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("900.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-PHOTO",
            "names": {
                "es": "Fotografías intraorales",
                "en": "Intraoral Photos",
                "fr": "Photographies intraorales",
                "ar": "\u062a\u0635\u0648\u064a\u0631 \u062f\u0627\u062e\u0644 \u0627\u0644\u0641\u0645",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("300.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-URGENT",
            "names": {
                "es": "Visita de urgencia",
                "en": "Emergency visit",
                "fr": "Visite d'urgence",
                "ar": "\u0632\u064a\u0627\u0631\u0629 \u0637\u0627\u0631\u0626\u0629",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-2ND-OPINION",
            "names": {"es": "Segunda opinión", "en": "Second opinion", "fr": "Deuxième avis", "ar": "\u0631\u0623\u064a \u062b\u0627\u0646"},
            "treatment_scope": "global_mouth",
            "default_price": Decimal("500.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "DX-TELE",
            "names": {
                "es": "Telerradiografía lateral",
                "en": "Lateral cephalogram",
                "fr": "Téléradiographie latérale",
                "ar": "\u062a\u0635\u0648\u064a\u0631 \u0625\u0634\u0639\u0627\u0639\u064a \u062c\u0627\u0646\u0628\u064a",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("450.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
    ],
    # ---------- Preventivo ----------
    "preventivo": [
        {
            "internal_code": "PREV-CLEAN",
            "names": {"es": "Limpieza dental", "en": "Dental Cleaning", "fr": "Détartrage", "ar": "\u062a\u0646\u0638\u064a\u0641 \u0623\u0633\u0646\u0627\u0646"},
            "descriptions": {
                "es": "Tartrectomía y pulido",
                "en": "Scaling and polishing",
                "fr": "Détartrage et polissage",
                "ar": "\u062a\u0646\u0638\u064a\u0641 \u0648\u062a\u0644\u0645\u064a\u0639 \u0627\u0644\u0623\u0633\u0646\u0627\u0646",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PREV-FLUOR",
            "names": {"es": "Fluorización", "en": "Fluoride Application", "fr": "Fluoration", "ar": "\u0641\u0644\u0648\u0631\u0627\u064a\u062f"},
            "treatment_scope": "global_mouth",
            "default_price": Decimal("250.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PREV-CHECKUP",
            "names": {"es": "Revisión", "en": "Checkup", "fr": "Contrôle", "ar": "\u0643\u0634\u0641 \u062f\u0648\u0631\u064a"},
            "descriptions": {
                "es": "Revisión general",
                "en": "General checkup",
                "fr": "Contrôle général",
                "ar": "\u0641\u062d\u0635 \u0639\u0627\u0645",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("300.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PREV-SEAL",
            "names": {
                "es": "Sellador de fosas y fisuras",
                "en": "Pit and Fissure Sealant",
                "fr": "Scellement de sillons et fissures",
                "ar": "\u0633\u064a\u0644\u0631",
            },
            "treatment_scope": "tooth",
            "requires_surfaces": True,
            "default_price": Decimal("300.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "sealant",
            "visualization_rules": [occlusal_surface("#06B6D4", "solid_fill")],
            "visualization_config": {"color": "#06B6D4"},
        },
        {
            "internal_code": "PREV-HYGIENE-EDU",
            "names": {
                "es": "Instrucciones de higiene",
                "en": "Oral Hygiene Instruction",
                "fr": "Instructions d'hygiène buccale",
                "ar": "\u062a\u0639\u0644\u064a\u0645\u0627\u062a \u0646\u0638\u0627\u0641\u0629 \u0627\u0644\u0641\u0645",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("200.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PREV-CLEAN-CURETTAGE",
            "names": {
                "es": "Tartrectomía con curetaje",
                "en": "Scaling with curettage",
                "fr": "Détartrage avec curetage",
                "ar": "\u062a\u0646\u0638\u064a\u0641 \u0628\u0627\u0644\u0643\u062d\u062a",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("1100.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PREV-CLEAN-PED",
            "names": {
                "es": "Profilaxis infantil",
                "en": "Pediatric prophylaxis",
                "fr": "Prophylaxie pédiatrique",
                "ar": "\u0648\u0642\u0627\u064a\u0629 \u0623\u0637\u0641\u0627\u0644",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("400.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
    ],
    # ---------- Restauradora ----------
    "restauradora": [
        # Obturaciones (empastes) — un item por material con precio por
        # tramos de superficies (1→5). El precio se calcula al picar las
        # superficies en el diente.
        {
            "internal_code": "REST-COMP",
            "names": {
                "es": "Obturación composite",
                "en": "Composite filling",
                "fr": "Obturation composite",
                "ar": "\u062d\u0634\u0648\u0629 \u062a\u062c\u0645\u064a\u0644\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "requires_surfaces": True,
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "per_surface",
            "surface_prices": {
                "1": "600.00",
                "2": "850.00",
                "3": "1100.00",
                "4": "1250.00",
                "5": "1350.00",
            },
            "odontogram_treatment_type": "filling_composite",
            "visualization_rules": [occlusal_surface("#3B82F6", "solid_fill")],
            "visualization_config": {"color": "#3B82F6"},
        },
        {
            "internal_code": "REST-AMAL",
            "names": {
                "es": "Obturación amalgama",
                "en": "Amalgam filling",
                "fr": "Obturation amalgame",
                "ar": "\u062d\u0634\u0648\u0629 \u0641\u0636\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "requires_surfaces": True,
            "default_price": Decimal("550.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "per_surface",
            "surface_prices": {
                "1": "550.00",
                "2": "750.00",
                "3": "950.00",
                "4": "1100.00",
                "5": "1200.00",
            },
            "odontogram_treatment_type": "filling_amalgam",
            "visualization_rules": [occlusal_surface("#6B7280", "solid_fill")],
            "visualization_config": {"color": "#6B7280"},
        },
        {
            "internal_code": "REST-TEMP",
            "names": {
                "es": "Obturación temporal",
                "en": "Temporary filling",
                "fr": "Obturation temporaire",
                "ar": "\u062d\u0634\u0648\u0629 \u0645\u0624\u0642\u062a\u0629",
            },
            "treatment_scope": "tooth",
            "requires_surfaces": True,
            "default_price": Decimal("400.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "filling_temporary",
            "visualization_rules": [occlusal_surface("#FBBF24", "solid_fill")],
            "visualization_config": {"color": "#FBBF24"},
        },
        # Incrustaciones
        {
            "internal_code": "REST-INLAY-COMP",
            "names": {"es": "Inlay composite", "en": "Composite inlay", "fr": "Inlay composite", "ar": "\u062a\u0631\u0635\u064a\u0639 \u0643\u0648\u0645\u0628\u0648\u0632\u064a\u062a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "inlay",
            "visualization_rules": [pattern_fill("dots", "#60A5FA")],
            "visualization_config": {"color": "#60A5FA"},
        },
        {
            "internal_code": "REST-INLAY-CER",
            "names": {"es": "Inlay cerámico", "en": "Ceramic inlay", "fr": "Inlay céramique", "ar": "\u062a\u0631\u0635\u064a\u0639 \u062e\u0632\u0641\u064a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("3500.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "inlay",
            "visualization_rules": [pattern_fill("dots", "#38BDF8")],
            "visualization_config": {"color": "#38BDF8"},
        },
        {
            "internal_code": "REST-OVER-COMP",
            "names": {
                "es": "Overlay composite",
                "en": "Composite overlay",
                "fr": "Overlay composite",
                "ar": "\u063a\u0637\u0627\u0621 \u0643\u0648\u0645\u0628\u0648\u0632\u064a\u062a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2400.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "overlay",
            "visualization_rules": [pattern_fill("grid", "#60A5FA")],
            "visualization_config": {"color": "#60A5FA"},
        },
        {
            "internal_code": "REST-OVER-CER",
            "names": {"es": "Overlay cerámico", "en": "Ceramic overlay", "fr": "Overlay céramique", "ar": "\u063a\u0637\u0627\u0621 \u062e\u0632\u0641\u064a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("4500.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "overlay",
            "visualization_rules": [pattern_fill("grid", "#38BDF8")],
            "visualization_config": {"color": "#38BDF8"},
        },
        # Carillas (per_tooth pricing — ideal for "carillas múltiples")
        {
            "internal_code": "REST-VEN-COMP",
            "names": {
                "es": "Carilla composite",
                "en": "Composite veneer",
                "fr": "Facette composite",
                "ar": "\u0642\u0634\u0631\u0629 \u0643\u0648\u0645\u0628\u0648\u0632\u064a\u062a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2800.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "veneer",
            "visualization_rules": [occlusal_surface("#F472B6", "outline")],
            "visualization_config": {"color": "#F472B6"},
        },
        {
            "internal_code": "REST-VEN-PORC",
            "names": {
                "es": "Carilla porcelana",
                "en": "Porcelain veneer",
                "fr": "Facette céramique",
                "ar": "\u0642\u0634\u0631\u0629 \u062e\u0632\u0641\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("4800.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "veneer",
            "visualization_rules": [occlusal_surface("#F472B6", "outline")],
            "visualization_config": {"color": "#F472B6"},
        },
        {
            "internal_code": "REST-VEN-ZIR",
            "names": {"es": "Carilla zirconio", "en": "Zirconia veneer", "fr": "Facette zircone", "ar": "\u0642\u0634\u0631\u0629 \u0632\u0631\u0643\u0648\u0646"},
            "treatment_scope": "tooth",
            "default_price": Decimal("5500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "veneer",
            "visualization_rules": [occlusal_surface("#EC4899", "outline")],
            "visualization_config": {"color": "#EC4899"},
        },
        # Coronas unitarias / múltiples (per_tooth pricing)
        {
            "internal_code": "REST-CROWN-MC",
            "names": {
                "es": "Corona metal-cerámica",
                "en": "Metal-ceramic crown",
                "fr": "Couronne métal-céramique",
                "ar": "\u062a\u0627\u062c \u0645\u0639\u062f\u0646\u064a-\u062e\u0632\u0641\u064a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("4000.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown",
            "visualization_rules": [pattern_fill("diagonal_stripes", "#F59E0B")],
            "visualization_config": {"color": "#F59E0B"},
            "sessions": [
                {
                    "labels": {
                        "es": "Toma de medidas",
                        "en": "Impressions",
                        "fr": "Prise d'empreinte",
                    },
                    "default_price": Decimal("1500.00"),
                },
                {
                    "labels": {"es": "Colocación", "en": "Placement", "fr": "Pose"},
                    "default_price": Decimal("2500.00"),
                },
            ],
        },
        {
            "internal_code": "REST-CROWN-ZIR",
            "names": {"es": "Corona zirconio", "en": "Zirconia crown", "fr": "Couronne zircone", "ar": "\u062a\u0627\u062c \u0632\u0631\u0643\u0648\u0646"},
            "treatment_scope": "tooth",
            "default_price": Decimal("5500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown",
            "visualization_rules": [pattern_fill("diagonal_stripes", "#FBBF24")],
            "visualization_config": {"color": "#FBBF24"},
            "sessions": [
                {
                    "labels": {
                        "es": "Toma de medidas",
                        "en": "Impressions",
                        "fr": "Prise d'empreinte",
                    },
                    "default_price": Decimal("2000.00"),
                },
                {
                    "labels": {"es": "Colocación", "en": "Placement", "fr": "Pose"},
                    "default_price": Decimal("3500.00"),
                },
            ],
        },
        {
            "internal_code": "REST-CROWN-DISI",
            "names": {
                "es": "Corona disilicato de litio",
                "en": "Lithium disilicate crown",
                "fr": "Couronne disilicate de lithium",
                "ar": "\u062a\u0627\u062c \u062f\u064a\u0633\u064a\u0644\u064a\u0643\u0627\u062a \u0627\u0644\u0644\u064a\u062b\u064a\u0648\u0645",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("6500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown",
            "visualization_rules": [pattern_fill("diagonal_stripes", "#FDE68A")],
            "visualization_config": {"color": "#FDE68A"},
            "sessions": [
                {
                    "labels": {
                        "es": "Toma de medidas",
                        "en": "Impressions",
                        "fr": "Prise d'empreinte",
                    },
                    "default_price": Decimal("2500.00"),
                },
                {
                    "labels": {"es": "Colocación", "en": "Placement", "fr": "Pose"},
                    "default_price": Decimal("4000.00"),
                },
            ],
        },
        {
            "internal_code": "REST-CROWN-METAL",
            "names": {"es": "Corona metal", "en": "Metal crown", "fr": "Couronne métallique", "ar": "\u062a\u0627\u062c \u0645\u0639\u062f\u0646\u064a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("3500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown",
            "visualization_rules": [pattern_fill("diagonal_stripes", "#9CA3AF")],
            "visualization_config": {"color": "#9CA3AF"},
        },
        {
            "internal_code": "REST-CROWN-PROV",
            "names": {
                "es": "Corona provisional",
                "en": "Provisional crown",
                "fr": "Couronne provisoire",
                "ar": "\u062a\u0627\u062c \u0645\u0624\u0642\u062a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1500.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown",
            "visualization_rules": [pattern_fill("outline", "#D1D5DB")],
            "visualization_config": {"color": "#D1D5DB"},
        },
        # Coronas sobre implante — render as solid lateral-crown fill
        # (the runtime in ToothDualView treats `crown_on_implant` and
        # `provisional_crown_on_implant` the same way as a bridge).
        {
            "internal_code": "REST-CROWN-IMPL-MC",
            "names": {
                "es": "Corona sobre implante metal-cerámica",
                "en": "Metal-ceramic crown on implant",
                "fr": "Couronne sur implant métal-céramique",
                "ar": "\u062a\u0627\u062c \u0639\u0644\u0649 \u0632\u0631\u0639\u0629 \u0645\u0639\u062f\u0646\u064a-\u062e\u0632\u0641\u064a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("6000.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown_on_implant",
            "visualization_rules": [pattern_fill("solid", "#F59E0B")],
            "visualization_config": {"color": "#F59E0B"},
            "sessions": [
                {
                    "labels": {
                        "es": "Toma de medidas",
                        "en": "Impressions",
                        "fr": "Prise d'empreinte",
                    },
                    "default_price": Decimal("2000.00"),
                },
                {
                    "labels": {"es": "Colocación", "en": "Placement", "fr": "Pose"},
                    "default_price": Decimal("4000.00"),
                },
            ],
        },
        {
            "internal_code": "REST-CROWN-IMPL-ZIR",
            "names": {
                "es": "Corona sobre implante zirconio",
                "en": "Zirconia crown on implant",
                "fr": "Couronne sur implant zircone",
                "ar": "\u062a\u0627\u062c \u0639\u0644\u0649 \u0632\u0631\u0639\u0629 \u0632\u0631\u0643\u0648\u0646",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("7500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown_on_implant",
            "visualization_rules": [pattern_fill("solid", "#FBBF24")],
            "visualization_config": {"color": "#FBBF24"},
            "sessions": [
                {
                    "labels": {
                        "es": "Toma de medidas",
                        "en": "Impressions",
                        "fr": "Prise d'empreinte",
                    },
                    "default_price": Decimal("2500.00"),
                },
                {
                    "labels": {"es": "Colocación", "en": "Placement", "fr": "Pose"},
                    "default_price": Decimal("5000.00"),
                },
            ],
        },
        {
            "internal_code": "REST-CROWN-IMPL-PROV",
            "names": {
                "es": "Corona provisional sobre implante",
                "en": "Provisional crown on implant",
                "fr": "Couronne provisoire sur implant",
                "ar": "\u062a\u0627\u062c \u0645\u0624\u0642\u062a \u0639\u0644\u0649 \u0632\u0631\u0639\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "provisional_crown_on_implant",
            "visualization_rules": [pattern_fill("solid", "#FCD34D")],
            "visualization_config": {"color": "#FCD34D"},
        },
        # Puentes (per_role pricing)
        {
            "internal_code": "REST-BRIDGE-MC",
            "names": {
                "es": "Puente metal-cerámica",
                "en": "Metal-ceramic bridge",
                "fr": "Pont métal-céramique",
                "ar": "\u062c\u0633\u0631 \u0645\u0639\u062f\u0646\u064a-\u062e\u0632\u0641\u064a",
            },
            "treatment_scope": "multi_tooth",
            "default_price": Decimal("4000.00"),
            "default_duration_minutes": 120,
            "vat_type": "exempt",
            "pricing_strategy": "per_role",
            "pricing_config": {"pillar": 400, "pontic": 300},
            "odontogram_treatment_type": "bridge",
            "visualization_rules": [pattern_fill("horizontal_stripes", "#F59E0B")],
            "visualization_config": {"color": "#F59E0B"},
        },
        {
            "internal_code": "REST-BRIDGE-ZIR",
            "names": {"es": "Puente zirconio", "en": "Zirconia bridge", "fr": "Pont zircone", "ar": "\u062c\u0633\u0631 \u0632\u0631\u0643\u0648\u0646"},
            "treatment_scope": "multi_tooth",
            "default_price": Decimal("5000.00"),
            "default_duration_minutes": 120,
            "vat_type": "exempt",
            "pricing_strategy": "per_role",
            "pricing_config": {"pillar": 500, "pontic": 400},
            "odontogram_treatment_type": "bridge",
            "visualization_rules": [pattern_fill("horizontal_stripes", "#FBBF24")],
            "visualization_config": {"color": "#FBBF24"},
        },
        {
            "internal_code": "REST-BRIDGE-MARY",
            "names": {"es": "Puente Maryland", "en": "Maryland bridge", "fr": "Pont du Maryland", "ar": "\u062c\u0633\u0631 \u0645\u064a\u0631\u064a\u0644\u0627\u0646\u062f"},
            "treatment_scope": "multi_tooth",
            "default_price": Decimal("3500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_role",
            "pricing_config": {"pillar": 350, "pontic": 300},
            "odontogram_treatment_type": "bridge",
            "visualization_rules": [pattern_fill("horizontal_stripes", "#FDE68A")],
            "visualization_config": {"color": "#FDE68A"},
        },
        # Férulas
        {
            "internal_code": "REST-SPLINT-OCC",
            "names": {
                "es": "Férula de descarga",
                "en": "Occlusal splint",
                "fr": "Gouttière d'occlusion",
                "ar": "\u062c\u0628\u064a\u0631\u0629 \u0625\u0637\u0628\u0627\u0642\u064a\u0629",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("2200.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "splint",
            "visualization_rules": [lateral_icon("splint", "#3B82F6")],
            "visualization_config": {"color": "#3B82F6"},
        },
        {
            "internal_code": "REST-SPLINT-PERIO",
            "names": {
                "es": "Férula periodontal de contención",
                "en": "Periodontal retention splint",
                "fr": "Gouttière de contention parodontale",
                "ar": "\u062c\u0628\u064a\u0631\u0629 \u062f\u0648\u0627\u0639\u0645 \u0633\u0646\u064a\u0629",
            },
            "treatment_scope": "multi_tooth",
            "default_price": Decimal("800.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "splint",
            "visualization_rules": [lateral_icon("splint", "#8B5CF6")],
            "visualization_config": {"color": "#8B5CF6"},
        },
        {
            "internal_code": "REST-RECONSTR",
            "names": {
                "es": "Reconstrucción amplia con composite",
                "en": "Large composite reconstruction",
                "fr": "Reconstruction extensive en composite",
                "ar": "\u0625\u0639\u0627\u062f\u0629 \u0628\u0646\u0627\u0621 \u0648\u0627\u0633\u0639\u0629 \u0628\u0627\u0644\u0643\u0648\u0645\u0628\u0648\u0632\u064a\u062a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1600.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "filling_composite",
            "visualization_rules": [occlusal_surface("#8B5CF6", "solid_fill")],
            "visualization_config": {"color": "#8B5CF6"},
        },
        {
            "internal_code": "REST-FILL-REPAIR",
            "names": {
                "es": "Reparación de obturación",
                "en": "Filling repair",
                "fr": "Réparation d'obturation",
                "ar": "\u0625\u0635\u0644\u0627\u062d \u062d\u0634\u0648\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("550.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "filling_composite",
            "visualization_rules": [occlusal_surface("#3B82F6", "solid_fill")],
            "visualization_config": {"color": "#3B82F6"},
        },
        {
            "internal_code": "REST-CROWN-RECEMENT",
            "names": {
                "es": "Recementado de corona",
                "en": "Crown recementation",
                "fr": "Recimentation de couronne",
                "ar": "\u0625\u0639\u0627\u062f\u0629 \u062a\u062b\u0628\u064a\u062a \u062a\u0627\u062c",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown",
            "visualization_rules": [pattern_fill("diagonal_stripes", "#94A3B8")],
            "visualization_config": {"color": "#94A3B8"},
        },
        {
            "internal_code": "REST-CROWN-POST-ENDO",
            "names": {
                "es": "Corona sobre diente endodonciado",
                "en": "Crown over endodontically treated tooth",
                "fr": "Couronne sur dent dévitalisée",
                "ar": "\u062a\u0627\u062c \u0639\u0644\u0649 \u0633\u0646 \u0645\u0639\u0627\u0644\u062c \u0644\u0628\u064a\u0627\u064b",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("4500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown",
            "visualization_rules": [pattern_fill("diagonal_stripes", "#A78BFA")],
            "visualization_config": {"color": "#A78BFA"},
        },
        {
            "internal_code": "REST-HEAL-ABUT",
            "names": {
                "es": "Pilar de cicatrización",
                "en": "Healing abutment",
                "fr": "Pilier de cicatrisation",
                "ar": "\u062f\u0639\u0627\u0645\u0629 \u0634\u0641\u0627\u0621",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1500.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "implant",
            "visualization_rules": [lateral_icon("implant", "#22C55E")],
            "visualization_config": {"color": "#22C55E"},
        },
        {
            "internal_code": "REST-DEF-ABUT",
            "names": {
                "es": "Pilar definitivo",
                "en": "Definitive abutment",
                "fr": "Pilier définitif",
                "ar": "\u062f\u0639\u0627\u0645\u0629 \u0646\u0647\u0627\u0626\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2500.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "implant",
            "visualization_rules": [lateral_icon("implant", "#16A34A")],
            "visualization_config": {"color": "#16A34A"},
        },
    ],
    # ---------- Endodoncia ----------
    "endodoncia": [
        {
            "internal_code": "ENDO-UNI",
            "names": {
                "es": "Endodoncia unirradicular",
                "en": "Single-root endodontics",
                "fr": "Endodontie uniradiculaire",
                "ar": "\u0639\u0644\u0627\u062c \u0639\u0635\u0628 \u0633\u0646 \u0648\u0627\u062d\u062f",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": [pulp_fill("#8B5CF6", "full")],
            "visualization_config": {"color": "#8B5CF6"},
        },
        {
            "internal_code": "ENDO-BI",
            "names": {
                "es": "Endodoncia birradicular",
                "en": "Two-root endodontics",
                "fr": "Endodontie biradiculaire",
                "ar": "\u0639\u0644\u0627\u062c \u0639\u0635\u0628 \u0633\u0646\u064a\u0646",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2800.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": [pulp_fill("#8B5CF6", "full")],
            "visualization_config": {"color": "#8B5CF6"},
        },
        {
            "internal_code": "ENDO-MULTI",
            "names": {
                "es": "Endodoncia molar",
                "en": "Molar endodontics",
                "fr": "Endodontie molaire",
                "ar": "\u0639\u0644\u0627\u062c \u0639\u0635\u0628 \u0637\u0627\u062d\u0648\u0646\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("3800.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": [pulp_fill("#7C3AED", "full")],
            "visualization_config": {"color": "#7C3AED"},
            "sessions": [
                {
                    "labels": {
                        "es": "Apertura y conductometría",
                        "en": "Access and length",
                        "fr": "Ouverture et détermination",
                    },
                    "default_price": Decimal("1300.00"),
                },
                {
                    "labels": {
                        "es": "Limpieza y conformación",
                        "en": "Cleaning and shaping",
                        "fr": "Nettoyage et mise en forme",
                    },
                    "default_price": Decimal("1300.00"),
                },
                {
                    "labels": {"es": "Obturación", "en": "Obturation", "fr": "Obturation"},
                    "default_price": Decimal("1200.00"),
                },
            ],
        },
        {
            "internal_code": "ENDO-RETREAT",
            "names": {
                "es": "Re-tratamiento endodóncico",
                "en": "Endodontic retreatment",
                "fr": "Retraitement endodontique",
                "ar": "\u0625\u0639\u0627\u062f\u0629 \u0639\u0644\u0627\u062c \u0639\u0635\u0628",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("3800.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": [pulp_fill("#A78BFA", "full")],
            "visualization_config": {"color": "#A78BFA"},
        },
        {
            "internal_code": "ENDO-POST-FIBER",
            "names": {"es": "Perno de fibra", "en": "Fiber post", "fr": "Pivot en fibre", "ar": "\u0648\u062a\u062f \u0644\u064a\u0641\u064a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("1200.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "post",
            "visualization_rules": [lateral_icon("post", "#8B5CF6")],
            "visualization_config": {"color": "#8B5CF6"},
        },
        {
            "internal_code": "ENDO-POST-METAL",
            "names": {"es": "Perno colado", "en": "Cast post", "fr": "Pivot coulé", "ar": "\u0648\u062a\u062f \u0645\u0639\u062f\u0646\u064a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "post",
            "visualization_rules": [lateral_icon("post", "#6B7280")],
            "visualization_config": {"color": "#6B7280"},
        },
        {
            "internal_code": "ENDO-URGENT",
            "names": {
                "es": "Apertura cameral urgente",
                "en": "Emergency pulp chamber opening",
                "fr": "Ouverture d'urgence de la chambre pulpaire",
                "ar": "\u0641\u062a\u062d \u062d\u062c\u0631\u0629 \u0627\u0644\u0644\u0628 \u0637\u0627\u0631\u0626",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("800.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_half",
            "visualization_rules": [pulp_fill("#C084FC", "partial_1_2")],
            "visualization_config": {"color": "#C084FC"},
        },
        {
            "internal_code": "ENDO-MED-REFRESH",
            "names": {
                "es": "Recambio de medicación intraconducto",
                "en": "Intracanal medication refresh",
                "fr": "Renouvellement de médicament intraradiculaire",
                "ar": "\u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0627\u0621 \u062f\u0627\u062e\u0644 \u0627\u0644\u0642\u0646\u0627\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_two_thirds",
            "visualization_rules": [pulp_fill("#C4B5FD", "partial_2_3")],
            "visualization_config": {"color": "#C4B5FD"},
        },
        {
            "internal_code": "ENDO-APICOFORM",
            "names": {"es": "Apicoformación", "en": "Apexification", "fr": "Apexification", "ar": "\u062a\u0643\u0648\u064a\u0646 \u0642\u0645\u0629 \u0627\u0644\u062c\u0630\u0631"},
            "treatment_scope": "tooth",
            "default_price": Decimal("2800.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": [pulp_fill("#A78BFA", "full")],
            "visualization_config": {"color": "#A78BFA"},
        },
        {
            "internal_code": "ENDO-PED",
            "names": {
                "es": "Endodoncia en pieza temporal",
                "en": "Endodontics on primary tooth",
                "fr": "Endodontie sur dent temporaire",
                "ar": "\u0639\u0644\u0627\u062c \u0639\u0635\u0628 \u0623\u0633\u0646\u0627\u0646 \u0623\u0637\u0641\u0627\u0644",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1400.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": [pulp_fill("#A78BFA", "full")],
            "visualization_config": {"color": "#A78BFA"},
        },
    ],
    # ---------- Periodoncia ----------
    "periodoncia": [
        {
            "internal_code": "PERIO-SCAL",
            "names": {
                "es": "Tartrectomía simple",
                "en": "Simple scaling",
                "fr": "Détartrage simple",
                "ar": "\u062a\u0646\u0638\u064a\u0641 \u062c\u064a\u0631 \u0628\u0633\u064a\u0637",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-RAR",
            "names": {
                "es": "Raspado y alisado radicular (por cuadrante)",
                "en": "Root scaling and planing (per quadrant)",
                "fr": "Détartrage et surfaçage radiculaire (par quadrant)",
                "ar": "\u062a\u0642\u0644\u064a\u062d \u0648\u0643\u0634\u0637 \u062c\u0630\u0631\u064a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-SURG",
            "names": {
                "es": "Cirugía periodontal",
                "en": "Periodontal surgery",
                "fr": "Chirurgie parodontale",
                "ar": "\u062c\u0631\u0627\u062d\u0629 \u062f\u0648\u0627\u0639\u0645 \u0633\u0646\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("4500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-GRAFT",
            "names": {"es": "Injerto gingival", "en": "Gingival graft", "fr": "Greffe gingivale", "ar": "\u0637\u0639\u0645 \u0644\u062b\u0648\u064a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("3800.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-BONE",
            "names": {
                "es": "Regeneración ósea guiada",
                "en": "Guided bone regeneration",
                "fr": "Régénération osseuse guidée",
                "ar": "\u062a\u0631\u0645\u064a\u0645 \u0639\u0638\u0645\u064a \u0645\u0648\u062c\u0647",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("5500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-MAINT",
            "names": {
                "es": "Mantenimiento periodontal",
                "en": "Periodontal maintenance",
                "fr": "Entretien parodontal",
                "ar": "\u0635\u064a\u0627\u0646\u0629 \u062f\u0648\u0627\u0639\u0645 \u0633\u0646\u064a\u0629",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("900.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-CURET-SEXT",
            "names": {
                "es": "Curetaje por sextante",
                "en": "Curettage per sextant",
                "fr": "Curetage par sextant",
                "ar": "\u0643\u062d\u062a \u0628\u0627\u0644\u0633\u062f\u0633",
            },
            "treatment_scope": "multi_tooth",
            "default_price": Decimal("900.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-STUDY",
            "names": {
                "es": "Estudio periodontal (sondaje)",
                "en": "Periodontal probing study",
                "fr": "Étude parodontale (sondage)",
                "ar": "\u062f\u0631\u0627\u0633\u0629 \u062f\u0648\u0627\u0639\u0645 \u0633\u0646\u064a\u0629",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("700.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-SPLINT-RAR",
            "names": {
                "es": "Férula de contención post-RAR",
                "en": "Post-SRP retention splint",
                "fr": "Gouttière de contention post-DDR",
                "ar": "\u062c\u0628\u064a\u0631\u0629 \u062a\u062b\u0628\u064a\u062a \u0628\u0639\u062f \u0627\u0644\u062a\u0642\u0644\u064a\u062d",
            },
            "treatment_scope": "multi_tooth",
            "default_price": Decimal("1500.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "splint",
            "visualization_rules": [lateral_icon("splint", "#8B5CF6")],
            "visualization_config": {"color": "#8B5CF6"},
        },
        {
            "internal_code": "PERIO-GINGIV",
            "names": {"es": "Gingivectomía", "en": "Gingivectomy", "fr": "Gingivectomie", "ar": "\u0627\u0633\u062a\u0626\u0635\u0627\u0644 \u0644\u062b\u0629"},
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-SURG-RESECT",
            "names": {
                "es": "Cirugía periodontal resectiva",
                "en": "Resective periodontal surgery",
                "fr": "Chirurgie parodontale résécative",
                "ar": "\u062c\u0631\u0627\u062d\u0629 \u062f\u0648\u0627\u0639\u0645 \u0627\u0633\u062a\u0626\u0635\u0627\u0644\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("4800.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PERIO-SURG-REGEN",
            "names": {
                "es": "Cirugía periodontal regenerativa",
                "en": "Regenerative periodontal surgery",
                "fr": "Chirurgie parodontale régénérative",
                "ar": "\u062c\u0631\u0627\u062d\u0629 \u062f\u0648\u0627\u0639\u0645 \u062a\u0631\u0645\u064a\u0645\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("5800.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
    ],
    # ---------- Cirugía ----------
    "cirugia": [
        {
            "internal_code": "SURG-EXT-SIMPLE",
            "names": {
                "es": "Extracción simple",
                "en": "Simple extraction",
                "fr": "Extraction simple",
                "ar": "\u062e\u0644\u0639 \u0628\u0633\u064a\u0637",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("800.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": [lateral_icon("extraction", "#DC2626")],
            "visualization_config": {"color": "#DC2626"},
        },
        {
            "internal_code": "SURG-EXT-COMPLEX",
            "names": {
                "es": "Extracción compleja",
                "en": "Complex extraction",
                "fr": "Extraction compliquée",
                "ar": "\u062e\u0644\u0639 \u0645\u0639\u0642\u062f",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1400.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": [lateral_icon("extraction", "#DC2626")],
            "visualization_config": {"color": "#DC2626"},
        },
        {
            "internal_code": "SURG-EXT-3MOLAR",
            "names": {
                "es": "Extracción tercer molar",
                "en": "Wisdom tooth extraction",
                "fr": "Extraction de la dent de sagesse",
                "ar": "\u062e\u0644\u0639 \u0636\u0631\u0633 \u0639\u0642\u0644",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2000.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": [lateral_icon("extraction", "#DC2626")],
            "visualization_config": {"color": "#DC2626"},
        },
        {
            "internal_code": "SURG-EXT-OST",
            "names": {
                "es": "Extracción quirúrgica con ostectomía",
                "en": "Surgical extraction with osteotomy",
                "fr": "Extraction chirurgicale avec ostéotomie",
                "ar": "\u062e\u0644\u0639 \u062c\u0631\u0627\u062d\u064a \u0645\u0639 \u0642\u0637\u0639 \u0639\u0638\u0645",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2800.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": [lateral_icon("extraction", "#991B1B")],
            "visualization_config": {"color": "#991B1B"},
        },
        {
            "internal_code": "SURG-IMP-TI",
            "names": {
                "es": "Implante de titanio",
                "en": "Titanium implant",
                "fr": "Implant en titane",
                "ar": "\u0632\u0631\u0627\u0639\u0629 \u062a\u064a\u062a\u0627\u0646\u064a\u0648\u0645",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("11000.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "implant",
            "visualization_rules": [lateral_icon("implant", "#10B981")],
            "visualization_config": {"color": "#10B981"},
            "sessions": [
                {
                    "labels": {
                        "es": "Cirugía de implante",
                        "en": "Implant surgery",
                        "fr": "Chirurgie implantaire",
                    },
                    "default_price": Decimal("7000.00"),
                },
                {
                    "labels": {
                        "es": "Pilar de cicatrización",
                        "en": "Healing abutment",
                        "fr": "Pilier de cicatrisation",
                    },
                    "default_price": Decimal("1500.00"),
                },
                {
                    "labels": {
                        "es": "Colocación de corona",
                        "en": "Crown placement",
                        "fr": "Pose de couronne",
                    },
                    "default_price": Decimal("2500.00"),
                },
            ],
        },
        {
            "internal_code": "SURG-IMP-ZIR",
            "names": {
                "es": "Implante de zirconio",
                "en": "Zirconia implant",
                "fr": "Implant en zircone",
                "ar": "\u0632\u0631\u0627\u0639\u0629 \u0632\u0631\u0643\u0648\u0646",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("15000.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "implant",
            "visualization_rules": [lateral_icon("implant", "#14B8A6")],
            "visualization_config": {"color": "#14B8A6"},
        },
        {
            "internal_code": "SURG-SINUS",
            "names": {"es": "Elevación de seno", "en": "Sinus lift", "fr": "Élévation sinusienne", "ar": "\u0631\u0641\u0639 \u0627\u0644\u062c\u064a\u0628 \u0627\u0644\u0641\u0643\u064a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("8000.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-BONE-GRAFT",
            "names": {"es": "Injerto óseo", "en": "Bone graft", "fr": "Greffe osseuse", "ar": "\u0637\u0639\u0645 \u0639\u0638\u0645\u064a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("4500.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-APEC",
            "names": {"es": "Apicectomía", "en": "Apicoectomy", "fr": "Apicectomie", "ar": "\u0627\u0633\u062a\u0626\u0635\u0627\u0644 \u0642\u0645\u0629 \u0627\u0644\u062c\u0630\u0631"},
            "treatment_scope": "tooth",
            "default_price": Decimal("3200.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "apicoectomy",
            "visualization_rules": [lateral_icon("apicoectomy", "#F59E0B")],
            "visualization_config": {"color": "#F59E0B"},
        },
        {
            "internal_code": "SURG-FREN",
            "names": {"es": "Frenectomía", "en": "Frenectomy", "fr": "Frénectomie", "ar": "\u0627\u0633\u062a\u0626\u0635\u0627\u0644 \u0644\u062c\u0627\u0645"},
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-BIOPSY",
            "names": {"es": "Biopsia", "en": "Biopsy", "fr": "Biopsie", "ar": "\u062e\u0632\u0639\u0629"},
            "treatment_scope": "tooth",
            "default_price": Decimal("2200.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-CONN-GRAFT",
            "names": {
                "es": "Injerto de tejido conectivo",
                "en": "Connective tissue graft",
                "fr": "Greffe de tissu conjonctif",
                "ar": "\u0637\u0639\u0645 \u0646\u0633\u064a\u062c \u0636\u0627\u0645",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("4200.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-CROWN-LENGTH",
            "names": {
                "es": "Alargamiento coronario",
                "en": "Crown lengthening",
                "fr": "Allongement coronaire",
                "ar": "\u0625\u0637\u0627\u0644\u0629 \u062a\u0627\u062c\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("3800.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-CYST",
            "names": {"es": "Exéresis de quiste", "en": "Cyst removal", "fr": "Exérèse de kyste", "ar": "\u0627\u0633\u062a\u0626\u0635\u0627\u0644 \u0643\u064a\u0633"},
            "treatment_scope": "tooth",
            "default_price": Decimal("5500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "apicoectomy",
            "visualization_rules": [lateral_icon("apicoectomy", "#F59E0B")],
            "visualization_config": {"color": "#F59E0B"},
        },
        {
            "internal_code": "SURG-EXT-INCLUIDO",
            "names": {
                "es": "Extracción de pieza incluida",
                "en": "Impacted tooth extraction",
                "fr": "Extraction de dent incluse",
                "ar": "\u062e\u0644\u0639 \u0633\u0646 \u0645\u0637\u0645\u0648\u0631",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2500.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": [lateral_icon("extraction", "#DC2626")],
            "visualization_config": {"color": "#DC2626"},
        },
        {
            "internal_code": "SURG-BONE-REGUL",
            "names": {
                "es": "Regularización ósea",
                "en": "Bone reshaping",
                "fr": "Régularisation osseuse",
                "ar": "\u062a\u0633\u0648\u064a\u0629 \u0639\u0638\u0645\u064a\u0629",
            },
            "treatment_scope": "multi_tooth",
            "default_price": Decimal("2200.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-PRP",
            "names": {
                "es": "Plasma rico en plaquetas",
                "en": "Platelet-rich plasma",
                "fr": "Plasma riche en plaquettes",
                "ar": "\u0628\u0644\u0627\u0632\u0645\u0627 \u063a\u0646\u064a\u0629 \u0628\u0627\u0644\u0635\u0641\u0627\u0626\u062d",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-PERIIMP",
            "names": {
                "es": "Tratamiento de periimplantitis",
                "en": "Peri-implantitis treatment",
                "fr": "Traitement de péri-implantite",
                "ar": "\u0639\u0644\u0627\u062c \u0627\u0644\u062a\u0647\u0627\u0628 \u062d\u0648\u0644 \u0627\u0644\u0632\u0631\u0639\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("4200.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-BONE-VERT",
            "names": {
                "es": "Aumento óseo vertical",
                "en": "Vertical bone augmentation",
                "fr": "Augmentation osseuse verticale",
                "ar": "\u0632\u064a\u0627\u062f\u0629 \u0639\u0638\u0645\u064a\u0629 \u0639\u0645\u0648\u062f\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("7500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-BONE-HORIZ",
            "names": {
                "es": "Aumento óseo horizontal",
                "en": "Horizontal bone augmentation",
                "fr": "Augmentation osseuse horizontale",
                "ar": "\u0632\u064a\u0627\u062f\u0629 \u0639\u0638\u0645\u064a\u0629 \u0623\u0641\u0642\u064a\u0629",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("6500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "SURG-SINUS-CLOSED",
            "names": {
                "es": "Elevación de seno cerrada (atraumática)",
                "en": "Closed sinus lift (atraumatic)",
                "fr": "Élévation sinusienne fermée (atraumatique)",
                "ar": "\u0631\u0641\u0639 \u062c\u064a\u0628 \u0641\u0643\u064a \u0645\u063a\u0644\u0642",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("5000.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
    ],
    # ---------- Ortodoncia ----------
    "ortodoncia": [
        {
            "internal_code": "ORTO-METAL",
            "names": {
                "es": "Ortodoncia brackets metálicos",
                "en": "Metal braces",
                "fr": "Bagues métalliques",
                "ar": "\u062a\u0642\u0648\u064a\u0645 \u0645\u0639\u062f\u0646\u064a",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("25000.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-CERAM",
            "names": {
                "es": "Ortodoncia brackets estéticos",
                "en": "Ceramic braces",
                "fr": "Bagues esthétiques",
                "ar": "\u062a\u0642\u0648\u064a\u0645 \u062a\u062c\u0645\u064a\u0644\u064a",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("35000.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-LINGUAL",
            "names": {"es": "Ortodoncia lingual", "en": "Lingual braces", "fr": "Bagues linguales", "ar": "\u062a\u0642\u0648\u064a\u0645 \u0644\u063a\u0648\u064a"},
            "treatment_scope": "global_mouth",
            "default_price": Decimal("55000.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-INV-LITE",
            "names": {"es": "Invisalign Lite", "en": "Invisalign Lite", "fr": "Invisalign Lite", "ar": "\u0625\u0646\u0641\u064a\u0632\u0627\u0644\u0627\u064a\u0646 \u0644\u0627\u064a\u062a"},
            "treatment_scope": "global_mouth",
            "default_price": Decimal("29000.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-INV-FULL",
            "names": {"es": "Invisalign Full", "en": "Invisalign Full", "fr": "Invisalign Full", "ar": "\u0625\u0646\u0641\u064a\u0632\u0627\u0644\u0627\u064a\u0646 \u0643\u0627\u0645\u0644"},
            "treatment_scope": "global_mouth",
            "default_price": Decimal("45000.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-BRACK",
            "names": {
                "es": "Bracket individual (reposición)",
                "en": "Bracket (replacement)",
                "fr": "Bracket individuel (remplacement)",
                "ar": "\u0642\u0648\u0633 \u062a\u0642\u0648\u064a\u0645 \u0641\u0631\u062f\u064a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("450.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "bracket",
            "visualization_rules": [lateral_icon("bracket", "#475569")],
            "visualization_config": {"color": "#475569"},
        },
        {
            "internal_code": "ORTO-REVIEW",
            "names": {
                "es": "Revisión de ortodoncia",
                "en": "Orthodontic review",
                "fr": "Contrôle d'orthodontie",
                "ar": "\u0645\u0631\u0627\u062c\u0639\u0629 \u062a\u0642\u0648\u064a\u0645",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("400.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-RET-FIX",
            "names": {"es": "Retenedor fijo", "en": "Fixed retainer", "fr": "Contention fixe", "ar": "\u0645\u062b\u0628\u062a \u062b\u0627\u0628\u062a"},
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "retainer",
            "visualization_rules": [lateral_icon("retainer", "#0EA5E9")],
            "visualization_config": {"color": "#0EA5E9"},
        },
        {
            "internal_code": "ORTO-RET-REM",
            "names": {
                "es": "Retenedor removible",
                "en": "Removable retainer",
                "fr": "Contention amovible",
                "ar": "\u0645\u062b\u0628\u062a \u0645\u062a\u062d\u0631\u0643",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("1200.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-ATTACH",
            "names": {
                "es": "Ataches de Invisalign",
                "en": "Invisalign attachments",
                "fr": "Attachements Invisalign",
                "ar": "\u0645\u0644\u062d\u0642\u0627\u062a \u0625\u0646\u0641\u064a\u0632\u0627\u0644\u0627\u064a\u0646",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "attachment",
            "visualization_rules": [lateral_icon("attachment", "#0891B2")],
            "visualization_config": {"color": "#0891B2"},
        },
        {
            "internal_code": "ORTO-BRACK-CEMENT",
            "names": {
                "es": "Cementado de bracket",
                "en": "Bracket bonding",
                "fr": "Collage de bracket",
                "ar": "\u0644\u0635\u0642 \u0642\u0648\u0633",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("350.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "bracket",
            "visualization_rules": [lateral_icon("bracket", "#475569")],
            "visualization_config": {"color": "#475569"},
        },
        {
            "internal_code": "ORTO-BRACK-DEBOND",
            "names": {
                "es": "Descementado de brackets",
                "en": "Bracket removal",
                "fr": "Dépose des bagues",
                "ar": "\u0641\u0643 \u0627\u0644\u062a\u0642\u0648\u064a\u0645",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("1200.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-SEPARATOR",
            "names": {
                "es": "Separadores ortodóncicos",
                "en": "Orthodontic separators",
                "fr": "Séparateurs orthodontiques",
                "ar": "\u0641\u0648\u0627\u0635\u0644 \u062a\u0642\u0648\u064a\u0645\u064a\u0629",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("500.00"),
            "default_duration_minutes": 20,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-PALATAL-EXP",
            "names": {
                "es": "Expansor palatino",
                "en": "Palatal expander",
                "fr": "Dilatateur palatin",
                "ar": "\u0645\u0648\u0633\u0639 \u062d\u0646\u0643\u064a",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("4500.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "ORTO-TAD",
            "names": {
                "es": "Microtornillo / anclaje esquelético temporal (TAD)",
                "en": "Temporary anchorage device (TAD)",
                "fr": "Dispositif d'ancrage temporaire (TAD)",
                "ar": "\u0628\u0631\u063a\u064a \u0635\u063a\u064a\u0631 \u062a\u0642\u0648\u064a\u0645\u064a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2500.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
        },
    ],
    # ---------- Estética ----------
    "estetica": [
        {
            "internal_code": "EST-BLAN-AMB",
            "names": {
                "es": "Blanqueamiento ambulatorio",
                "en": "At-home whitening",
                "fr": "Blanchiment à domicile",
                "ar": "\u062a\u0628\u064a\u064a\u0636 \u0645\u0646\u0632\u0644\u064a",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("2500.00"),
            "default_duration_minutes": 30,
            "vat_type": "standard",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "EST-BLAN-CLIN",
            "names": {
                "es": "Blanqueamiento en clínica",
                "en": "In-office whitening",
                "fr": "Blanchiment en cabinet",
                "ar": "\u062a\u0628\u064a\u064a\u0636 \u0639\u064a\u0627\u062f\u0629",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("4000.00"),
            "default_duration_minutes": 90,
            "vat_type": "standard",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "EST-BLAN-COMBO",
            "names": {
                "es": "Blanqueamiento combinado",
                "en": "Combined whitening",
                "fr": "Blanchiment combiné",
                "ar": "\u062a\u0628\u064a\u064a\u0636 \u0645\u062f\u0645\u062c",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("5500.00"),
            "default_duration_minutes": 120,
            "vat_type": "standard",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "EST-MICROAB",
            "names": {"es": "Microabrasión", "en": "Microabrasion", "fr": "Microabrasion", "ar": "\u062a\u0622\u0643\u0644 \u062f\u0642\u064a\u0642"},
            "treatment_scope": "tooth",
            "default_price": Decimal("1200.00"),
            "default_duration_minutes": 45,
            "vat_type": "standard",
            "pricing_strategy": "per_tooth",
        },
        {
            "internal_code": "EST-REMIN",
            "names": {
                "es": "Remineralización estética",
                "en": "Aesthetic remineralization",
                "fr": "Reminéralisation esthétique",
                "ar": "\u0625\u0639\u0627\u062f\u0629 \u062a\u0645\u0639\u062f\u0646 \u062a\u062c\u0645\u064a\u0644\u064a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("900.00"),
            "default_duration_minutes": 30,
            "vat_type": "standard",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "EST-COMP-AESTH",
            "names": {
                "es": "Reconstrucción estética con composite",
                "en": "Aesthetic composite reconstruction",
                "fr": "Reconstruction esthétique en composite",
                "ar": "\u0625\u0639\u0627\u062f\u0629 \u0628\u0646\u0627\u0621 \u062a\u062c\u0645\u064a\u0644\u064a \u0628\u0627\u0644\u0643\u0648\u0645\u0628\u0648\u0632\u064a\u062a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("2200.00"),
            "default_duration_minutes": 60,
            "vat_type": "standard",
            "pricing_strategy": "per_tooth",
        },
        {
            "internal_code": "EST-PIG-REMOVE",
            "names": {
                "es": "Eliminación de pigmentación",
                "en": "Pigmentation removal",
                "fr": "Élimination des pigmentations",
                "ar": "\u0625\u0632\u0627\u0644\u0629 \u062a\u0635\u0628\u063a",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("900.00"),
            "default_duration_minutes": 30,
            "vat_type": "standard",
            "pricing_strategy": "flat",
        },
    ],
    # ---------- Prótesis ----------
    "protesis": [
        {
            "internal_code": "PROT-FULL-SUP",
            "names": {
                "es": "Prótesis completa superior",
                "en": "Full upper denture",
                "fr": "Prothèse complète supérieure",
                "ar": "\u0637\u0642\u0645 \u0643\u0627\u0645\u0644 \u0639\u0644\u0648\u064a",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("9000.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PROT-FULL-INF",
            "names": {
                "es": "Prótesis completa inferior",
                "en": "Full lower denture",
                "fr": "Prothèse complète inférieure",
                "ar": "\u0637\u0642\u0645 \u0643\u0627\u0645\u0644 \u0633\u0641\u0644\u064a",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("9000.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PROT-PART-METAL",
            "names": {
                "es": "Prótesis parcial esquelética",
                "en": "Partial metal denture",
                "fr": "Prothèse partielle squelettique",
                "ar": "\u0637\u0642\u0645 \u062c\u0632\u0626\u064a \u0645\u0639\u062f\u0646\u064a",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("7500.00"),
            "default_duration_minutes": 90,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PROT-PART-ACR",
            "names": {
                "es": "Prótesis parcial acrílica",
                "en": "Partial acrylic denture",
                "fr": "Prothèse partielle acrylique",
                "ar": "\u0637\u0642\u0645 \u062c\u0632\u0626\u064a \u0623\u0643\u0631\u064a\u0644\u064a\u0643",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("4500.00"),
            "default_duration_minutes": 75,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PROT-OVERDENT",
            "names": {
                "es": "Sobredentadura sobre implantes",
                "en": "Implant-supported overdenture",
                "fr": "Surprothèse sur implants",
                "ar": "\u0637\u0642\u0645 \u0639\u0644\u0649 \u0632\u0631\u0639\u0627\u062a",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("18000.00"),
            "default_duration_minutes": 120,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PROT-REBASE",
            "names": {
                "es": "Rebasado de prótesis",
                "en": "Denture reline",
                "fr": "Rebasage de prothèse",
                "ar": "\u0625\u0639\u0627\u062f\u0629 \u0642\u0627\u0639\u062f\u0629 \u0637\u0642\u0645",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1200.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PROT-REPAIR",
            "names": {
                "es": "Reparación de prótesis",
                "en": "Denture repair",
                "fr": "Réparation de prothèse",
                "ar": "\u0625\u0635\u0644\u0627\u062d \u0637\u0642\u0645",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("800.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PROT-PROV-REMOV",
            "names": {
                "es": "Prótesis provisional removible",
                "en": "Provisional removable denture",
                "fr": "Prothèse provisoire amovible",
                "ar": "\u0637\u0642\u0645 \u0645\u0624\u0642\u062a \u0645\u062a\u062d\u0631\u0643",
            },
            "treatment_scope": "global_arch",
            "default_price": Decimal("3500.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PROT-OCC-ADJ",
            "names": {
                "es": "Ajuste oclusal",
                "en": "Occlusal adjustment",
                "fr": "Ajustement occlusal",
                "ar": "\u062a\u0639\u062f\u064a\u0644 \u0625\u0637\u0628\u0627\u0642\u064a",
            },
            "treatment_scope": "global_mouth",
            "default_price": Decimal("600.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
    ],
    # ---------- Odontopediatría ----------
    "pediatrica": [
        {
            "internal_code": "PED-FLUOR",
            "names": {
                "es": "Fluorización pediátrica",
                "en": "Pediatric fluoride",
                "fr": "Fluoration pédiatrique",
                "ar": "\u0641\u0644\u0648\u0631\u0627\u064a\u062f \u0623\u0637\u0641\u0627\u0644",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("250.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PED-SEAL",
            "names": {
                "es": "Sellador pediátrico",
                "en": "Pediatric sealant",
                "fr": "Scellement de sillons pédiatrique",
                "ar": "\u0633\u064a\u0644\u0631 \u0623\u0637\u0641\u0627\u0644",
            },
            "treatment_scope": "tooth",
            "requires_surfaces": True,
            "default_price": Decimal("250.00"),
            "default_duration_minutes": 15,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "sealant",
            "visualization_rules": [occlusal_surface("#06B6D4", "solid_fill")],
            "visualization_config": {"color": "#06B6D4"},
        },
        {
            "internal_code": "PED-PULPOTOMY",
            "names": {"es": "Pulpotomía", "en": "Pulpotomy", "fr": "Pulpotomie", "ar": "\u0628\u0636\u0639 \u0627\u0644\u0644\u0628"},
            "treatment_scope": "tooth",
            "default_price": Decimal("1500.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_half",
            "visualization_rules": [pulp_fill("#A78BFA", "partial_1_2")],
            "visualization_config": {"color": "#A78BFA"},
        },
        {
            "internal_code": "PED-CROWN-SS",
            "names": {
                "es": "Corona preformada pediátrica",
                "en": "Stainless steel crown",
                "fr": "Couronne préformée pédiatrique",
                "ar": "\u062a\u0627\u062c \u0623\u0637\u0641\u0627\u0644 \u0645\u0639\u062f\u0646\u064a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1800.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "per_tooth",
            "odontogram_treatment_type": "crown",
            "visualization_rules": [pattern_fill("diagonal_stripes", "#9CA3AF")],
            "visualization_config": {"color": "#9CA3AF"},
        },
        {
            "internal_code": "PED-SPACE",
            "names": {
                "es": "Mantenedor de espacio simple",
                "en": "Simple space maintainer",
                "fr": "Mainteneur d'espace simple",
                "ar": "\u062d\u0627\u0641\u0638 \u0645\u0633\u0627\u062d\u0629 \u0628\u0633\u064a\u0637",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1500.00"),
            "default_duration_minutes": 45,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PED-SPACE-COMPOUND",
            "names": {
                "es": "Mantenedor de espacio compuesto",
                "en": "Compound space maintainer",
                "fr": "Mainteneur d'espace composé",
                "ar": "\u062d\u0627\u0641\u0638 \u0645\u0633\u0627\u062d\u0629 \u0645\u0631\u0643\u0628",
            },
            "treatment_scope": "multi_tooth",
            "default_price": Decimal("2200.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
        },
        {
            "internal_code": "PED-EXT-TEMP",
            "names": {
                "es": "Extracción de pieza temporal",
                "en": "Primary tooth extraction",
                "fr": "Extraction de dent temporaire",
                "ar": "\u062e\u0644\u0639 \u0633\u0646 \u0645\u0624\u0642\u062a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("550.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "extraction",
            "visualization_rules": [lateral_icon("extraction", "#DC2626")],
            "visualization_config": {"color": "#DC2626"},
        },
        {
            "internal_code": "PED-FILL-TEMP",
            "names": {
                "es": "Obturación en dentición temporal",
                "en": "Primary tooth filling",
                "fr": "Obturation sur dent temporaire",
                "ar": "\u062d\u0634\u0648\u0629 \u0633\u0646 \u0645\u0624\u0642\u062a",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("450.00"),
            "default_duration_minutes": 30,
            "vat_type": "exempt",
            "pricing_strategy": "per_surface",
            "surface_prices": {
                "1": "450.00",
                "2": "650.00",
                "3": "850.00",
                "4": "950.00",
                "5": "1050.00",
            },
            "requires_surfaces": True,
            "odontogram_treatment_type": "filling_composite",
            "visualization_rules": [occlusal_surface("#3B82F6", "solid_fill")],
            "visualization_config": {"color": "#3B82F6"},
        },
        {
            "internal_code": "PED-PULPECTOMY",
            "names": {
                "es": "Pulpectomía pediátrica",
                "en": "Pediatric pulpectomy",
                "fr": "Pulpectomie pédiatrique",
                "ar": "\u0627\u0633\u062a\u0626\u0635\u0627\u0644 \u0644\u0628 \u0623\u0637\u0641\u0627\u0644",
            },
            "treatment_scope": "tooth",
            "default_price": Decimal("1600.00"),
            "default_duration_minutes": 60,
            "vat_type": "exempt",
            "pricing_strategy": "flat",
            "odontogram_treatment_type": "root_canal_full",
            "visualization_rules": [pulp_fill("#A78BFA", "full")],
            "visualization_config": {"color": "#A78BFA"},
        },
    ],
}


# ============================================================================
# Seeding logic
# ============================================================================


async def _ensure_vat_types(db: AsyncSession, clinic_id: UUID) -> dict[str, UUID]:
    vat_type_map: dict[str, UUID] = {}
    for vat_data in VAT_TYPES:
        existing = await db.execute(
            select(VatType).where(
                VatType.clinic_id == clinic_id,
                VatType.rate == vat_data["rate"],
            )
        )
        vat = existing.scalar_one_or_none()
        if not vat:
            vat = VatType(
                clinic_id=clinic_id,
                names=vat_data["names"],
                rate=vat_data["rate"],
                is_default=vat_data["is_default"],
                is_system=True,
            )
            db.add(vat)
            await db.flush()
        vat_type_map[vat_data["key"]] = vat.id
    return vat_type_map


async def seed_catalog(db: AsyncSession, clinic_id: UUID) -> dict:
    """Seed catalog items for a clinic. Idempotent (skips existing internal_codes)."""
    vat_type_map = await _ensure_vat_types(db, clinic_id)

    categories_created = 0
    items_created = 0
    category_map: dict[str, UUID] = {}

    for cat_data in CATEGORIES:
        existing = await db.execute(
            select(TreatmentCategory).where(
                TreatmentCategory.clinic_id == clinic_id,
                TreatmentCategory.key == cat_data["key"],
            )
        )
        category = existing.scalar_one_or_none()
        if not category:
            category = TreatmentCategory(clinic_id=clinic_id, is_system=True, **cat_data)
            db.add(category)
            await db.flush()
            categories_created += 1
        category_map[cat_data["key"]] = category.id

    for category_key, treatments in TREATMENTS.items():
        category_id = category_map.get(category_key)
        if not category_id:
            continue

        for treatment_raw in treatments:
            treatment_data = dict(treatment_raw)

            odontogram_type = treatment_data.pop("odontogram_treatment_type", None)
            viz_rules = treatment_data.pop("visualization_rules", None)
            viz_config = treatment_data.pop("visualization_config", None) or {}
            vat_type_key = treatment_data.pop("vat_type", "exempt")
            vat_type_id = vat_type_map.get(vat_type_key, vat_type_map.get("exempt"))
            session_template = treatment_data.pop("sessions", None)

            existing = await db.execute(
                select(TreatmentCatalogItem).where(
                    TreatmentCatalogItem.clinic_id == clinic_id,
                    TreatmentCatalogItem.internal_code == treatment_data["internal_code"],
                )
            )
            if existing.scalar_one_or_none():
                continue

            item = TreatmentCatalogItem(
                clinic_id=clinic_id,
                category_id=category_id,
                vat_type_id=vat_type_id,
                is_system=True,
                **treatment_data,
            )
            db.add(item)
            await db.flush()

            if odontogram_type and viz_rules:
                mapping = TreatmentOdontogramMapping(
                    clinic_id=clinic_id,
                    catalog_item_id=item.id,
                    odontogram_treatment_type=odontogram_type,
                    visualization_rules=viz_rules,
                    visualization_config=viz_config,
                    clinical_category=category_key,
                )
                db.add(mapping)

            # Per-session template (multi-session billing). Treatment plans
            # snapshot this when the item is added — see ``treatment_plan``.
            if session_template:
                for idx, session_data in enumerate(session_template, start=1):
                    db.add(
                        CatalogItemSession(
                            catalog_item_id=item.id,
                            sequence=session_data.get("sequence") or idx,
                            labels=session_data.get("labels") or {},
                            default_price=session_data["default_price"],
                        )
                    )

            items_created += 1

    await db.flush()

    return {
        "categories": categories_created,
        "items": items_created,
        "vat_types": len(vat_type_map),
    }


async def seed_all_clinics(db: AsyncSession) -> dict:
    """Seed catalog for every clinic in the database."""
    from app.core.auth.models import Clinic

    result = await db.execute(select(Clinic))
    clinics = result.scalars().all()

    summary = {}
    for clinic in clinics:
        summary[str(clinic.id)] = await seed_catalog(db, clinic.id)
    return summary
