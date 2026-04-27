from tortoise import fields, models


class DocumentationSession(models.Model):
    id = fields.IntField(pk=True)

    code_session = fields.ForeignKeyField(
        "models.CodeSession",
        related_name="documentation_sessions",
        on_delete=fields.CASCADE
    )

    overview = fields.TextField()
    architecture = fields.JSONField()
    file_responsibilities = fields.JSONField()
    

    status = fields.CharField(max_length=50, default="COMPLETED")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "documentation_sessions"