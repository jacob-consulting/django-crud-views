# Supported Field Types

The following Django fields are auto-detected and rendered with type-specific templates:

| Detected type | Django field |
|---------------|--------------|
| `char` | `CharField`, `SlugField`, `URLField`, `EmailField` |
| `text` | `TextField` |
| `boolean` | `BooleanField`, `NullBooleanField` |
| `datetime` | `DateTimeField` |
| `date` | `DateField` |
| `integer` | `IntegerField`, `SmallIntegerField`, `BigIntegerField`, `PositiveIntegerField`, `PositiveSmallIntegerField`, `PositiveBigIntegerField`, `AutoField`, `BigAutoField`, `SmallAutoField` |
| `float` | `FloatField`, `DecimalField` |
| `foreignkey` | `ForeignKey`, `OneToOneField`, `OneToOneRel` |
| `manytomany` | `ManyToManyField`, `ManyToManyRel`, `ManyToOneRel` |

Methods, properties, and unrecognised fields fall back to the `default` type.
