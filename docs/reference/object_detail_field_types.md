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

Scalar model choices render as readable text, including integer and boolean labels, before
ordinary type formatting. Explicit `type` does not opt out; use `choices_display=False`.
Single-object FK/O2O traversal supports terminal scalar choices; collections retain their
existing rendering. See [choice support and display metadata](object_detail_configuration.md#choice-labels-and-raw-values).

Stock `char`, `text` and `default` leaves show the muted em dash for exact `None` or `""`
in `display_value`. Zero, False and whitespace remain values. Nonempty `text` keeps the
configured `linebreaks`/`linebreaksbr` formatting. Empty rows, titles and explicit detail
remain visible; custom templates own their output. See the [copied text leaf](object_detail_configuration.md#copied-text-value-template).
