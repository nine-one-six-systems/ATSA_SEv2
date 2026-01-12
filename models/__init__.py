from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.client import Client
from models.document import Document
from models.extracted_data import ExtractedData
from models.analysis import AnalysisResult, AnalysisSummary
from models.irs_reference import IRSReference
from models.tax_tables import TaxBracket, StandardDeduction

__all__ = ['db', 'Client', 'Document', 'ExtractedData', 'AnalysisResult', 'AnalysisSummary', 'IRSReference', 'TaxBracket', 'StandardDeduction']

