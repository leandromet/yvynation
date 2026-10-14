"""CPCAD's fixed-list (coded-domain) values, in the three page languages.

The register publishes these as English labels (``PA_OECM_DF``, ``STATUS``,
``GOV_TYPE``, ``OWNER_TYPE`` and the two non-category ``IUCN_CAT`` values), and
the GeoPackage stores them that way. They are a small closed vocabulary, so
they can be translated safely at display time — the stored value stays the
register's own, and a value this table does not know passes through unchanged.

Deliberately **not** here: the park's own designation (``TYPE_E``, e.g.
"A - Park"), its managing authority, owner and names. Those are free text a
provider wrote, and an official register's wording is not ours to rephrase.
"""

from __future__ import annotations

from typing import Dict

#: ``{english value: {"pt": …, "fr": …}}`` per field.
TABLES: Dict[str, Dict[str, Dict[str, str]]] = {
    "pa_oecm": {
        "Protected area (PA)": {"pt": "Área protegida (AP)", "fr": "Aire protégée (AP)"},
        "Other effective area-based conservation measure (OECM)": {
            "pt": "Outra medida eficaz de conservação baseada em área (OMEC)",
            "fr": "Autre mesure efficace de conservation par zone (AMCEZ)"},
        "Interim - protected area (PA)": {
            "pt": "Provisória — área protegida (AP)", "fr": "Provisoire — aire protégée (AP)"},
        "Interim - other effective area-based conservation measure (OECM)": {
            "pt": "Provisória — outra medida eficaz de conservação (OMEC)",
            "fr": "Provisoire — autre mesure efficace de conservation (AMCEZ)"},
        "Not applicable": {"pt": "Não se aplica", "fr": "Sans objet"},
    },
    "status": {
        "Delisted": {"pt": "Excluída da lista", "fr": "Radiée"},
        "Designated": {"pt": "Designada", "fr": "Désignée"},
        "Established": {"pt": "Estabelecida", "fr": "Établie"},
        "Interim": {"pt": "Provisória", "fr": "Provisoire"},
        "Inscribed": {"pt": "Inscrita", "fr": "Inscrite"},
        "Adopted": {"pt": "Adotada", "fr": "Adoptée"},
    },
    "governance": {
        "National government": {"pt": "Governo nacional", "fr": "Gouvernement national"},
        "Sub-national government": {"pt": "Governo subnacional", "fr": "Gouvernement infranational"},
        "Government-delegated management": {
            "pt": "Gestão delegada pelo governo", "fr": "Gestion déléguée par le gouvernement"},
        "Transboundary governance": {"pt": "Governança transfronteiriça", "fr": "Gouvernance transfrontalière"},
        "Collaborative governance": {"pt": "Governança colaborativa", "fr": "Gouvernance collaborative"},
        "Joint governance": {"pt": "Governança conjunta", "fr": "Gouvernance conjointe"},
        "Individual landowners": {"pt": "Proprietários individuais", "fr": "Propriétaires individuels"},
        "Non-profit organizations": {
            "pt": "Organizações sem fins lucrativos", "fr": "Organismes sans but lucratif"},
        "For-profit organizations": {
            "pt": "Organizações com fins lucrativos", "fr": "Organisations à but lucratif"},
        "Indigenous peoples": {"pt": "Povos indígenas", "fr": "Peuples autochtones"},
        "Local communities": {"pt": "Comunidades locais", "fr": "Communautés locales"},
        "Not reported": {"pt": "Não informado", "fr": "Non déclaré"},
    },
    "owner": {
        "Federal": {"pt": "Federal", "fr": "Fédéral"},
        "Provincial / territorial": {"pt": "Provincial / territorial", "fr": "Provincial / territorial"},
        "Municipal": {"pt": "Municipal", "fr": "Municipal"},
        "Indigenous": {"pt": "Indígena", "fr": "Autochtone"},
        "Communal": {"pt": "Comunitária", "fr": "Communautaire"},
        "Individual landowners": {"pt": "Proprietários individuais", "fr": "Propriétaires individuels"},
        "For-profit organizations": {
            "pt": "Organizações com fins lucrativos", "fr": "Organisations à but lucratif"},
        "Non-profit organizations": {
            "pt": "Organizações sem fins lucrativos", "fr": "Organismes sans but lucratif"},
        "Joint ownership": {"pt": "Propriedade conjunta", "fr": "Propriété conjointe"},
        "Multiple ownership": {"pt": "Propriedade múltipla", "fr": "Propriété multiple"},
        "Contested": {"pt": "Contestada", "fr": "Contestée"},
        "Not reported": {"pt": "Não informado", "fr": "Non déclaré"},
    },
    "iucn": {
        "Not reported": {"pt": "Não informada", "fr": "Non déclarée"},
        "Not applicable": {"pt": "Não se aplica", "fr": "Sans objet"},
    },
}


def translate(table: str, value: str, lang: str) -> str:
    """The value in ``lang`` (unchanged for English or an unknown value)."""
    return TABLES[table].get(value, {}).get(lang, value)
