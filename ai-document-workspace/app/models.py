from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Text


class Base(DeclarativeBase):
    pass


class Workspace(Base):

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)

    # One Workspace -> Many Documents
    documents: Mapped[list["Document"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan"
    )


class Document(Base):

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String)
    filepath: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id")
    )

    # Many Documents -> One Workspace
    workspace: Mapped["Workspace"] = relationship(
        back_populates="documents"
    )

    # One Document -> One DocumentContent
    document_content: Mapped["DocumentContent"] = relationship(
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan"
    )


class DocumentContent(Base):

    __tablename__ = "document_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        unique=True
    )

    # One DocumentContent -> One Document
    document: Mapped["Document"] = relationship(
        back_populates="document_content"
    )
        