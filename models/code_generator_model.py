from tortoise import fields, models

class CodeSession(models.Model):
    id = fields.IntField(pk=True)

    requirement_session = fields.ForeignKeyField(
        "models.RequirementSession",
        related_name="code_sessions",
        on_delete=fields.CASCADE
    )

    generated_code = fields.JSONField()
    status = fields.CharField(max_length=50, default="PENDING")

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "code_sessions"