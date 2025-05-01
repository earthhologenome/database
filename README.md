# EHI Data Browser

This is the code source of the EHI Data browser. Data are stored in an internal Airtable database, from which CSV files of animal specimens and MAGs are outputted. The script `csv_to_js.py` generates the javascript arrays that the html document can read to display all the data.

```
python csv_to_js.py specimens.csv mags.csv > data.js
```

The rendered version is accessible in:

http://www.earthhologenome.org/database
