import streamlit as st
import boto3
from boto3.dynamodb.conditions import Key, Attr
import pandas as pd
import datetime

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


def get_data(site, start, end):
    dynamodb = boto3.resource(
        "dynamodb",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name="eu-central-1",
    )
    table = dynamodb.Table("conversions")
    end = int(end.timestamp())
    start = int(start.timestamp())
    r = table.query(
        IndexName="sitegroup-timestamp-index",
        KeyConditionExpression=Key("timestamp").between(str(start), str(end))
        & (Key("sitegroup").eq(site)),
    )
    df = pd.DataFrame(r["Items"])
    df.timestamp = pd.to_datetime(df.timestamp, utc=True, unit="s")
    df.timestamp = df.timestamp.dt.tz_convert("Europe/Berlin")
    df["conversions"] = 1
    df = df.sort_values("timestamp", ascending=False)
    df.uniqueid = df.uniqueid.astype(int)
    df.price = df.price.astype(float)
    return df


if check_password():
    st.snow()
    site = "mps"
    start = "2022-11-28"  # @param {type: "date", min:1, max:90}
    end = "2022-12-31"  # @param {type:"date"}
    ACCESS_KEY = st.secrets["ACCESS_KEY"]
    SECRET_KEY = st.secrets["SECRET_KEY"]
    start = datetime.datetime.strptime(start, "%Y-%m-%d")
    end = datetime.datetime.strptime(end, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59
    )
    df = get_data(site, start, end)
    df.dropna(subset=["site"], inplace=True)
    st.title("Kaufbasierte Recos")
    st.write("Zeitraum: ", start, " - ", end)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Käufe bei manueller Ausspielung",
            df[df.site.str.contains("artDetailManual")].shape[0],
        )
    with col2:
        st.metric(
            "Käufe bei automatischer Ausspielung",
            df[df.site.str.contains("artDetailApi")].shape[0],
        )
