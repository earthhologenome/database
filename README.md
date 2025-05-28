# EHI Data Browser

This is the code source of the EHI Data browser. Data are stored in an internal Airtable database. The script `airtable_to_js.py` generates the javascript arrays that the html document can read to display all the data in the database. Note that the Airtable data can only be accessed with a private API key that is not publicly available.

```
python csv_to_js.py specimens.csv mags.csv > data.js

export AIRTABLE_API_KEY="key..."
python airtable_to_js.py \
  --spec-base appQpr6MxnaiVHsHy \
  --spec-table Captures \
  --mag-base appWbHBNLE6iAsMRV \
  --mag-table MAGs \
  --output data.js
```

The rendered version is accessible in:

http://www.earthhologenome.org/database
