import re


def clean_text(value):
    """Clean text for use in citation formats."""

    if not value:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def build_citation_metadata(
    archive,
    inventory,
    metadata
):
    """
    Build normalized citation metadata.

    Nationaal Archief citation instruction:

    Full:
    Nationaal Archief, Den Haag, Ministerie van Koloniën:
    Memories van Overgave, nummer toegang 2.10.39,
    inventarisnummer ...

    Short:
    NL-HaNA, Koloniën / Memories van Overgave, 2.10.39,
    inv.nr. ...
    """

    title = clean_text(
        metadata.get("title")
    )

    date = clean_text(
        metadata.get("date")
    )

    physical_description = clean_text(
        metadata.get("physicalDescription")
    )

    handle = clean_text(
        metadata.get("handle")
    )

    # -------------------------------------------------
    # Archive-level information
    # -------------------------------------------------

    # For now this is specific to the collection we are
    # currently supporting. We can make this dynamic later.
    archive_name = (
        "Ministerie van Koloniën: "
        "Memories van Overgave"
    )

    repository = "Nationaal Archief"
    repository_location = "Den Haag"

    # -------------------------------------------------
    # Citations
    # -------------------------------------------------

    full_citation = (
        f"{repository}, {repository_location}, "
        f"{archive_name}, "
        f"nummer toegang {archive}, "
        f"inventarisnummer {inventory}"
    )

    short_citation = (
        f"NL-HaNA, Koloniën / Memories van Overgave, "
        f"{archive}, inv.nr. {inventory}"
    )

    return {
        "title": title,
        "date": date,
        "physicalDescription": physical_description,
        "handle": handle,
        "archive": clean_text(archive),
        "inventory": clean_text(inventory),
        "repository": repository,
        "repositoryLocation": repository_location,
        "archiveName": archive_name,
        "fullCitation": full_citation,
        "shortCitation": short_citation
    }


def escape_ris(value):
    """Clean text for RIS output."""

    if not value:
        return ""

    return clean_text(value)


def escape_bibtex(value):
    """Escape characters that have special meaning in BibTeX."""

    if not value:
        return ""

    value = clean_text(value)

    value = value.replace("\\", "\\\\")
    value = value.replace("{", "\\{")
    value = value.replace("}", "\\}")

    return value


def generate_ris(citation):
    """
    Generate an RIS citation for an archival item.

    RIS tags used:

    TY = type
    TI = title
    PY = year
    PB = publisher/repository
    CY = place
    UR = URL
    N1 = note
    ER = end record
    """

    lines = [
        "TY  - GEN",
        f"TI  - {escape_ris(citation['title'])}",
    ]

    if citation["date"]:
        lines.append(
            f"PY  - {escape_ris(citation['date'])}"
        )

    if citation["repository"]:
        lines.append(
            f"PB  - {escape_ris(citation['repository'])}"
        )

    if citation["repositoryLocation"]:
        lines.append(
            f"CY  - {escape_ris(citation['repositoryLocation'])}"
        )

    if citation["handle"]:
        lines.append(
            f"UR  - {escape_ris(citation['handle'])}"
        )

    # Archive/collection information.
    archive_note = (
        f"{citation['archiveName']}, "
        f"nummer toegang {citation['archive']}, "
        f"inventarisnummer {citation['inventory']}"
    )

    lines.append(
        f"N1  - {escape_ris(archive_note)}"
    )

    if citation["physicalDescription"]:
        lines.append(
            f"N1  - {escape_ris(citation['physicalDescription'])}"
        )

    lines.append(
        f"N1  - {escape_ris(citation['shortCitation'])}"
    )

    lines.append("ER  -")

    return "\n".join(lines) + "\n"


def generate_bibtex(citation):
    """
    Generate a BibTeX citation for an archival item.
    """

    archive = escape_bibtex(
        citation["archive"]
    )

    inventory = escape_bibtex(
        citation["inventory"]
    )

    title = escape_bibtex(
        citation["title"]
    )

    date = escape_bibtex(
        citation["date"]
    )

    repository = escape_bibtex(
        citation["repository"]
    )

    repository_location = escape_bibtex(
        citation["repositoryLocation"]
    )

    archive_name = escape_bibtex(
        citation["archiveName"]
    )

    handle = escape_bibtex(
        citation["handle"]
    )

    physical_description = escape_bibtex(
        citation["physicalDescription"]
    )

    full_citation = escape_bibtex(
        citation["fullCitation"]
    )

    short_citation = escape_bibtex(
        citation["shortCitation"]
    )

    citation_key = (
        f"NLHaNA_{archive}_{inventory}"
    )

    lines = [
        f"@misc{{{citation_key},",
        f"  title = {{{title}}},",
        f"  year = {{{date}}},",
        f"  institution = {{{repository}}},",
        f"  address = {{{repository_location}}},",
        f"  collection = {{{archive_name}}},",
        f"  number = {{{archive}, inventarisnummer {inventory}}},",
        f"  url = {{{handle}}},",
        f"  fullcitation = {{{full_citation}}},",
        f"  shortcitation = {{{short_citation}}},",
    ]

    if physical_description:
        lines.append(
            f"  note = {{{physical_description}}}"
        )

    lines.append("}")

    return "\n".join(lines) + "\n"