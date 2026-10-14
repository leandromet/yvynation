"""Yvynation's citation constants, for the Canada page's cite dialog."""

APP_URL = "https://yvynation.umaterra.com.br"
APP_YEAR = "2026"

AUTHORS = [
    ("Leandro Meneguelli Biondo",
     "University of British Columbia Okanagan (UBC Okanagan), Canadá"),
]

AUTHORS_EN = [(name, inst.replace("Canadá", "Canada")) for name, inst in AUTHORS]
