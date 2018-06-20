# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-12 09:50
from __future__ import unicode_literals

from bulk_update.helper import bulk_update
from django.db import migrations
from fluent.syntax import FluentParser, FluentSerializer


def migrate_ftl_translations_to_0_6_4(apps, schema):
    """
    Converts all FTL translations to the latest (0.5) syntax and serializes
    them with the latest (0.6.4) serializer to prevent creating duplicate
    translations on save. Also convert corresponding TranslationMemoryEntries.

    See bugs 1441020 and 1442201 for more details.
    """
    parser = FluentParser()
    serializer = FluentSerializer()

    # Translations
    Translation = apps.get_model('base', 'Translation')
    translations = Translation.objects.filter(entity__resource__format='ftl')
    translations_to_update = []

    for t in translations:
        current = t.string
        ast = parser.parse_entry(current)
        t.string = serializer.serialize_entry(ast)

        if t.string != current:
            translations_to_update.append(t)

    bulk_update(translations_to_update, update_fields=['string'])

    # Translation Memory Entries
    TranslationMemoryEntry = apps.get_model('base', 'TranslationMemoryEntry')
    updated_pks = [x.pk for x in translations_to_update]
    tms = TranslationMemoryEntry.objects.filter(translation__pk__in=updated_pks)
    tms_to_update = []

    for tm in tms:
        current = tm.target
        ast = parser.parse_entry(current)
        tm.target = serializer.serialize_entry(ast)

        if tm.target != current:
            tms_to_update.append(tm)

    bulk_update(tms_to_update, update_fields=['target'])


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0115_idx_translation_date_locale'),
    ]

    operations = [
        migrations.RunPython(
            migrate_ftl_translations_to_0_6_4,
            migrations.RunPython.noop
        )
    ]
