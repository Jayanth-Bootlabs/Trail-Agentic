from tortoise import fields, models


class InsightsSession(models.Model):
    id = fields.IntField(pk=True)

    code_session = fields.ForeignKeyField(
        "models.CodeSession",
        related_name="insights_sessions",
        on_delete=fields.CASCADE
    )

    missing_implementations = fields.JSONField()
    code_quality_issues = fields.JSONField()
    security_issues = fields.JSONField()
    scalability_problems = fields.JSONField()
    refactoring_suggestions = fields.JSONField()

    status = fields.CharField(max_length=50, default="COMPLETED")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "insights_sessions"