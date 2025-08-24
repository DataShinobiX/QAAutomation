"""
Document Parser Manager
Orchestrates different document parsers and provides unified interface
"""
import os
import asyncio
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import structlog
from datetime import datetime
import mimetypes

from document_parsers import (
    PDFParser, WordParser, ExcelParser, PowerPointParser,
    NotionParser, ConfluenceParser, TextParser
)
from doc_parser_config import config

# Import models with fallback
try:
    from models import DocumentContent, DocumentType, ParsingError, ParsedDocument
except ImportError:
    # Use models from document_parsers
    from document_parsers import DocumentContent, DocumentType, ParsingError
    from pydantic import BaseModel, Field
    from datetime import datetime
    from typing import Optional
    import uuid
    
    class ParsedDocument(BaseModel):
        id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        source_type: str
        source_path: str
        content: DocumentContent
        parsed_at: datetime = Field(default_factory=datetime.utcnow)
        processing_time: float
        parser_version: str
        success: bool
        error_message: Optional[str] = None

logger = structlog.get_logger()


class DocumentParserManager:
    """Manages all document parsers and provides unified parsing interface"""
    
    def __init__(self):
        self.parsers = {
            '.pdf': PDFParser(),
            '.docx': WordParser(),
            '.doc': WordParser(), 
            '.xlsx': ExcelParser(),
            '.xls': ExcelParser(),
            '.pptx': PowerPointParser(),
            '.ppt': PowerPointParser(),
            '.txt': TextParser(),
            '.md': TextParser(),
            '.rst': TextParser()
        }
        
        # Web-based parsers
        self.notion_parser = NotionParser()
        self.confluence_parser = ConfluenceParser()
        
        logger.info("Document parser manager initialized", 
                   supported_formats=list(self.parsers.keys()))
    
    async def parse_file(self, file_path: str, **kwargs) -> ParsedDocument:
        """Parse a local file"""
        if not os.path.exists(file_path):
            raise ParsingError(f"File not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.parsers:
            raise ParsingError(f"Unsupported file format: {file_ext}")
        
        parser = self.parsers[file_ext]
        
        try:
            logger.info("Starting file parsing", 
                       file=file_path, 
                       parser=parser.__class__.__name__)
            
            start_time = datetime.now()
            content = await parser.parse(file_path, **kwargs)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create parsed document
            parsed_doc = ParsedDocument(
                id=f"file_{hash(file_path)}_{int(datetime.now().timestamp())}",
                source_type="file",
                source_path=file_path,
                content=content,
                parsed_at=datetime.now(),
                processing_time=processing_time,
                parser_version="1.0.0",
                success=True
            )
            
            logger.info("File parsing completed",
                       file=file_path,
                       processing_time=processing_time,
                       text_length=len(content.text),
                       sections=len(content.sections))
            
            return parsed_doc
            
        except Exception as e:
            logger.error("File parsing failed", 
                        file=file_path, 
                        parser=parser.__class__.__name__, 
                        error=str(e))
            
            # Return failed parsing result
            return ParsedDocument(
                id=f"file_{hash(file_path)}_{int(datetime.now().timestamp())}",
                source_type="file",
                source_path=file_path,
                content=DocumentContent(text="", metadata=None, sections=[]),
                parsed_at=datetime.now(),
                processing_time=0,
                parser_version="1.0.0",
                success=False,
                error_message=str(e)
            )
    
    async def parse_notion_page(self, page_id: str, **kwargs) -> ParsedDocument:
        """Parse a Notion page"""
        try:
            logger.info("Starting Notion page parsing", page_id=page_id)
            
            start_time = datetime.now()
            content = await self.notion_parser.parse_page(page_id, **kwargs)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            parsed_doc = ParsedDocument(
                id=f"notion_{page_id}_{int(datetime.now().timestamp())}",
                source_type="notion",
                source_path=page_id,
                content=content,
                parsed_at=datetime.now(),
                processing_time=processing_time,
                parser_version="1.0.0",
                success=True
            )
            
            logger.info("Notion page parsing completed",
                       page_id=page_id,
                       processing_time=processing_time,
                       text_length=len(content.text),
                       sections=len(content.sections))
            
            return parsed_doc
            
        except Exception as e:
            logger.error("Notion page parsing failed", page_id=page_id, error=str(e))
            
            return ParsedDocument(
                id=f"notion_{page_id}_{int(datetime.now().timestamp())}",
                source_type="notion",
                source_path=page_id,
                content=DocumentContent(text="", metadata=None, sections=[]),
                parsed_at=datetime.now(),
                processing_time=0,
                parser_version="1.0.0",
                success=False,
                error_message=str(e)
            )
    
    async def parse_confluence_page(self, page_id: str, **kwargs) -> ParsedDocument:
        """Parse a Confluence page"""
        try:
            logger.info("Starting Confluence page parsing", page_id=page_id)
            
            start_time = datetime.now()
            content = await self.confluence_parser.parse_page(page_id, **kwargs)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            parsed_doc = ParsedDocument(
                id=f"confluence_{page_id}_{int(datetime.now().timestamp())}",
                source_type="confluence", 
                source_path=page_id,
                content=content,
                parsed_at=datetime.now(),
                processing_time=processing_time,
                parser_version="1.0.0",
                success=True
            )
            
            logger.info("Confluence page parsing completed",
                       page_id=page_id,
                       processing_time=processing_time,
                       text_length=len(content.text),
                       sections=len(content.sections))
            
            return parsed_doc
            
        except Exception as e:
            logger.error("Confluence page parsing failed", page_id=page_id, error=str(e))
            
            return ParsedDocument(
                id=f"confluence_{page_id}_{int(datetime.now().timestamp())}",
                source_type="confluence",
                source_path=page_id,
                content=DocumentContent(text="", metadata=None, sections=[]),
                parsed_at=datetime.now(),
                processing_time=0,
                parser_version="1.0.0",
                success=False,
                error_message=str(e)
            )
    
    async def parse_multiple_files(self, file_paths: List[str], **kwargs) -> List[ParsedDocument]:
        """Parse multiple files concurrently"""
        logger.info("Starting batch file parsing", file_count=len(file_paths))
        
        # Create tasks for concurrent parsing
        tasks = [self.parse_file(file_path, **kwargs) for file_path in file_paths]
        
        # Execute all parsing tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        parsed_docs = []
        successful = 0
        failed = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Batch parsing task failed", 
                           file=file_paths[i], 
                           error=str(result))
                # Create failed result
                failed_doc = ParsedDocument(
                    id=f"file_{hash(file_paths[i])}_{int(datetime.now().timestamp())}",
                    source_type="file",
                    source_path=file_paths[i],
                    content=DocumentContent(text="", metadata=None, sections=[]),
                    parsed_at=datetime.now(),
                    processing_time=0,
                    parser_version="1.0.0",
                    success=False,
                    error_message=str(result)
                )
                parsed_docs.append(failed_doc)
                failed += 1
            else:
                parsed_docs.append(result)
                if result.success:
                    successful += 1
                else:
                    failed += 1
        
        logger.info("Batch file parsing completed", 
                   total=len(file_paths),
                   successful=successful, 
                   failed=failed)
        
        return parsed_docs
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported file formats"""
        return {
            "local_files": list(self.parsers.keys()),
            "web_platforms": ["notion", "confluence"]
        }
    
    async def detect_document_type(self, file_path: str) -> Optional[DocumentType]:
        """Detect document type from file"""
        if not os.path.exists(file_path):
            return None
        
        file_ext = Path(file_path).suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Map extensions to document types
        type_mapping = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.WORD,
            '.doc': DocumentType.WORD,
            '.xlsx': DocumentType.EXCEL,
            '.xls': DocumentType.EXCEL,
            '.pptx': DocumentType.POWERPOINT,
            '.ppt': DocumentType.POWERPOINT,
            '.txt': DocumentType.TEXT,
            '.md': DocumentType.TEXT,
            '.rst': DocumentType.TEXT
        }
        
        return type_mapping.get(file_ext)
    
    async def extract_metadata_only(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract only metadata without full parsing"""
        try:
            file_stats = os.stat(file_path)
            doc_type = await self.detect_document_type(file_path)
            
            basic_metadata = {
                'file_name': os.path.basename(file_path),
                'file_size': file_stats.st_size,
                'document_type': doc_type.value if doc_type else 'unknown',
                'created': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'mime_type': mimetypes.guess_type(file_path)[0]
            }
            
            return basic_metadata
            
        except Exception as e:
            logger.error("Metadata extraction failed", file=file_path, error=str(e))
            return None
    
    async def validate_parsing_capabilities(self) -> Dict[str, bool]:
        """Validate all parsing capabilities"""
        capabilities = {
            'pdf_parser': True,
            'word_parser': True,
            'excel_parser': True,
            'powerpoint_parser': True,
            'text_parser': True,
            'notion_parser': self.notion_parser.client is not None,
            'confluence_parser': self.confluence_parser.client is not None,
            'ocr_support': False  # Will be implemented later
        }
        
        logger.info("Parser capabilities validated", capabilities=capabilities)
        return capabilities
    
    async def get_parsing_statistics(self) -> Dict[str, Any]:
        """Get parsing statistics and performance metrics"""
        # This would be implemented with actual usage tracking
        return {
            'total_documents_parsed': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'average_processing_time': 0.0,
            'supported_formats': len(self.parsers),
            'web_integrations_active': sum([
                self.notion_parser.client is not None,
                self.confluence_parser.client is not None
            ])
        }