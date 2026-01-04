from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.client import Client
from models.document import Document
from models.extracted_data import ExtractedData
from models.analysis import AnalysisResult
from models.irs_reference import IRSReference

__all__ = ['db', 'Client', 'Document', 'ExtractedData', 'AnalysisResult', 'IRSReference']

