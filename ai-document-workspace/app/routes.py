import os,fitz
from fastapi import APIRouter,Depends,HTTPException,File,UploadFile,Form,BackgroundTasks,WebSocket,WebSocketDisconnect

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,text

from app.database import get_db
from app.models import Workspace,Document,DocumentContent
from app.schemas import *
from app.background import process_document
from app.llm import ask_llm

router = APIRouter()

SEARCH_QUERY = text("""
    SELECT
        d.id,
        d.filename,

        ts_headline(
            'english',
            dc.content,
            plainto_tsquery('english', :query),
            'StartSel=<mark>, StopSel=</mark>, MaxWords=40, MinWords=15'
        ) AS snippet,

        dc.content,

        ts_rank(
            to_tsvector('english', dc.content),
            plainto_tsquery('english', :query)
        ) AS rank

    FROM document_contents dc

    JOIN documents d
        ON dc.document_id = d.id

    WHERE
        to_tsvector('english', dc.content)
        @@
        plainto_tsquery('english', :query)

    ORDER BY rank DESC

    LIMIT 5
""")

#Workspace

#Create Workspace
@router.post("/workspaces",response_model=WorkspaceResponse)
async def create_workspace(workspace:WorkspaceCreate,db:AsyncSession=Depends(get_db)):
    new_workspace = Workspace(**workspace.model_dump())
    db.add(new_workspace)
    await db.commit()
    await db.refresh(new_workspace)
    return new_workspace

# Show all workSpace
@router.get("/workspaces",response_model=list[WorkspaceResponse])
async def show_workspace(db:AsyncSession=Depends(get_db)):
    result = await db.execute(select(Workspace))
    workspace = result.scalars().all()
    return workspace

# Get one workspace
@router.get("/workspaces/{ws_id}",response_model=WorkspaceResponse)
async def show_workspace_one(ws_id:int,db:AsyncSession=Depends(get_db)):
    result = await db.get(Workspace,ws_id)

    if result is None:
        raise HTTPException(status_code=404,detail="WorkSpace not found")

    return result

#Update workspace
@router.put("/workspaces/{ws_id}",response_model=WorkspaceResponse)
async def update_workspace(ws_id:int,workspace:WorkspaceCreate,db:AsyncSession=Depends(get_db)):
    existing_workspace = await db.get(Workspace,ws_id)
    if existing_workspace is None:
        raise HTTPException(status_code=404,detail="Workspace not found")

    existing_workspace.name=workspace.name
    await db.commit()
    await db.refresh(existing_workspace)
    return existing_workspace

#Delete Workspace
@router.delete("/workspaces/{ws_id}",response_model=WorkspaceResponse)
async def delete_workspace(ws_id:int,db:AsyncSession=Depends(get_db)):
    workspace = await db.get(Workspace,ws_id)
    if workspace is None:
        raise HTTPException(status_code=404,detail="Workspace not found")
    
    deleted_workspace = WorkspaceResponse.model_validate(workspace)

    await db.delete(workspace)
    await db.commit()

    return deleted_workspace


#Document

#Upload Document form
@router.post("/documents/upload",response_model=DocumentResponse)
async def upload_document(background_tasks: BackgroundTasks,workspace_id: int = Form(...),
                          file: UploadFile = File(...),db: AsyncSession = Depends(get_db)):

    workspace = await db.get(Workspace, workspace_id)

    if workspace is None:
        raise HTTPException(status_code=404,detail="Workspace not found")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400,detail="Only PDF files are allowed.")

    os.makedirs("uploads/documents",exist_ok=True)

    file_path = f"uploads/documents/{file.filename}"

    with open(file_path, "wb") as pdf:

        while chunk := await file.read(1024 * 1024):
            pdf.write(chunk)

    new_document = Document(
        filename=file.filename,
        filepath=file_path,
        status="PROCESSING",
        workspace_id=workspace_id
    )

    db.add(new_document)

    await db.commit()

    await db.refresh(new_document)

    background_tasks.add_task(process_document,new_document.id,file_path)

    return new_document


#Get all documents
@router.get("/documents",response_model=list[DocumentResponse])
async def show_all(db:AsyncSession=Depends(get_db)):
    result = await db.execute(select(Document))
    documents = result.scalars().all()
    return documents

#Get one documents
@router.get("/documents/{document_id}",response_model=DocumentResponse)
async def show_one(document_id:int,db:AsyncSession=Depends(get_db)):
    result = await db.get(Document,document_id)

    if result is None:
        raise HTTPException(status_code=404,detail="Document not found")
    return result


#Get document content
@router.get("/documents/{document_id}/content",response_model=DocumentContentResponse)
async def get_document_content(
    document_id: int,db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(DocumentContent).where(DocumentContent.document_id == document_id))

    content = result.scalar_one_or_none()

    if content is None:
        raise HTTPException(status_code=404,detail="Document content not found")
        
    return content


#delte document
@router.delete("/documents/{document_id}")
async def delete_document(document_id: int,db: AsyncSession = Depends(get_db)):

    document = await db.get(Document,document_id)

    if document is None:
        raise HTTPException(status_code=404,detail="Document not found")
    
    if os.path.exists(document.filepath):
        os.remove(document.filepath)

    await db.delete(document)
    await db.commit()

    return {"message": "Document deleted successfully"  }     




#Function that will return all the response from the search 
@router.post("/search",response_model=SearchResponse)
async def search_documents(request: SearchRequest,db: AsyncSession = Depends(get_db)):

    result = await db.execute(SEARCH_QUERY,
        {
            "query": request.query
        }
    )

    rows = result.fetchall()

    if not rows:
        raise HTTPException(status_code=404,detail="No matching documents found.")

    documents = []
    for row in rows:
        documents.append(SearchResult(filename=row.filename,snippet=row.snippet))

    return SearchResponse(documents=documents)



#LLM Integraton
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest,db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        SEARCH_QUERY,
        {
            "query": request.question
        }
    )

    rows = result.fetchall()

    if not rows:
        raise HTTPException(status_code=404,detail="No relevant documents found.")

    context = ""

    for row in rows:
        context += f"Document: {row.filename}\n"
        context += row.content
        context += "\n\n"

    answer = await ask_llm(context=context,question=request.question)

    return ChatResponse(answer=answer)


#LLM With websocket 
@router.websocket("/ws/chat")
async def websocket_chat(websocket:WebSocket,db:AsyncSession=Depends(get_db)):
    await websocket.accept()

    GREETINGS = {
        "hi": "Hello! 👋 Ask me anything about your uploaded documents.",
        "hello": "Hello! 👋 Ask me anything about your uploaded documents.",
        "hey": "Hi! 👋 How can I help you with your documents?",
        "good morning": "Good morning! ☀️ What would you like to know?",
        "good evening": "Good evening! 🌙 How can I assist you?",
        "who are you":"I am Akki handles reponse based upon the uploded document",
        "who invented you":"I am invented by Akshat Trivedi "
    }



    try:
        while True:
            question=await websocket.receive_text()

            question = question.strip().lower()

            if question in GREETINGS:
                await websocket.send_text(GREETINGS[question])
                continue

            result = await db.execute(
                SEARCH_QUERY,{
                    "query":question
                }
            )

            rows = result.fetchall()

            if not rows:
                await websocket.send_text("No relevent docs")

                continue
            
            context = ""

            for row in rows:
                context+=f"Document:{row.filename}\n"
                context+= row.content
                context+="\n\n"

            answer= await ask_llm(
                context=context,
                question=question
            )

            await websocket.send_text(answer)

    except WebSocketDisconnect:

        print("Discoennected")
