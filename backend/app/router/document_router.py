import os
import time
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from service import DocumentService, ServiceConfig
from service.docmind_service import process_document_with_docmind
from schemas.document import (
    DeleteDocumentsRequest,
    RetrieveDocumentsRequest,
    UploadDocumentResponse,
    DocumentListResponse,
    DeleteDocumentsResponse
)

# Create router instance
router = APIRouter(prefix="/documents", tags=["documents"])

# Get service configuration
def get_document_service():
    config = ServiceConfig.get_api_config()
    return DocumentService(
        base_url=config['base_url'],
        api_key=config['api_key']
    ), config['default_dataset_id']

# 支持的文件类型
SUPPORTED_FILE_TYPES = {
    '.pdf', '.docx', '.xlsx', '.xls', '.txt'
}

@router.post("/upload", status_code=HTTP_200_OK, response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    index_name: str = Query(default="policy_documents", description="Index name for storing the document"),
):
    """
    Upload a document and process it using local parsing and ES storage.
    Supports multiple file formats: PDF, DOCX, XLSX, TXT etc.
    
    Args:
        file: Document file to upload
        index_name: Index name for storing the document (default: policy_documents)
    
    Returns:
        JSON response with upload status and document details
    """
    try:
        # 验证文件类型
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in SUPPORTED_FILE_TYPES:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(sorted(SUPPORTED_FILE_TYPES))}"
            )
        
        # 生成唯一的文档ID
        document_id = str(uuid.uuid4())
        
        # 保存上传的文件到临时位置
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # 使用 DocMind 处理文档并存储到 Milvus
        processing_result = process_document_with_docmind(
            file_path=temp_file_path,
            file_name=file.filename,
            index_name=index_name,
            chunk_size=500
        )

        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # 检查处理结果
        if not processing_result["success"]:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Document processing failed: {processing_result['message']}"
            )

        return {
            "status": "success",
            "message": processing_result["message"],
            "document_count": processing_result["document_count"]
        }
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 清理临时文件
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/list", status_code=HTTP_200_OK, response_model=DocumentListResponse)
async def get_document_list(
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Number of items per page"),
    keywords: Optional[str] = Query(None, description="Keywords to filter document titles"),
    document_id: Optional[str] = Query(None, description="Filter by specific document ID"),
    service_info: tuple = Depends(get_document_service)
):
    """
    Get a list of documents with filtering options.
    
    Args:
        page: Page number for pagination
        page_size: Number of items per page
        keywords: Optional keywords to filter document titles
        document_id: Optional document ID to filter specific document
        
    Returns:
        JSON response with list of documents and their details
    """
    doc_service, dataset_id = service_info
    
    try:
        # Get documents from service
        response = doc_service.get_documents(
            dataset_id=dataset_id,
            page=page,
            page_size=page_size,
            keywords=keywords,
            document_id=document_id
        )
        
        # 检查响应中的错误码
        if response.get("code") != 0:
            # 如果是因为没有文档导致的特定错误，返回空列表而不是错误
            if 'document None' in response.get("message", ""):
                return {
                    "code": 0,
                    "data": {
                        "docs": [],
                        "total": 0
                    }
                }
            # 其他错误正常抛出异常
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve documents: {response}"
            )
        
        # Return the response directly to match the expected format
        return response
        
    except Exception as e:
        # 如果是因为没有文档导致的异常，返回空列表
        error_msg = str(e)
        if "document None" in error_msg or "You don't own the document None" in error_msg:
            return {
                "code": 0,
                "data": {
                    "docs": [],
                    "total": 0
                }
            }
        
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )

@router.post("/delete", status_code=HTTP_200_OK, response_model=DeleteDocumentsResponse)
async def delete_documents(
    request: DeleteDocumentsRequest,
    service_info: tuple = Depends(get_document_service)
):
    """
    Delete documents from a dataset.
    
    Args:
        request: Body containing document_ids list
        
    Returns:
        JSON response with deletion status
    """
    doc_service, dataset_id = service_info
    
    try:
        # Call service to delete documents
        response = doc_service.delete_documents(
            dataset_id=dataset_id,
            document_ids=request.document_ids
        )
        
        # Check for errors in response
        if response.get("code") != 0:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete documents: {response}"
            )
        
        # Return successful response
        return {
            "code": 0,
            "message": "Documents deleted successfully",
            "data": response.get("data", {})
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting documents: {str(e)}"
        )

@router.post("/retrieve", status_code=HTTP_200_OK)
async def retrieve_documents(
    request: RetrieveDocumentsRequest,
    service_info: tuple = Depends(get_document_service)
):
    """
    Retrieve documents based on a question.
    
    Args:
        request: Body containing the question and optional document_ids
        
    Returns:
        JSON response with retrieved documents
    """
    doc_service, dataset_id = service_info
    
    try:
        # Call service to retrieve documents
        response = doc_service.retrieve_documents(
            question=request.question,
            dataset_ids=[dataset_id],
            document_ids=request.document_ids
        )
        
        # Check for errors in response
        if response.get("code") != 0:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve documents: {response}"
            )
        
        # Return the response directly
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        ) 