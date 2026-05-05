from tortoise import fields, models

class Documentation(models.Model):
    id = fields.IntField(pk=True)

    user = fields.ForeignKeyField("models.Users", related_name="documentations", on_delete=fields.CASCADE)

    session = fields.ForeignKeyField("models.ValidationSession",related_name="documentations",on_delete=fields.CASCADE)

    code = fields.ForeignKeyField("models.GeneratedCode", related_name="documentations", on_delete=fields.CASCADE)

    tests = fields.ForeignKeyField("models.UnitTests", related_name="documentations", on_delete=fields.CASCADE)

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

    class Meta:
        table = "documentation"