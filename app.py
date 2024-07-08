# pylint: disable=missing-module-docstring
# pylint: disable=invalid-name

import os
import logging
from datetime import date, timedelta
import subprocess
import duckdb
import streamlit as st

if "data" not in os.listdir():
    print("creating folder data")
    logging.error(os.listdir())
    logging.error("creating folder data")
    os.mkdir("data")

if "exercises_sql_tables.duckdb" not in os.listdir("data"):
    subprocess.run(["python", "init_db.py"], check="True")
# subprocess.run(["python", "init_db.py"])

con = duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)


def check_users_solution(user_query: str) -> None:
    """
    Checks that user SQL query is correct by:
    1: checking the columns
    2: checking the values
    :param user_query: a string containing the query inserted by the user
    """
    result = con.execute(user_query).df()
    st.dataframe(result)
    try:
        result = result[solution_df.columns]
        st.dataframe(result.compare(solution_df))
        if result.compare(solution_df).shape == (0, 0):
            st.write("Correct !")
            st.balloons()
    except KeyError:
        st.write("Some columns are missing")
    n_lines_difference = result.shape[0] - solution_df.shape[0]
    if n_lines_difference != 0:
        st.write(
            f"result has a {n_lines_difference} lines difference with the solution_df"
        )


with st.sidebar:
    available_themes_df = con.execute("SELECT DISTINCT theme FROM memory_state").df()
    theme = st.selectbox(
        "What would you like to review?",
        available_themes_df["theme"].unique(),
        index=None,
        placeholder="Select a theme...",
    )
    if theme:
        st.write(f"You selected {theme}")
        select_exercise_query = f"SELECT * FROM memory_state WHERE theme = '{theme}'"
    else:
        select_exercise_query = (
            "SELECT * FROM memory_state"  # f"SELECT * FROM memory_state"
        )

    exercise = (
        con.execute(select_exercise_query)
        .df()
        .sort_values("last_reviewed")
        .reset_index(drop=True)
    )
    st.write(exercise)
    exercise_name = exercise.loc[0, "exercise_name"]
    with open(f"answers/{exercise_name}.sql", "r", encoding="utf-8") as f:
        answer = f.read()

    solution_df = con.execute(answer).df()

st.header("enter your code:")
form = st.form("my_form")
query = form.text_area(label="votre code SQL ici", key="user_input")
form.form_submit_button("Submit")

if query:
    check_users_solution(query)

for n_days in [2, 7, 21]:
    if st.button(f"Revoir dans {n_days} jours"):
        next_review = date.today() + timedelta(days=n_days)
        con.execute(
            "UPDATE memory_state SET last_reviewed = ? WHERE exercise_name = ?",
            [next_review, exercise_name],
            #                "UPDATE memory_state SET last_reviewed = '{next_review}'\
            #                WHERE exercise_name = '{exercise_name}'"
        )
        st.rerun()

if st.button("Reset"):
    con.execute("UPDATE memory_state SET last_reviewed = '1970-01-01'")
    # con.execute(f"UPDATE memory_state SET last_reviewed = '1970-01-01'")
    st.rerun()


with st.expander("Tables"):
    st.header("Source Tables")
    exercise_tables = exercise.loc[0, "tables"]
    for table in exercise_tables:
        st.write(f"table: {table}")
        df_table = con.execute(f"SELECT * FROM {table}").df()
        st.dataframe(df_table)

with st.expander("Solution"):
    st.header("Query Result / Query")
    st.write(answer)
