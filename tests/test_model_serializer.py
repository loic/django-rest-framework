"""
The `ModelSerializer` and `HyperlinkedModelSerializer` classes are essentially
shortcuts for automatically creating serializers based on a given model class.

These tests deal with ensuring that we correctly map the model fields onto
an appropriate set of serializer fields for each case.
"""
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase
from rest_framework import serializers


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


# Testing regular field mappings

class CustomField(models.Field):
    pass


class RegularFieldsModel(models.Model):
    auto_field = models.AutoField(primary_key=True)
    big_integer_field = models.BigIntegerField()
    boolean_field = models.BooleanField(default=False)
    char_field = models.CharField(max_length=100)
    comma_seperated_integer_field = models.CommaSeparatedIntegerField(max_length=100)
    date_field = models.DateField()
    datetime_field = models.DateTimeField()
    decimal_field = models.DecimalField(max_digits=3, decimal_places=1)
    email_field = models.EmailField(max_length=100)
    float_field = models.FloatField()
    integer_field = models.IntegerField()
    null_boolean_field = models.NullBooleanField()
    positive_integer_field = models.PositiveIntegerField()
    positive_small_integer_field = models.PositiveSmallIntegerField()
    slug_field = models.SlugField(max_length=100)
    small_integer_field = models.SmallIntegerField()
    text_field = models.TextField()
    time_field = models.TimeField()
    url_field = models.URLField(max_length=100)
    custom_field = CustomField()

    def method(self):
        return 'method'


class TestRegularFieldMappings(TestCase):
    def test_regular_fields(self):
        """
        Model fields should map to their equivelent serializer fields.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel

        expected = dedent("""
            TestSerializer():
                auto_field = IntegerField(read_only=True)
                big_integer_field = IntegerField()
                boolean_field = BooleanField(default=False)
                char_field = CharField(max_length=100)
                comma_seperated_integer_field = CharField(max_length=100, validators=[<django.core.validators.RegexValidator object>])
                date_field = DateField()
                datetime_field = DateTimeField()
                decimal_field = DecimalField(decimal_places=1, max_digits=3)
                email_field = EmailField(max_length=100)
                float_field = FloatField()
                integer_field = IntegerField()
                null_boolean_field = BooleanField(required=False)
                positive_integer_field = IntegerField()
                positive_small_integer_field = IntegerField()
                slug_field = SlugField(max_length=100)
                small_integer_field = IntegerField()
                text_field = CharField()
                time_field = TimeField()
                url_field = URLField(max_length=100)
                custom_field = ModelField(model_field=<tests.test_model_serializer.CustomField: custom_field>)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_method_field(self):
        """
        Properties and methods on the model should be allowed as `Meta.fields`
        values, and should map to `ReadOnlyField`.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field', 'method')

        expected = dedent("""
            TestSerializer():
                auto_field = IntegerField(read_only=True)
                method = ReadOnlyField()
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_fields(self):
        """
        Both `pk` and the actual primary key name are valid in `Meta.fields`.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('pk', 'auto_field')

        expected = dedent("""
            TestSerializer():
                pk = IntegerField(label='Auto field', read_only=True)
                auto_field = IntegerField(read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_extra_field_kwargs(self):
        """
        Ensure `extra_kwargs` are passed to generated fields.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('pk', 'char_field')
                extra_kwargs = {'char_field': {'default': 'extra'}}

        expected = dedent("""
            TestSerializer():
                pk = IntegerField(label='Auto field', read_only=True)
                char_field = CharField(default='extra', max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_invalid_field(self):
        """
        Field names that do not map to a model field or relationship should
        raise a configuration errror.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field', 'invalid')

        with self.assertRaises(ImproperlyConfigured) as excinfo:
            TestSerializer()
        expected = 'Field name `invalid` is not valid for model `ModelBase`.'
        assert str(excinfo.exception) == expected

    def test_missing_field(self):
        """
        Fields that have been declared on the serializer class must be included
        in the `Meta.fields` if it exists.
        """
        class TestSerializer(serializers.ModelSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field',)

        with self.assertRaises(ImproperlyConfigured) as excinfo:
            TestSerializer()
        expected = (
            'Field `missing` has been declared on serializer '
            '`TestSerializer`, but is missing from `Meta.fields`.'
        )
        assert str(excinfo.exception) == expected


# Testing relational field mappings

class ForeignKeyTargetModel(models.Model):
    name = models.CharField(max_length=100)


class ManyToManyTargetModel(models.Model):
    name = models.CharField(max_length=100)


class OneToOneTargetModel(models.Model):
    name = models.CharField(max_length=100)


class ThroughTargetModel(models.Model):
    name = models.CharField(max_length=100)


class Supplementary(models.Model):
    extra = models.IntegerField()
    forwards = models.ForeignKey('ThroughTargetModel')
    backwards = models.ForeignKey('RelationalModel')


class RelationalModel(models.Model):
    foreign_key = models.ForeignKey(ForeignKeyTargetModel, related_name='reverse_foreign_key')
    many_to_many = models.ManyToManyField(ManyToManyTargetModel, related_name='reverse_many_to_many')
    one_to_one = models.OneToOneField(OneToOneTargetModel, related_name='reverse_one_to_one')
    through = models.ManyToManyField(ThroughTargetModel, through=Supplementary, related_name='reverse_through')


class TestRelationalFieldMappings(TestCase):
    def test_pk_relations(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                foreign_key = PrimaryKeyRelatedField(queryset=ForeignKeyTargetModel.objects.all())
                one_to_one = PrimaryKeyRelatedField(queryset=OneToOneTargetModel.objects.all())
                many_to_many = PrimaryKeyRelatedField(many=True, queryset=ManyToManyTargetModel.objects.all())
                through = PrimaryKeyRelatedField(many=True, read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_nested_relations(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                foreign_key = NestedSerializer(read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
                one_to_one = NestedSerializer(read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
                many_to_many = NestedSerializer(many=True, read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
                through = NestedSerializer(many=True, read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_hyperlinked_relations(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
                foreign_key = HyperlinkedRelatedField(queryset=ForeignKeyTargetModel.objects.all(), view_name='foreignkeytargetmodel-detail')
                one_to_one = HyperlinkedRelatedField(queryset=OneToOneTargetModel.objects.all(), view_name='onetoonetargetmodel-detail')
                many_to_many = HyperlinkedRelatedField(many=True, queryset=ManyToManyTargetModel.objects.all(), view_name='manytomanytargetmodel-detail')
                through = HyperlinkedRelatedField(many=True, read_only=True, view_name='throughtargetmodel-detail')
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_nested_hyperlinked_relations(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
                foreign_key = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='foreignkeytargetmodel-detail')
                    name = CharField(max_length=100)
                one_to_one = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='onetoonetargetmodel-detail')
                    name = CharField(max_length=100)
                many_to_many = NestedSerializer(many=True, read_only=True):
                    url = HyperlinkedIdentityField(view_name='manytomanytargetmodel-detail')
                    name = CharField(max_length=100)
                through = NestedSerializer(many=True, read_only=True):
                    url = HyperlinkedIdentityField(view_name='throughtargetmodel-detail')
                    name = CharField(max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_reverse_foreign_key(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = ForeignKeyTargetModel
                fields = ('id', 'name', 'reverse_foreign_key')

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                name = CharField(max_length=100)
                reverse_foreign_key = PrimaryKeyRelatedField(many=True, queryset=RelationalModel.objects.all())
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_reverse_one_to_one(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = OneToOneTargetModel
                fields = ('id', 'name', 'reverse_one_to_one')

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                name = CharField(max_length=100)
                reverse_one_to_one = PrimaryKeyRelatedField(queryset=RelationalModel.objects.all())
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_reverse_many_to_many(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = ManyToManyTargetModel
                fields = ('id', 'name', 'reverse_many_to_many')

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                name = CharField(max_length=100)
                reverse_many_to_many = PrimaryKeyRelatedField(many=True, queryset=RelationalModel.objects.all())
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_reverse_through(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = ThroughTargetModel
                fields = ('id', 'name', 'reverse_through')

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                name = CharField(max_length=100)
                reverse_through = PrimaryKeyRelatedField(many=True, read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)


class TestIntegration(TestCase):
    def setUp(self):
        self.foreign_key_target = ForeignKeyTargetModel.objects.create(
            name='foreign_key'
        )
        self.one_to_one_target = OneToOneTargetModel.objects.create(
            name='one_to_one'
        )
        self.many_to_many_targets = [
            ManyToManyTargetModel.objects.create(
                name='many_to_many (%d)' % idx
            ) for idx in range(3)
        ]
        self.instance = RelationalModel.objects.create(
            foreign_key=self.foreign_key_target,
            one_to_one=self.one_to_one_target,
        )
        self.instance.many_to_many = self.many_to_many_targets
        self.instance.save()

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel

        self.serializer_cls = TestSerializer

    def test_pk_retrival(self):
        serializer = self.serializer_cls(self.instance)
        expected = {
            'id': self.instance.pk,
            'foreign_key': self.foreign_key_target.pk,
            'one_to_one': self.one_to_one_target.pk,
            'many_to_many': [item.pk for item in self.many_to_many_targets],
            'through': []
        }
        self.assertEqual(serializer.data, expected)

    def test_pk_create(self):
        new_foreign_key = ForeignKeyTargetModel.objects.create(
            name='foreign_key'
        )
        new_one_to_one = OneToOneTargetModel.objects.create(
            name='one_to_one'
        )
        new_many_to_many = [
            ManyToManyTargetModel.objects.create(
                name='new many_to_many (%d)' % idx
            ) for idx in range(3)
        ]
        data = {
            'foreign_key': new_foreign_key.pk,
            'one_to_one': new_one_to_one.pk,
            'many_to_many': [item.pk for item in new_many_to_many],
        }

        # Serializer should validate okay.
        serializer = self.serializer_cls(data=data)
        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.foreign_key.pk == new_foreign_key.pk
        assert instance.one_to_one.pk == new_one_to_one.pk
        assert [
            item.pk for item in instance.many_to_many.all()
        ] == [
            item.pk for item in new_many_to_many
        ]
        assert list(instance.through.all()) == []

        # Representation should be correct.
        expected = {
            'id': instance.pk,
            'foreign_key': new_foreign_key.pk,
            'one_to_one': new_one_to_one.pk,
            'many_to_many': [item.pk for item in new_many_to_many],
            'through': []
        }
        self.assertEqual(serializer.data, expected)

    def test_pk_update(self):
        new_foreign_key = ForeignKeyTargetModel.objects.create(
            name='foreign_key'
        )
        new_one_to_one = OneToOneTargetModel.objects.create(
            name='one_to_one'
        )
        new_many_to_many = [
            ManyToManyTargetModel.objects.create(
                name='new many_to_many (%d)' % idx
            ) for idx in range(3)
        ]
        data = {
            'foreign_key': new_foreign_key.pk,
            'one_to_one': new_one_to_one.pk,
            'many_to_many': [item.pk for item in new_many_to_many],
        }

        # Serializer should validate okay.
        serializer = self.serializer_cls(self.instance, data=data)
        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.foreign_key.pk == new_foreign_key.pk
        assert instance.one_to_one.pk == new_one_to_one.pk
        assert [
            item.pk for item in instance.many_to_many.all()
        ] == [
            item.pk for item in new_many_to_many
        ]
        assert list(instance.through.all()) == []

        # Representation should be correct.
        expected = {
            'id': self.instance.pk,
            'foreign_key': new_foreign_key.pk,
            'one_to_one': new_one_to_one.pk,
            'many_to_many': [item.pk for item in new_many_to_many],
            'through': []
        }
        self.assertEqual(serializer.data, expected)
