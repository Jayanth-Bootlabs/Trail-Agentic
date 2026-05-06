from tortoise import fields, models

class Insights(models.Model):
    id = fields.IntField(pk=True)

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
    is_completed = fields.BooleanField(default=False)

    class Meta:
        table = "insights"