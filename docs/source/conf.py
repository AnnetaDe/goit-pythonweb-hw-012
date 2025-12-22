# Configuration file for the Sphinx documentation builder.

import os
import sys

sys.path.insert(0, os.path.abspath('../../contacts_api'))

# -- Project information -----------------------------------------------------

project = 'Contacts API'
copyright = '2025, Mykola Kushka'
author = 'Mykola Kushka'
release = '1.0.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # Для Google-style та NumPy-style docstrings
    'sphinx.ext.viewcode',  # Додати посилання на код
]

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'special-members': '__init__',
    'show-inheritance': True,
}

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'  # або 'sphinx_rtd_theme', якщо встановлено
html_static_path = ['_static']
