# SEBRA Playground
This is a repo to provide with data wrangling utils for the open government SEBRA data https://data.egov.bg/organisation/datasets/resourceView/ba444b96-6ec3-4be7-8981-92bc33d1a94b

## Installation

`python -m pip install git+https://github.com/krumeto/sebra_data_playground`

## Usage

```
from sebradata import sebrautils as sebra

link_to_data = "https://data.egov.bg/resource/download/zip/ba444b96-6ec3-4be7-8981-92bc33d1a94b"

data = (sebra.data_load_sebra(link_to_data).
        # Lowercase columns
        pipe(sebra.lowercase_columns).
        # Add year as a separate column
        pipe(sebra.add_year).
        # Add columns for ruling party/government during a given period
        # joining on settlement date gets more results than on reg_date
        merge(sebra.pull_government_periods(), 
              how ='left',
              left_on ='settlement_date',
              right_on = 'date').
        drop(columns = ['date']).
        # Add bank names for BIC codes
        merge(sebra.pull_bank_names_per_bic(),
              how = "left",
              left_on = "client_receiver_bic",
              right_on = "bic").
        drop(columns = ['bic']).
        pipe(sebra.uppercase_all_object_cols))
```

