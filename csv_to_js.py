#!/usr/bin/env python3
import csv
import sys
import re

def load_csv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))

def format_js_array(name, data, fields, types):
    """
    Emit a JS array of objects called `name`, picking out each field
    according to its type (str, num, or arr), and using safe defaults
    for empty values.
    """
    print(f"const {name} = [")
    for i, row in enumerate(data):
        parts = []
        for field in fields:
            val = row.get(field, "")               # get the raw CSV cell
            t   = types.get(field, "str")          # lookup its declared type

            if t == "str":
                # always emit a JS string literal (even if empty)
                parts.append(f"{field}:'{val}'")

            elif t == "num":
                # trim whitespace, fall back to 0 if blank
                v = val.strip() if isinstance(val, str) else val
                parts.append(f"{field}:{v if v != '' else 0}")

            elif t == "arr":
                # only split if non-empty, else produce an empty array
                if isinstance(val, str) and val.strip():
                    items = [x.strip() for x in val.split(',')]
                else:
                    items = []
                arr = ",".join(f"'{x}'" for x in items)
                parts.append(f"{field}:[{arr}]")

        # join into a JS object literal
        line = "{" + ",".join(parts) + "}"
        end  = "," if i < len(data) - 1 else ""
        print(f"  {line}{end}")
    print("];\n")

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} specimens.csv mags.csv", file=sys.stderr)
        sys.exit(1)
    spec_csv, mag_csv = sys.argv[1], sys.argv[2]
    specs = load_csv(spec_csv)
    mags  = load_csv(mag_csv)

    # ─── rename specimen columns ───
    spec_rename = {
        "specimen_id":                  "specimenID",
        "Species":                      "Species",
        "Family":                       "Family",
        "Order":                        "Order",
        "Class":                        "Class",
        "Length (mm)":                  "Length",
        "Weight (g)":                   "Weight",
        "Country":                      "Country",
        "Biome":                        "Biome",
        "Sample types":                 "SampleType",
        "Total data (GB)":              "TotalData",
        "Host data (GB)":               "HostData",
        "Metagenomic data (GB)":        "MetagenomicData",
        "Release":                      "Release",
        "Latitude reduced":             "Latitude",
        "Longitude reduced":            "Longitude"
    }
    specs = [
        { spec_rename.get(orig, orig): val
          for orig, val in row.items() }
        for row in specs
    ]
    # ─────────────────────────────────

    spec_fields = [
        "specimenID", "Species", "Family", "Order", "Class",
        "Length", "Weight", "Country", "Biome", "SampleType",
        "TotalData", "HostData", "MetagenomicData", "Release", "Latitude", "Longitude"
    ]
    spec_types = {f: 'str' for f in spec_fields}
    spec_types.update({
        "Length":           'num',
        "Weight":           'num',
        "SampleType":       'arr',
        "TotalData":        'num',
        "HostData":         'num',
        "MetagenomicData":  'num',
        "Latitude":         'num',
        "Longitude":        'num'
    })

    mag_rename = {
        "\ufeffID":            "MAGID",
        "specimenID":          "specimenID",
        "species":             "Species",
        "genus":               "Genus",
        "family":              "Family",
        "order":               "Order",
        "class":               "Class",
        "phylum":              "Phylum",
        "completeness":        "Completeness",
        "contamination":       "Contamination",
        "MAG_url_public":      "Link",
        "Release":             "Release"
    }

    mags = [
        { mag_rename.get(orig, orig): val
          for orig, val in row.items() }
        for row in mags
    ]

    tax_cols = ["Species","Genus","Family","Order","Class","Phylum"]
    for row in mags:
        for col in tax_cols:
            v = row.get(col, "")
            if isinstance(v, str):
                # remove any single-letter prefix + '__' at start of the string
                row[col] = re.sub(r'^[dpkocfgs]__', '', v)

    mag_fields = [
        "MAGID","specimenID","Species","Genus","Family","Order","Class","Phylum","Completeness","Contamination","Link","Release"
    ]
    mag_types = {f:'str' for f in mag_fields}
    mag_types.update({
        "Completeness": 'num',
        "Contamination": 'num'
    })

    format_js_array("specimensData", specs, spec_fields, spec_types)
    format_js_array("magsData", mags, mag_fields, mag_types)

if __name__ == '__main__':
    main()
