# Document router package
from .document_router import router as document_router
from .search_router import router as search_router
from .chat_router import router as chat_router
from .research_router import router as research_router

__all__ = ['document_router', 'search_router', 'chat_router', 'research_router'] 