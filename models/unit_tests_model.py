from tortoise import fields, models

class UnitTests(models.Model):
    id = fields.IntField(pk=True)

    code = fields.ForeignKeyField("models.GeneratedCode",related_name="unit_tests",on_delete=fields.CASCADE)

    test_code = fields.TextField()
    test_summary = fields.TextField(null=True)
    frameworks_used = fields.JSONField(default=list)

    created_at = fields.DatetimeField(auto_now_add=True)
    is_completed = fields.BooleanField(default=False)

    class Meta:
        table = "unit_tests"