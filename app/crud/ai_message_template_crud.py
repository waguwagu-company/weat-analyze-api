from typing import List, Optional
from sqlalchemy import text
from app.db.db import SessionFactory
from app.models.ai_message_template_model import AIMessageTemplate

def get_ai_message_templates_by_basis_type(
    basis_type: str,
) -> List[AIMessageTemplate]:
    with SessionFactory() as session:
        result = session.execute(
            text("""
                SELECT
                    ai_message_template_id,
                    ai_message_template_title,
                    ai_message_template_content,
                    ai_analysis_basis_type
                FROM public.ai_message_template
                WHERE ai_analysis_basis_type = :basis_type
                ORDER BY ai_message_template_id ASC
            """),
            {
                "basis_type": basis_type,
            }
        )
        rows = result.mappings().all()

    models: List[AIMessageTemplate] = []
    for row in rows:
        basis_list: Optional[List[str]] = [row["ai_analysis_basis_type"]] if row["ai_analysis_basis_type"] else []
        model = AIMessageTemplate(
            ai_message_template_id=row["ai_message_template_id"],
            ai_message_template_title=row["ai_message_template_title"],
            ai_message_template_content=row["ai_message_template_content"],
            ai_analysis_basis_type=basis_list,
        )
        models.append(model)

    return models