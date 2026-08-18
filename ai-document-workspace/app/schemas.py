from pydantic import BaseModel, ConfigDict


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    status:str
    workspace_id: int

    model_config = ConfigDict(from_attributes=True)


class DocumentContentResponse(BaseModel):

    id: int
    content: str
    document_id: int
    model_config = ConfigDict(
        from_attributes=True
    )
    



#LLM
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


#Search
class SearchRequest(BaseModel):
    query: str


class SearchResult(BaseModel):
    filename: str
    snippet: str


class SearchResponse(BaseModel):
    documents: list[SearchResult]