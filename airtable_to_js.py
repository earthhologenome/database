#!/usr/bin/env python3
import os
import sys
import re
import argparse
from pyairtable import Api

"""
Fetch specimens and mags data from two Airtable bases using the airtable-python-wrapper
and output as JavaScript arrays.
Usage:
    export AIRTABLE_API_KEY="key..."
    python3 airtable_to_js.py \
    --spec-base SPEC_BASE_ID --spec-table SPEC_TABLE_NAME \
    --mag-base MAG_BASE_ID   --mag-table MAG_TABLE_NAME \
    [--output output.js]
Requires environment variable AIRTABLE_API_KEY.
"""


def fetch_airtable_table(base_id, api_key, table_name, filter_formula=None):
    """
    Fetch all records from the given Airtable table via pyairtable.
    Optionally apply an Airtable formula filter.
    Returns a list of field dictionaries.
    """
    api = Api(api_key)
    table = api.table(base_id, table_name)
    if filter_formula:
        # Use 'formula' parameter for filtering
        records = table.all(formula=filter_formula)
    else:
        records = table.all()
    return [rec.get('fields', {}) for rec in records]

def format_js_array(name, data, fields, types, out=sys.stdout):
    print(f"const {name} = [", file=out)
    for i, row in enumerate(data):
        parts = []
        for field in fields:
            val = row.get(field, "")
            t = types.get(field, "str")
            if t == "str":
                # flatten list to comma-separated string if needed
                if isinstance(val, list):
                    candidate = ", ".join(val)
                else:
                    candidate = val
                parts.append(f"{field}:'{candidate}'")
            elif t == "num":
                # support numeric lists (take first), strings, and raw numbers
                if isinstance(val, list) and val:
                    candidate = val[0]
                else:
                    candidate = val
                if isinstance(candidate, str):
                    candidate = candidate.strip()
                try:
                    vnum = float(candidate)
                except Exception:
                    vnum = 0
                parts.append(f"{field}:{vnum}")
            elif t == "arr":
                # convert list or comma-separated string to JS array
                if isinstance(val, list):
                    items = val
                elif isinstance(val, str) and val.strip():
                    items = [x.strip() for x in val.split(',')]
                else:
                    items = []
                arr = ",".join(f"'{x}'" for x in items)
                parts.append(f"{field}:[{arr}]")
        line = "{" + ",".join(parts) + "}"
        end = "," if i < len(data) - 1 else ""
        print(f"  {line}{end}", file=out)
    print("];", file=out)
    print(file=out)

def parse_args():
    p = argparse.ArgumentParser(
        description="Fetch Airtable tables and output as JS arrays"
    )
    p.add_argument("--spec-base",   required=True, help="Airtable base ID for specimens")
    p.add_argument("--spec-table",  required=True, help="Specimens table name")
    p.add_argument("--mag-base",    required=True, help="Airtable base ID for mags")
    p.add_argument("--mag-table",   required=True, help="Mags table name")
    p.add_argument("--output",      "-o", help="Output .js file path (defaults to stdout)")
    return p.parse_args()


def main():
    args = parse_args()
    api_key = os.getenv('AIRTABLE_API_KEY')
    if not api_key:
        print("Error: Please set AIRTABLE_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)

    # determine output target
    out = open(args.output, 'w') if args.output else sys.stdout

    # Fetch specimens
    print(f"Fetching specimens data from base '{args.spec_base}', table '{args.spec_table}'...", file=sys.stderr)
    specs = fetch_airtable_table(args.spec_base, api_key, args.spec_table)
    print(f"Fetched {len(specs)} specimen records", file=sys.stderr)

    # Fetch mags filtered by assembly_type = 'Individual'
    mag_formula = "{assembly_type} = 'Individual'"
    print(f"Fetching mags data with filter ('{mag_formula}') from base '{args.mag_base}', table '{args.mag_table}'...", file=sys.stderr)
    mags = fetch_airtable_table(args.mag_base, api_key, args.mag_table, filter_formula=mag_formula)
    print(f"Fetched {len(mags)} mag records with assembly_type='Individual'", file=sys.stderr)

    # ─── rename specimen fields ───
    spec_rename = {
        "specimen_id":                  "specimenID",
        "Species":                      "Species",
        "Family":                       "Family",
        "Order":                        "Order",
        "Class":                        "Class",
        "Length (mm)":                  "Length",
        "Weight (g)":                   "Weight",
        "Country_flat":                 "Country",
        "Biome":                        "Biome",
        "SampleTypes_flat":             "SampleType",
        "Total data (GB)":              "TotalData",
        "Host data (GB)":               "HostData",
        "Metagenomic data (GB)":        "MetagenomicData",
        "Release":                      "Release",
        "ena_run_accession_flat":       "Accessions",
        "Latitude reduced":             "Latitude",
        "Longitude reduced":            "Longitude"
    }
    specs = [
        { spec_rename.get(orig, orig): val
          for orig, val in row.items() }
        for row in specs
    ]

    spec_fields = [
        "specimenID", "Species", "Family", "Order", "Class",
        "Length", "Weight", "Country", "Biome", "SampleType",
        "TotalData", "HostData", "MetagenomicData", "Release", "Accessions", "Latitude", "Longitude"
    ]
    spec_types = {f: 'str' for f in spec_fields}
    spec_types.update({
        "Length":           'num',
        "Weight":           'num',
        "SampleType":       'arr',
        "TotalData":        'num',
        "HostData":         'num',
        "MetagenomicData":  'num',
        "Accessions":       'arr',
        "Latitude":         'num',
        "Longitude":        'num'
    })

    # ─── rename mag fields ───
    mag_rename = {
        "ID":            "MAGID",
        "specimenID":    "specimenID",
        "species":       "Species",
        "genus":         "Genus",
        "family":        "Family",
        "order":         "Order",
        "class":         "Class",
        "phylum":        "Phylum",
        "completeness":  "Completeness",
        "contamination": "Contamination",
        "MAG_url_public":"Link",
        "Release":       "Release"
    }
    mags = [
        { mag_rename.get(orig, orig): val
          for orig, val in row.items() }
        for row in mags
    ]

    # clean taxonomy prefixes
    tax_cols = ["Species","Genus","Family","Order","Class","Phylum"]
    for row in mags:
        for col in tax_cols:
            v = row.get(col, "")
            if isinstance(v, str):
                row[col] = re.sub(r'^[dpkocfgs]__', '', v)

    mag_fields = [
        "MAGID","specimenID","Species","Genus","Family","Order","Class","Phylum","Completeness","Contamination","Link","Release"
    ]
    mag_types = {f: 'str' for f in mag_fields}
    mag_types.update({
        "Completeness": 'num',
        "Contamination": 'num'
    })

    # Output JavaScript arrays
    format_js_array("specimensData", specs, spec_fields, spec_types, out)
    format_js_array("magsData", mags, mag_fields, mag_types, out)

    if args.output:
        out.close()

if __name__ == '__main__':
    main()
