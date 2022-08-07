import pandas as pd
import numpy as np
import dateparser


def data_load_sebra(link_to_data):
    data = pd.read_csv(link_to_data, compression = 'zip')
    data["REG_DATE"] = pd.to_datetime(data["REG_DATE"]).dt.normalize()
    data["SETTLEMENT_DATE"] = pd.to_datetime(data["SETTLEMENT_DATE"]).dt.normalize()
    return(data)

def lowercase_columns(dataf):
    dataf.columns = dataf.columns.str.lower()
    return(dataf)

def add_year(dataf):
    return(
        dataf.assign(reg_year = dataf['reg_date'].dt.year)
        )
    
def uppercase_all_object_cols(dataf):
    object_cols = dataf.select_dtypes("object").columns
    # For loop instead of apply for memory purposes
    for col in object_cols:
      dataf[col] = dataf[col].str.upper()
    return(dataf)


def pull_government_periods():
    """A function to pull periods of different governments and prepare the info in a format for left join"""

    # Data pull from wikipedia
    governments = pd.read_html("https://bg.wikipedia.org/wiki/%D0%9F%D1%80%D0%B0%D0%B2%D0%B8%D1%82%D0%B5%D0%BB%D1%81%D1%82%D0%B2%D0%B0_%D0%BD%D0%B0_%D0%91%D1%8A%D0%BB%D0%B3%D0%B0%D1%80%D0%B8%D1%8F",
                              match = "Република България"
                              )[0]

    # better column names              
    governments.columns = ["gov_nr", "government_alias", "government_pm", "government_start_dt", "government_end_dt", "n_days", "party/coalition"]

    # Get only post-communist goverments
    post_com_index = governments.loc[lambda d: d["gov_nr"] == "Република България (от 1990 г.)"].index
    governments = governments.iloc[lambda d: d.index > post_com_index[0]]

    # Convert dates using dateparser
    governments.government_start_dt = governments.government_start_dt.apply(dateparser.parse)

    # Weird if-else, as the last cell of the wikipedia article is usually empty, but occasionally - not
    if sum(governments.government_end_dt.isna()) > 0:
      governments.government_end_dt.iloc[:-1] = governments.government_end_dt.iloc[:-1].apply(dateparser.parse)
    else:
      governments.government_end_dt = governments.government_end_dt.apply(dateparser.parse)


    # extra cautious with dates, as we will be joining on them later
    governments.government_start_dt = pd.to_datetime(governments.government_start_dt).dt.normalize()
    governments.government_end_dt = pd.to_datetime(governments.government_end_dt).dt.normalize()


    # Get data in a long format
    # Potentially there is a much cleaner way, but data is small and this works
    long_gov_df = pd.DataFrame(columns = ["date", "government_alias", "government_pm", 'party/coalition'])

    # Iter over all rows
    for ix, row in governments.iterrows():
      interim_df = pd.DataFrame(columns = ["date", 'government_alias', 'government_pm', 'party/coalition'])
      # create a date_range starting from the day after a government starts until the day it ends
      try:
        date_period = pd.date_range(start = row["government_start_dt"] + pd.Timedelta(days=1), end = row["government_end_dt"])
      # except for the NA for the latest government
      except ValueError:
        date_period = pd.date_range(start = row["government_start_dt"] + pd.Timedelta(days=1), end = pd.Timestamp.today())
      interim_df["date"] = date_period
      interim_df["government_alias"] = row["government_alias"]
      interim_df["government_pm"] = row["government_pm"]
      interim_df['party/coalition'] = row['party/coalition']
      long_gov_df = pd.concat([long_gov_df, interim_df])

    long_gov_df["date"] = pd.to_datetime(long_gov_df["date"]).dt.normalize()
    return(long_gov_df)


def pull_bank_names_per_bic():
    """A function to pull bank names for a given bic"""

    bics_raw = pd.read_html("https://www.bnb.bg/RegistersAndServices/RSBAEAndBIC/index.htm")

    # clean the raw output
    bics = pd.DataFrame()

    for dataf in bics_raw:
      if dataf.shape[1] == 3 and dataf.shape[0] > 0:
        bics = pd.concat([bics, dataf])

    # keep the bics only
    bics = bics.dropna().iloc[:, [0,2]].reset_index(drop=True)
    bics.columns = ["bank_name", "bic"]

    # Expired and additional bics
    additional_banks_list = [('Българска народна банка', 'BNBGBGSF'),
    ('Българска народна банка', 'BNBGBGSD'),
    ('СИБАНК', 'BUIBBGSF'),
    ('УниКредит Булбанк АД', 'BFTBBGSF'),
    ('Сосиете Женерал Експрес Банк', 'TTBBBG22'),
    ('Unknown bank', 'ACBPGS2P'),
    ('МКБ Юнионбанк АД', 'CBUNBGSF'),
    ('ДЗИ Банк АД', 'REXIBGSF'),
    ('Корпоративна търговска банка АД', 'KORPBGSF'),
    ('Пиреус Банк България АД', 'PIRBBGSF'),
    ('ТИ БИ АЙ БАНК ЕАД', 'WEBKBGSF'),
    ('Алфа банк - клон България', 'CRBABGSF'),
    ('Креди Агрикол България', 'BINVBGSF'),
    ('SG Експресбанк AD', 'TTBB22'),
    ('ISBANK AG', 'ISBKBGSF'),
    ('Ейч Ви Би Банк БиохимАД', 'BACXBGSF')
    ]


    additional_banks_df = pd.DataFrame(additional_banks_list, columns = ["bank_name", "bic"])

    bics = pd.concat([bics, additional_banks_df]).reset_index(drop = True)
    bics = bics.loc[lambda d: d['bic'].str.len() <= 8].reset_index(drop = True)

    return(bics)

def get_a_report_per_iban(dataf, iban):
    """Get a report per IBAN"""
    all_rows = dataf.loc[lambda d: d["client_receiver_acc"] == iban]
    n_hashes = (all_rows["client_name_hash"].unique())
    n_client_receiver_name = (all_rows["client_receiver_name"].unique())
    flows = (all_rows.
             groupby(["primary_organization", "reg_year"])['amount'].
             agg(["sum", 'count']).
             sort_values('reg_year'))
    
    return([all_rows, n_hashes, n_client_receiver_name, flows])


def plot_organization_timeseries(dataf, groupby_col = 'primary_organization', time_col = 'settlement_date', interactive = True, custom_title = False):
    """A plotting function after a groupby+reset_index()"""
    selection = alt.selection_multi(fields=[groupby_col], bind='legend')

    final_chart = alt.Chart(dataf).mark_line(point=alt.OverlayMarkDef()).encode(
        x= time_col,
        y='amount',
        color=alt.Color(groupby_col, scale=alt.Scale(scheme='tableau20')),
        strokeDash=groupby_col,
        tooltip = [groupby_col, time_col, 'amount'],
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).configure_legend(
        labelLimit= 0
    ).add_selection(
        selection
    ).properties(
        width=800,
        height=300,
        title = custom_title if custom_title else f"{groupby_col} over time" 
    )

    if interactive:
       final_chart = final_chart.interactive()

    return(final_chart)