import fitz

from app.database import AsyncSessionLocal
from app.models import Document, DocumentContent


async def process_document(document_id: int, file_path: str):

    async with AsyncSessionLocal() as db:

        try:

            document = await db.get(Document, document_id)

            pdf = fitz.open(file_path)

            content = ""

            for page in pdf:
                content += page.get_text()

            pdf.close()

            document_content = DocumentContent(
                content=content,
                document_id=document.id
            )

            db.add(document_content)

            document.status = "READY"

            await db.commit()

        except Exception:

            document = await db.get(Document, document_id)

            if document:
                document.status = "FAILED"
                await db.commit()