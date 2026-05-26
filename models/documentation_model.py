from tortoise import fields, models

class Documentation(models.Model):
    id = fields.IntField(pk=True)

    insights = fields.ForeignKeyField("models.Insights",related_name="documentations",on_delete=fields.CASCADE)

    overview = fields.TextField()
    architecture = fields.TextField()
    file_responsibilities = fields.JSONField()
    functional_requirements = fields.JSONField()
    non_functional_requirements = fields.JSONField()
    tech_stack_used = fields.JSONField()
    assumptions = fields.JSONField()
    test_summary = fields.TextField()
    next_steps = fields.JSONField()

    created_at = fields.DatetimeField(auto_now_add=True)
    is_completed = fields.BooleanField(default=False)

    class Meta:
        table = "documentation"
        indexes = [
        ("insights_id", "is_completed", "created_at"),
    ]