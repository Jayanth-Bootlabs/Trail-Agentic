from tortoise import fields, models

class Insights(models.Model):
    id = fields.IntField(pk=True)

    user = fields.ForeignKeyField("models.Users", related_name="insights", on_delete=fields.CASCADE)

    session = fields.ForeignKeyField("models.ValidationSession",related_name="insights",on_delete=fields.CASCADE)

    code = fields.ForeignKeyField("models.GeneratedCode",related_name="insights",on_delete=fields.CASCADE)

    tests = fields.ForeignKeyField("models.UnitTests",related_name="insights",on_delete=fields.CASCADE)

    insights_summary = fields.TextField()
    key_insights = fields.JSONField(default=list)
    missing_implementations = fields.JSONField(default=list)
    code_quality_issues = fields.JSONField(default=list)
    security_issues = fields.JSONField(default=list)
    scalability_problems = fields.JSONField(default=list)
    refactoring_suggestions = fields.JSONField(default=list)
    dependencies = fields.JSONField(default=list)
    recommendations = fields.JSONField(default=list)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "insights"