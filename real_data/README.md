# Real-world test datasets

These files are unmodified samples of public datasets. They are what
`tests/test_real_data.py` runs `clean` and `gather` against, and what the numbers
in the README's "Results on real data" table come from. Nothing in them was
hand-edited to make the tool look good; where a file is a slice of a larger
dataset, the slice is a contiguous range of the original rows.

| File | Source | What makes it messy | Rows |
|---|---|---|---|
| `titanic.csv` | Kaggle Titanic training set, via [datasciencedojo/datasets](https://github.com/datasciencedojo/datasets) | 177 missing ages, 687 missing cabins, lowercase `male`/`female` | 891 |
| `uci_adult_sample.csv` | [UCI Adult (census income)](https://archive.ics.uci.edu/dataset/2/adult), rows 3501-5000 of `adult.data` with the documented header added | every text cell has a leading space, `?` marks missing values, one exact duplicate row | 1500 |
| `uci_automobile.csv` | [UCI Automobile (imports-85)](https://archive.ics.uci.edu/dataset/10/automobile), full file with the documented header added | `?` in numeric columns (price, horsepower, ...) which turns them into text; a column named `width` | 205 |
| `openflights_airlines.csv` | [OpenFlights airlines.dat](https://github.com/jpatokal/openflights), first 1500 rows with the documented header added | MySQL-style `\N` for null, `Y`/`N` flags, padded callsigns | 1500 |
| `northwind_customers.csv`, `northwind_orders.csv` | Northwind sample database export, via [neo4j-contrib/northwind-neo4j](https://github.com/neo4j-contrib/northwind-neo4j) | unquoted commas inside company names break 24 customer lines and 176 order lines; literal `NULL` strings; SQL timestamps | 91 / 830 |

Licences: UCI datasets are CC BY 4.0. OpenFlights data is ODbL. The Titanic
training set is public domain (Kaggle competition data, originally from the
Encyclopedia Titanica). Northwind is a Microsoft sample database distributed
under the MIT licence by the linked repository.

## Adding a dataset

1. Pick something public, under about 150 KB, with a licence that allows
   redistribution. Prefer data that exposes a behaviour no current file does.
2. If the source has no header row, add the documented column names and say so
   in the table above. Do not change any data values.
3. Run `python scripts/clean.py real_data/<file>` and read the JSON critically.
   Every count should be explainable from the raw file with plain pandas.
4. Add a test in `tests/test_real_data.py` that recomputes those counts from the
   raw file and asserts the report matches. Fixed numbers are fine when they
   are documented properties of the dataset (Titanic has 891 rows).
5. Add a row to the table above.
