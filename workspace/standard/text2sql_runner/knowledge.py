from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


KNOWLEDGE_MODES = ("Full", "None")


@dataclass(frozen=True)
class KnowledgeContext:
    mode: str
    files: tuple[str, ...]
    content: str


def load_knowledge_context(mode: str, root: Path) -> KnowledgeContext:
    if mode not in KNOWLEDGE_MODES:
        raise ValueError(f"不支持的知识库模式: {mode}")
    if mode == "None":
        return KnowledgeContext(mode="None", files=(), content="")
    if not root.is_dir():
        raise RuntimeError(f"知识库目录不存在: {root}")
    if root.is_symlink():
        raise RuntimeError(f"知识库根目录不能是符号链接: {root}")

    resolved_root = root.resolve(strict=True)
    validated_paths: list[tuple[str, Path]] = []
    for path in root.rglob("*.md"):
        if path.is_symlink():
            raise RuntimeError(f"知识文件不能是符号链接: {path}")
        resolved_path = path.resolve(strict=True)
        try:
            relative_path = resolved_path.relative_to(resolved_root).as_posix()
        except ValueError as exc:
            raise RuntimeError(
                f"知识文件位于知识库目录之外: {path}"
            ) from exc
        if not resolved_path.is_file():
            continue
        validated_paths.append((relative_path, resolved_path))

    validated_paths.sort(key=lambda item: (item[0].casefold(), item[0]))

    documents: list[tuple[str, str]] = []
    for relative_path, path in validated_paths:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        documents.append((relative_path, content))
    if not documents:
        raise RuntimeError(f"知识库目录没有非空 Markdown 文件: {root}")

    rendered = "\n\n".join(
        f"## 知识文件：{relative_path}\n\n{content}"
        for relative_path, content in documents
    )
    return KnowledgeContext(
        mode="Full",
        files=tuple(relative_path for relative_path, _ in documents),
        content=rendered,
    )


def combine_schema_and_knowledge(
    schema: str,
    context: KnowledgeContext,
) -> str:
    if not schema.strip():
        raise ValueError("数据库结构为空")
    if context.mode == "None":
        return schema
    return (
        schema
        + "\n\n完整业务知识库（数据库未声明外键时，以明确业务规则为准）：\n"
        + context.content
    )
